import argparse
import fnmatch
import glob
import itertools
import os
import pkg_resources
import shutil
import subprocess
import sys
import zipfile

root = os.path.abspath(os.path.dirname(__file__))

def _set_root_relative():
    global feet_bin
    global site_packages
    global zip_excludes

    feet_bin = root.split('_data')[0] + '.exe'
    site_packages = os.path.join(root, 'cpython', 'lib', 'site-packages')

    zip_excludes = [
        "*.pyc",
        "*__pycache__*",
        "dist*",
        ".git*",
        os.path.basename(root) + '*',
    ]

_set_root_relative()

# Add path for included third-party packages with the Feet runtime
sys.path.insert(0, os.path.join(sys.executable, 'Lib', 'site-packages'))

# Add path for project required Python dependencies
sys.path.insert(0, site_packages)

# Add path for the actual project, main script and all
# TODO: Decide if this is necessary...?
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
subparsers = parser.add_subparsers(dest='command')

run_parser = subparsers.add_parser('run')

library_parser = subparsers.add_parser('library')
library_parser.add_argument('--update', action='store_true')
library_parser.add_argument('spec', type=str, nargs='?')

shell_parser = subparsers.add_parser('shell')

setup_parser = subparsers.add_parser('setup')

exe_parser = subparsers.add_parser('exe')
exe_parser.add_argument('name', type=str, action='store')
exe_parser.add_argument('files', type=str, nargs='*')
exe_parser.add_argument('--confirm', action='store_true')

zip_parser = subparsers.add_parser('zip')
zip_parser.add_argument('name', type=str, action='store')
zip_parser.add_argument('files', type=str, nargs='*')


def add_to_zip(path, dest, compression, prefix=None):
    zipf = zipfile.ZipFile(dest, 'a', compression)

    for root, _, files in os.walk(path):
        for file in files:
            src = os.path.join(root, file)
            name = os.path.relpath(src, ".")
            base = name.split(os.path.sep, 1)[0]

            # print(name, '...', end='')
            excluded = False
            for pattern in zip_excludes:
                if fnmatch.fnmatch(name, pattern):
                    excluded = True
                    # print('skip')
                    break
            if not excluded:
                # print('ok')
                if prefix:
                    name = os.path.relpath(os.path.join(prefix, name))
                name = name.replace('\\', '/')
                try:
                    zipf.getinfo(name)
                except KeyError:
                    zipf.write(src, name)
    
    zipf.close()


def get_app_files(files, exclude=()):
    if files:
        yield from files
    else:
        for fn in os.listdir('.'):
            include = True
            for exc in itertools.chain(zip_excludes, exclude):
                if fnmatch.fnmatch(fn, exc):
                    include = False
                    break
            if include:
                yield fn



def main(argv):
    feet_exec = argv.pop(0)
    args = parser.parse_args(argv)

    assert os.path.exists(feet_bin)
    py_bin = os.path.join(root, "cpython", "python.exe")
    
    main = os.path.join(root, "app", "main.py")
    if not os.path.exists(main):
        main = os.path.join(root, "..", "main.py")
    main = os.path.abspath(main)
    if not os.path.exists(main):
        print(HELP)
        exit(1)

    if args.command == 'run' or not args.command:
        env = os.environ.copy()
        env.update({
            'PYTHONPATH': ':'.join((
                site_packages,
            )),
        })
        proc = subprocess.Popen(
            [py_bin, main],
            cwd=os.path.dirname(main),
            env=env,
            stdout=sys.stdout,
            stderr=sys.stderr,
            stdin=sys.stdin,
        )
        sys.exit(proc.wait())
    
    elif args.command == 'setup':
        print('Python Feet environemnt ready for use!')
        return 0

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
        if args.update:
            if os.path.exists('requirements.txt'):
                subprocess.check_call([py_bin, '-m', 'pip', 'install', '--trusted-host=pypi.org', '-Ur', 'requirements.txt'])
            else:
                print("This project has no Python libraries listed in a requirements.txt file.")
                print("Use `feet libary some-library` to install libraries from Python's ecosystem to your project.")

        else:
            cur_libraries = {}

            if os.path.exists('requirements.txt'):
                for req in pkg_resources.parse_requirements(open('requirements.txt')):
                    cur_libraries[req.name] = req.specifier
            new_req = list(pkg_resources.parse_requirements(args.spec))[0]
            cur_libraries[new_req.name] = new_req.specifier

            args = ['install', '--trusted-host=pypi.org', args.spec]
            subprocess.check_call([py_bin, '-m', 'pip', *args])

            print("Updating project requirements.txt file...")
            with open('requirements.txt', 'w') as f:
                for name, spec in cur_libraries.items():
                    f.write(f'{name}{spec}\n')
    
    elif args.command == 'exe':
        if not args.confirm:
            print("The exe packing command is experimental. Use --confirm to confirm opting into using it.")
            exit(1)
        name = args.name
        if not name.endswith('.exe'):
            name += ".exe"
        if not name.startswith('dist/'):
            name = "dist/" + name
            if not os.path.exists('dist'):
                os.mkdir('dist')


        shutil.copy(feet_bin, name)
        include = get_app_files(args.files, exclude=[feet_bin])
        prefix = '.'

        zf = zipfile.ZipFile(name, 'a', zipfile.ZIP_BZIP2)
        for f in include:
            zf.write(f, os.path.join(prefix, f))
        zf.close()

        add_to_zip(".", name, zipfile.ZIP_BZIP2, prefix=prefix)
    
    elif args.command == 'zip':
        name = args.name
        if not name.endswith('.zip'):
            name += ".zip"
        if not name.startswith('dist/'):
            name = "dist/" + name
        if not os.path.exists("dist"):
            os.makedirs("dist")
        
        include = get_app_files(args.files)

        zf = zipfile.ZipFile(name, 'a', zipfile.ZIP_DEFLATED)
        for f in include:
            zf.write(f, f)
        zf.close()

        add_to_zip(".", name, zipfile.ZIP_DEFLATED, prefix=".")


if __name__ == '__main__':
    sys.exit(main(sys.argv))