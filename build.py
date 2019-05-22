#!/usr/bin/env python3

import argparse
import os
import shutil
import subprocess
import sys


parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers(dest='command')

build_parser = subparsers.add_parser('build')
build_parser.add_argument('--debug', action='store_true')

clean_parser = subparsers.add_parser('clean')

setup_parser = subparsers.add_parser('setup')

def clean():
    if os.path.exists("dist"):
        shutil.rmtree("dist")
    if os.path.exists("build"):
        shutil.rmtree("build")

def main(argv):
    if argv[0] == 'build.py':
        argv = argv[1:]
    args = parser.parse_args(argv)
    print(args)

    if args.command == "build":
        clean()
        cmd = ['pyinstaller']
        if not args.debug:
            cmd += ['--onefile']
        cmd += ['feet.py']
        subprocess.check_call(cmd)
    elif args.command == "clean":
        clean()
    elif args.command == "setup":
        subprocess.check_call(["pip", "install", "-r", "requirements.txt"])


if __name__ == '__main__':
    main(sys.argv)
