import argparse
import fnmatch
import glob
import os
import shutil
import subprocess
import sys
import zipfile

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

exe_parser = subparsers.add_parser('exe')
exe_parser.add_argument('name', type=str, action='store')
exe_parser.add_argument('files', type=str, nargs='+')

zip_parser = subparsers.add_parser('zip')
zip_parser.add_argument('name', type=str, action='store')

zip_excludes = [
    "*.pyc",
    "*__pycache__*",
]

def add_to_zip(path, dest, compression, prefix=None):
    if not prefix:
        prefix = os.path.join("feet", "app")
    zipf = zipfile.ZipFile(dest, 'a', compression)

    for root, _, files in os.walk(path):
        for file in files:
            src = os.path.join(root, file)
            name = os.path.relpath(src, ".")

            excluded = False
            for pattern in zip_excludes:
                if fnmatch.fnmatch(os.path.abspath(name), pattern):
                    excluded = True
                    break
            if not excluded:
                name = os.path.join(prefix, name)
                print("...", name)
                zipf.write(src, name)
    
    zipf.close()


def main(argv):
    feet_exec = argv.pop(0)
    args = parser.parse_args(argv)

    root = os.path.abspath(os.path.dirname(__file__))
    feet_bin = root.split('_data')[0] + '.exe'
    assert os.path.exists(feet_bin)
    py_bin = os.path.join(root, "cpython", "python.exe")
    
    main =  os.path.join(root, "app", "main.py")
    if not os.path.exists(main):
        main =  os.path.join(root, "..", "main.py")
    if not os.path.exists(main):
        print(HELP)
        exit(1)

    # sys.path.append(os.path.join(os.path.dirname(main), 'Lib', 'site-packages'))

    if args.command == 'run' or not args.command:
        env = os.environ.copy()
        env.update({
            'PYTHONPATH': ':'.join((
                os.path.join(os.path.dirname(main), 'Lib', 'site-packages'),
            )),
        })
        subprocess.Popen([py_bin, main], env=env)

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
    
    elif args.command == 'exe':
        name = args.name
        if not name.endswith('.exe'):
            name += ".exe"
        include = args.files or [main]

        shutil.copy(feet_bin, name)

        zf = zipfile.ZipFile(name, 'a', zipfile.ZIP_BZIP2)
        for pattern in include:
            for f in glob.glob(pattern):
                print(f, "->", os.path.join("feet", "app", f))
                zf.write(f, os.path.join("feet", "app", f))
        zf.close()

        if os.path.exists("Lib/site-packages/"):
            add_to_zip("Lib", name, zipfile.ZIP_BZIP2)
    
    elif args.command == 'zip':
        name = args.name
        if not name.endswith('.zip'):
            name += ".zip"
        if not name.startswith('dist/'):
            name = "dist/" + name
        if not os.path.exists("dist"):
            os.makedirs("dist")
        
        zip_excludes.append(os.path.join(os.path.abspath(root), '*'))
        zip_excludes.append(os.path.join(os.path.abspath("dist"), '*'))
        add_to_zip(".", name, zipfile.ZIP_DEFLATED, prefix=".")


if __name__ == '__main__':
    main(sys.argv)