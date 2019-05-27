import argparse
import os
import sys

# Add path for included third-party packages with the Feet runtime
sys.path.insert(0, os.path.join(sys.executable, 'Lib', 'site-packages'))

# Add path for project required Python dependencies
sys.path.insert(0, '.\\Lib\\site-packages\\')

# Add path for the actual project, main script and all
# TODO: Decide if this is necessary...?
sys.path.insert(0, '.')

import requirements


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
subparsers = parser.add_subparsers(dest='command')

run_parser = subparsers.add_parser('run')

library_parser = subparsers.add_parser('library')
library_parser.add_argument('--update', action='store_true')
library_parser.add_argument('spec', type=str, nargs='?')

shell_parser = subparsers.add_parser('shell')


def main(argv):
    feet_exec = argv.pop(0)
    args = parser.parse_args(argv)

    root = "."
    path = os.path.join(root, "main.py")
    sys.path.append(os.path.join('.', 'Lib', 'site-packages'))

    if args.command == 'run' or not args.command:
        if not os.path.exists(path):
            print(HELP)
        else:
            # At this point, we import the main script to "run" it.
            # This import statement will block until the Feet app is done.
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
        import pip.__main__, pip._internal, pip._vendor
        if args.update:
            if os.path.exists('requirements.txt'):
                pip._internal.main(['install', '--trusted-host=pypi.org', '--prefix=.', '-Ur', 'requirements.txt'])
            else:
                print("This project has no Python libraries listed in a requirements.txt file.")
                print("Use `feet libary some-library` to install libraries from Python's ecosystem to your project.")

        else:
            cur_libraries = {}

            if os.path.exists('requirements.txt'):
                for line in requirements.parse(open('requirements.txt')):
                    cur_libraries[line.name] = line.line
            new_req = list(requirements.parse(args.spec))[0]
            cur_libraries[new_req.name] = new_req.line

            args = ['install', '--prefix=.', '--trusted-host=pypi.org', new_req.line]
            retcode = pip._internal.main(args)
            assert retcode == 0, "Library failed to install"

            print("Updating project requirements.txt file...")
            with open('requirements.txt', 'w') as f:
                for _, line in cur_libraries.items():
                    f.write(f'{line}\n')


if __name__ == '__main__':
    main(sys.argv)