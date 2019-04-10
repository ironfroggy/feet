#!/usr/bin/env python3

import shutil
import subprocess
import sys


HELP = """Python Feet Build Script

This simple script builds Feet for Windows.

python build.py build
python build.py clean
"""


def main(argv):
    if len(argv) == 1:
        print(HELP)
    else:
        if argv[1] == "build":
            subprocess.check_call(["pyinstaller", "--onefile", "feet.py"])
        elif argv[1] == "clean":
            shutil.rmtree("dist")
        elif argv[1] == "setup":
            subprocess.check_call(["pip", "install", "-r", "requirements.txt"])


if __name__ == '__main__':
    main(sys.argv)