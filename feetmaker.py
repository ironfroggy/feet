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


parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers(dest='command')

build_parser = subparsers.add_parser('build')
build_parser.add_argument('--debug', action='store_true')

clean_parser = subparsers.add_parser('clean')

setup_parser = subparsers.add_parser('setup')

python_loc = os.getenv("FEET_PYTHON_DIR", None)
assert python_loc, "Please set $FEET_PYTHON_DIR to a checkout of CPython which you have compiled."

arch = "amd64" # win32 or amd64
py_bin = os.path.join(python_loc, 'PCBuild', arch, 'python.exe')

# These patterns will be excluded from the generated Zip archives
zip_excludes = [
    '*__pycache__*',
    '*.pyc',
    '*venv*.exe',
    '*/pythonw.exe',
    '*/py.exe',
    '*/pyw.exe',
    'test/**',
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


def zipdir(path, relto, dest, compression):
    zipf = zipfile.ZipFile(dest, 'w', compression)
    relto = relto or path

    if path.endswith('*'):
        path = path[:-2]
    print("Writing zip file", dest, "from", path)

    for root, _, files in os.walk(path):
        
        for file in files:
            src = os.path.join(root, file)
            name = os.path.relpath(src, relto)
            excluded = False
            for pattern in zip_excludes:
                if fnmatch.fnmatch(name, pattern):
                    excluded = True
                    break
            if not excluded:
                zipf.write(src, name)
    
    zipf.close()


def main():
    argv = sys.argv[1:]
    args = parser.parse_args(argv)

    if not os.path.exists("feetmaker.py"):
        print("You are not in the feet repo. Cannot build.")
        sys.exit(1)

    if not args.command or args.command == "build":
        clean()

        print("Compiling bootloader...")
        subprocess.check_call("cargo build")

        print("Creating runtime archive...")
        shutil.copytree(
            os.path.join(python_loc, "PCbuild", arch),
            "feet/cpython",
        )

        os.makedirs("feet/cpython/lib")
        for name in non_zip_modules:
            src = os.path.join(python_loc, "lib", name)
            if not os.path.exists(src):
                name += ".py"
                src = os.path.join(python_loc, "lib", name)
            # if not os.path.exists(src):
            #     print("missing", src)
            else:
                if os.path.isdir(src):
                    shutil.copytree(src, f"feet/cpython/lib/{name}")
                else:
                    shutil.copy(
                        src,
                        "feet/cpython/lib/",
                    )
        
        # Create the stdlib zip to make unpacking faster
        zipdir(
            os.path.join(python_loc, "lib"),
            None,
            os.path.join("feet", "cpython", "python37.zip"),
            zipfile.ZIP_STORED,
        )

        # Create the archive to attach to feet.exe to self-extract
        for name in py_deps:
            try:
                subprocess.check_call([py_bin, '-m', 'pip', 'install', '-U', name])
            except FileNotFoundError:
                logger.error(f"Could not find python executable to install deps: {py_bin}")
                raise
        shutil.copytree(
            os.path.join(python_loc, "Lib", "site-packages"),
            f"feet/cpython/lib/site-packages",
        )
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
        final = open('build/feet.exe', 'wb')

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
