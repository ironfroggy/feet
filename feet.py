import argparse
import os
import sys

# trigger inclusion
import dataclasses
import pathlib

import pip.__main__, pip._internal, pip._vendor
# import pygame

sys.path.insert(0, '.\\Lib\\site-packages\\')
sys.path.insert(0, '.')


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


parser = argparse.ArgumentParser(description='Make Python Run')
parser.add_argument('command', metavar='CMD', type=str, nargs='?',
                    help='an optional subcommand', default='run')
parser.add_argument('parameter', metavar='PARAM', type=str, nargs='?',
                    help='an optional subcommand', default=None)




def main(argv):
    feet_exec = argv.pop(0)
    args = parser.parse_args(argv)
    print(args.command)

    # if argv:
    #     root = argv.pop(0)
    # else:
    #     root = "."

    root = "."
    path = os.path.join(root, "main.py")
    sys.path.append(os.path.join('.', 'Lib', 'site-packages'))

    if args.command == 'run':
        if not os.path.exists(path):
            print(HELP)
        else:
            # init_py = open(path).read()
            # exec(init_py)
            import main
    elif args.command == 'shell':
        try:
            import readline # optional, will allow Up/Down/History in the console
        except ImportError:
            pass
        import code
        variables = globals().copy()
        variables.update(locals())
        shell = code.InteractiveConsole(variables)
        shell.interact()
    elif args.command == 'library':
        # from subprocess import check_output, CalledProcessError
        # try:
            # check_output([sys.executable, '-m', 'pip', 'install', '--prefix=.', args.parameter])
        # except CalledProcessError as e:
            # print(e.output)
        cert_path = '.\\Lib\\site-packages\\pip\\_vendor\\certifi\\'
        pip._internal.main(['install', '--prefix=.', '--trusted-host=pypi.org', args.parameter])


if __name__ == '__main__':
    main(sys.argv)