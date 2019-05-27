#!/usr/bin/env python3

import argparse
import os
import shutil
import subprocess
import sys
import zipfile


parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers(dest='command')

build_parser = subparsers.add_parser('build')
build_parser.add_argument('--debug', action='store_true')

clean_parser = subparsers.add_parser('clean')

setup_parser = subparsers.add_parser('setup')

python_loc = os.getenv("FEET_PYTHON_DIR")
assert python_loc, "Please set $FEET_PYTHON_DIR to a checkout of CPython which you have compiled."


def clean():
    if os.path.exists("feet/cpython"):
        shutil.rmtree("feet/cpython")


def zipdir(path, dest):
    zipf = zipfile.ZipFile(dest, 'w', zipfile.ZIP_DEFLATED)
    for root, dirs, files in os.walk(path):
        for file in files:
            src = os.path.join(root, file)
            if '__pycache__' not in src and '.pyc' not in src:
                zipf.write(src)
    zipf.close()


py_deps = (
    'requirements',
    'pip',
    'setuptools',
    'pkg_resources',
)


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
            os.path.join(python_loc, "PCbuild", "win32"),
            "feet/cpython",
        )
        shutil.copytree(
            os.path.join(python_loc, "Lib"),
            "feet/cpython/lib/",
        )
        shutil.rmtree("feet/cpython/lib/test")
        for name in py_deps:
            shutil.copytree(
                os.path.join(".", "Lib", name),
                f"feet/cpython/lib/site-packages/{name}",
            )
        zipdir('./feet/', './feetruntime.zip')
        
        print("Combining...")
        base = open('target/debug/feet.exe', 'rb')
        archive = open('feetruntime.zip', 'rb')
        final = open('feet.exe', 'wb')

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
