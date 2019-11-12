#!/usr/bin/env python3

import argparse
import fnmatch
import logging
import os
import shutil
import subprocess
import sys
import zipfile


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers(dest='command')

build_parser = subparsers.add_parser('build')
build_parser.add_argument('--debug', action='store_true')
build_parser.add_argument('-o', action='store', default=None, dest='output')

clean_parser = subparsers.add_parser('clean')

setup_parser = subparsers.add_parser('setup')

python_parser = subparsers.add_parser('python')

version = open("VERSION.txt").read()
arch = "amd64" # win32 or amd64
python_loc_default = "cpython"
python_loc = os.getenv("FEET_PYTHON_DIR", python_loc_default)
py_bin = os.path.join(python_loc, 'PCBuild', arch, 'python.exe')

# These patterns will be excluded from the generated Zip archives
zip_excludes = [
    '**/__pycache__',
    '**/*.pyc',
    '**/*.pdb',
    '**/*.exp',
    '*venv*.exe',
    '**/pythonw.exe',
    '**/_test*',
    '**/py.exe',
    '**/pyw.exe',
    '*test_*',
]

# These third-party packages will be included in the build
py_deps = (
    'pip',
    'requirements-parser',
    'setuptools',
    # 'pkg_resources',
)

# These first-party modules will be included outside the stdlib archive
non_zip_modules = (
    'importlib',
    'collections',
    '_weakref',
    '_io',
    'encodings',
    'codecs',
    '_codecs',
    '_signal',
    '__main__',
    'io',
    'abc',
    '_abc',
    'site',
    'os',
    'stat',
    '_stat',
    'ntpath',
    'genericpath',
    '_collections_abc',
    '_sitebuiltins',
    '_bootlocale',
    '_locale',
)


def clean():
    if os.path.exists("feet/cpython"):
        shutil.rmtree("feet/cpython")
    for name in os.listdir('build'):
        path = os.path.join('build', name)
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.unlink(path)


def is_excluded(name):
    for pattern in zip_excludes:
        if fnmatch.fnmatch(name, pattern):
            return True
    return False


def ignore_excludes(dirname, names):
    if is_excluded(dirname):
        print("IGNORE", dirname)
        return []
    return [
        name for name in names
        if is_excluded(os.path.join(dirname, name))
    ]


def zipdir(path, relto, dest, compression):
    zipf = zipfile.ZipFile(dest, 'w', compression, compresslevel=9)
    relto = relto or path

    if path.endswith('*'):
        path = path[:-2]
    print("Writing zip file", dest, "from", path)

    for root, _, files in os.walk(path):
        
        for file in files:
            src = os.path.join(root, file)
            name = os.path.relpath(src, relto)
            if not is_excluded(name):
                zipf.write(src, name)
    
    zipf.close()


def main():
    argv = sys.argv[1:]
    args = parser.parse_args(argv)

    if not os.path.exists("feetmaker.py"):
        print("You are not in the feet repo. Cannot build.")
        sys.exit(1)

    if args.command == "python":
        if not os.path.exists(python_loc):
            assert python_loc_default == python_loc, "No python checkout found at FEET_PYTHON_DIR"
            subprocess.check_call(f"git clone https://github.com/python/cpython.git {python_loc}")
            subprocess.check_call(f"git checkout 3.7")

        assert os.path.exists(f"./{python_loc}/PCBuild/build.bat")
        if arch == "amd64":
            p = "x64"
        else:
            p = arch
        print(f"./{python_loc}/PCBuild/build.bat -c Release -p {p} -t Build")
        subprocess.check_call(f"{python_loc}\\PCBuild\\build.bat -c Release -p {p} -t Build")

    elif not args.command or args.command == "build":
        if os.path.exists("feet/cpython"):
            shutil.rmtree("feet/cpython")

        print("Compiling bootloader...")
        subprocess.check_call("cargo build")

        print("Creating runtime archive...")
        shutil.copytree(
            os.path.join(python_loc, "PCbuild", arch),
            "feet/cpython",
            ignore=ignore_excludes,
        )
        
        os.makedirs("feet/cpython/lib")

        for name in os.listdir(os.path.join(python_loc, 'Lib')):

            src = os.path.join(python_loc, "lib", name)
            if os.path.splitext(name)[0] in non_zip_modules:
                if not os.path.exists(src):
                    name += ".py"
                    src = os.path.join(python_loc, "lib", name)
                if not os.path.exists(src):
                    print("Missing", src)
                else:
                    print(f"Copying {src}")
                    if os.path.isdir(src):
                        shutil.copytree(src, f"feet/cpython/{name}")
                    else:
                        shutil.copy(
                            src,
                            "feet/cpython/",
                        )

        # Create the stdlib zip to make unpacking faster
        zipdir(
            os.path.join(python_loc, "lib"),
            None,
            os.path.join("feet", "cpython", "python37.zip"),
            zipfile.ZIP_DEFLATED,
        )

        # Create the archive to attach to feet.exe to self-extract
        feet_py = "feet/cpython/python.exe"
        subprocess.check_call([feet_py, '-m', 'ensurepip'])
        for name in py_deps:
            try:
                p = subprocess.run([feet_py, '-m', 'pip', 'install', '-U', name], text=True)
                print(f"Installing package '{name}'")
                if p.stdout:
                    print(p.stdout)
            except FileNotFoundError:
                logger.error(f"Could not find python executable to install deps: {feet_py}")
                raise

        # # Copy installed packages
        # shutil.copytree(
        #     os.path.join(python_loc, "Lib", "site-packages"),
        #     f"feet/cpython/lib/site-packages",
        # # )

        # Create archive to attach to runtime
        zipdir(
            './feet/',
            '.',
            './feetruntime.zip',
            zipfile.ZIP_BZIP2,
        )
        
        print("Combining...")
        if not os.path.exists('build'):
            os.mkdir('build')

        base = open('target/debug/feet.exe', 'rb')
        archive = open('feetruntime.zip', 'rb')
        output = args.output or 'build/feet-{arch}-{version}'
        if not output.endswith('.exe'):
            output += '.exe'
        final = open(output, 'wb')

        final.write(base.read())
        final.write(archive.read())

        final.close()
        base.close()
        archive.close()

        print("Done.")

    elif args.command == "clean":
        clean()

    elif args.command == "setup":
        subprocess.check_call(["pip", "install", "-r", "requirements.txt"])


if __name__ == '__main__':
    main()
