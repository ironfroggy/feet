import contextlib
from io import StringIO
import os
from shutil import copyfile
from subprocess import call, Popen, PIPE
import sys
from tempfile import TemporaryDirectory
from time import sleep
from zipfile import ZipFile

import pytest


@contextlib.contextmanager
def cd(path):
    # print 'initially inside {0}'.format(os.getcwd())
    CWD = os.getcwd()
    
    os.chdir(path)
    # print 'inside {0}'.format(os.getcwd())
    try:
        yield
    finally:
        # print 'finally inside {0}'.format(os.getcwd())
        os.chdir(CWD)


@pytest.fixture(scope='session')
def rundir():
    return os.getcwd()

@pytest.fixture(scope='session')
def build():
    print("BUILDING")
    exe = os.getenv('FEET_TEST_EXE', None)
    if exe:
        copyfile(exe, 'build/feet.exe')
        print(f"USING {exe}")
    else:
        p = Popen("python feetmaker.py build -o build/feet.exe", stdout=PIPE, stderr=PIPE)
        stdout, stderr = p.communicate()
        assert p.returncode == 0, stderr

@pytest.fixture(scope='session')
def tempdir(build, rundir):
    cwd = os.getcwd()
    with TemporaryDirectory() as tempdir:
        os.chdir(tempdir)
        src = os.path.join(rundir, 'build', 'feet.exe')
        dest = os.path.join(tempdir, 'feet.exe')
        copyfile(src, dest)
        yield tempdir
        os.chdir(cwd)

# def test_build(tempdir, build):
#     assert build == 0

def test_setup(tempdir):
    p = Popen("feet.exe setup", stdout=PIPE)
    stdout, stderr = p.communicate()
    ret = p.returncode
    #assert ret == 0

def test_run(tempdir):
    open('main.py', 'w').write('print("Hello, World!")')

    p = Popen("feet.exe", stdout=PIPE, stderr=PIPE, universal_newlines=True)
    stdout, stderr = p.communicate()
    ret = p.returncode

    lines = stdout.splitlines()

    assert lines[-1] == 'Hello, World!', stderr
    assert ret == 0, stderr

MAIN_SETUPTOOLS = '''
import sdl2
print("ok")
'''

def test_setuptools_package(rundir, tempdir, build):
    src = os.path.join(rundir, 'build', 'feet.exe')
    dest = os.path.join(tempdir, 'feet.exe')
    copyfile(src, dest)

    open('main.py', 'w').write(MAIN_SETUPTOOLS)

    call('./feet.exe library pysdl2-dll')
    call('./feet.exe library pysdl2')
    assert not os.path.exists('./Lib')

    p = Popen("feet.exe", stdout=PIPE, universal_newlines=True)
    stdout, stderr = p.communicate()
    ret = p.returncode

    lines = stdout.splitlines()
    assert lines[-1] == "ok", stderr


@pytest.mark.skip
def test_exe(rundir, tempdir, build):
    src = os.path.join(rundir, 'build', 'feet.exe')
    dest = os.path.join(tempdir, 'feet.exe')
    copyfile(src, dest)

    open('main.py', 'w').write(MAIN_SETUPTOOLS)

    call('./feet.exe library pysdl2-dll')
    call('./feet.exe library pysdl2')
    assert os.path.exists('feet_data/cpython/lib/site-packages/sdl2')
    call('./feet.exe exe testprog.exe main.py')
    with TemporaryDirectory() as exedir:
        copyfile(os.path.join(rundir, 'dist/testprog.exe'), os.path.join(exedir, 'testprog.exe'))

        with cd(exedir):
            assert 0 == call('./testprog.exe setup')

            print("Running test program")
            p = Popen("testprog.exe", stdout=PIPE, stderr=PIPE, universal_newlines=True)
            stdout, stderr = p.communicate()
            ret = p.returncode

            lines = stdout.splitlines()
            assert lines and lines[-1] == "ok", stderr


@pytest.mark.skip
def test_exe_auto(rundir, tempdir, build):
    src = os.path.join(rundir, 'build', 'feet.exe')
    dest = os.path.join(tempdir, 'feet.exe')
    copyfile(src, dest)

    open('main.py', 'w').write(MAIN_SETUPTOOLS)
    open('module.py', 'w').write("")
    open('compiled.pyc', 'w').write("")

    call('./feet.exe library pysdl2-dll')
    call('./feet.exe library pysdl2')
    assert os.path.exists('feet_data/cpython/lib/site-packages/sdl2')
    call('./feet.exe exe testprog.exe')
    with TemporaryDirectory() as exedir:
        copyfile(os.path.join(rundir, 'dist/testprog.exe'), os.path.join(exedir, 'testprog.exe'))

        with cd(exedir):
            assert 0 == call('./testprog.exe setup', stdout=sys.stdout, stderr=sys.stderr), str(os.listdir(exedir))

            print("Running test program")
            p = Popen("testprog.exe", stdout=PIPE, stderr=PIPE, universal_newlines=True)
            stdout, stderr = p.communicate()
            ret = p.returncode

            lines = stdout.splitlines()
            assert lines and lines[-1] == "ok", stderr

            assert os.path.exists(os.path.join(exedir, 'testprog_data', 'app', 'main.py'))
            assert os.path.exists(os.path.join(exedir, 'testprog_data', 'app', 'module.py'))
            assert not os.path.exists(os.path.join(exedir, 'testprog_data', 'app', 'compiled.pyc'))


def test_zip(rundir, tempdir, build):
    src = os.path.join(rundir, 'build', 'feet.exe')
    dest = os.path.join(tempdir, 'feet.exe')
    copyfile(src, dest)

    open('main.py', 'w').write(MAIN_SETUPTOOLS)

    call('./feet.exe library pysdl2-dll')
    call('./feet.exe library pysdl2')
    assert os.path.exists('feet_data/cpython/lib/site-packages/sdl2')
    call('./feet.exe zip testprog.zip')
    with TemporaryDirectory() as exedir:
        copyfile('dist/testprog.zip', os.path.join(exedir, 'testprog.zip'))

        with cd(exedir):
            zf = ZipFile(os.path.join(exedir, 'testprog.zip'))
            zf.extractall('.')
            zf.close()

            assert 0 == call('./feet.exe setup')

            print("Running test program")
            p = Popen("feet.exe", stdout=PIPE, stderr=PIPE, universal_newlines=True)
            stdout, stderr = p.communicate()
            ret = p.returncode

            lines = stdout.splitlines()
            assert lines and lines[-1] == "ok", stderr



MAIN_NONZERO = '''
import sys
sys.exit(1)
'''

def test_nonzero_exit(rundir, tempdir, build):
    src = os.path.join(rundir, 'build', 'feet.exe')
    dest = os.path.join(tempdir, 'feet.exe')
    copyfile(src, dest)

    open('main.py', 'w').write(MAIN_NONZERO)

    p = Popen("feet.exe", stdout=PIPE, universal_newlines=True)
    stdout, stderr = p.communicate()
    ret = p.returncode

    assert ret == 1, stderr
