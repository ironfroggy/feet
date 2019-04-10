import os
import sys

import pygame


HELP = """FEET, it makes Python run!

FEET is a runner for Python. What does that mean?

It makes it easy to create Python scripts, programs, applications, or games
and package them up to send to friends, users, players, or whomever you want
to share your work with. FEET is really just a wrapper around the excellent
PyInstaller project and it is *mostly* for Windows users, because they have
the hardest time sharing Python code.

FEET is just an executable, called `feet.exe`, that sits in a folder beside
your script that you name `main.py`. You can zip up this folder and send it
to anyone else on a Windows machine, and when they click the EXE, your 
program will run. They don't need to install Python and you never need to build
or package anything.

Just send them your files and the runner.

ERROR: You're seeing this help text because FEET cannot find your main.py
file. Put this EXE in a folder with your main.py script and run it again!
"""


def main(argv):
    feet_exec = argv.pop(0)
    if argv:
        root = argv.pop(0)
    else:
        root = "."
    
    path = os.path.join(root, "main.py")

    if not os.path.exists(path):
        print(HELP)
    else:
        init_py = open(path).read()
        exec(init_py)
    


if __name__ == '__main__':
    main(sys.argv)