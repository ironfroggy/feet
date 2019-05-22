# FEET, it makes Python run!

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

Note: Feet is a prototype, but please let me know if you find it useful and
file issues for any improvements that you feel would help make it less of an
experiment and more of a real thing.

## BUILDING

To build feet, install the build dependencies and then run the build script.

    pip install -r requirements.txt
    python build.py build
    # ./dist/feet.exe

## USING

To use Feet, copy the built EXE file into any directory with a main.py script
and run the feet EXE. Just double-click and run your script. Right now, feet
includes Pygame and the Python standard library. Support for other third-party
libraries will come in the future.

You can also download a pre-built EXE from the releases.

Feet has a few optional subcommands, as well.

### Running Feet applications

To run an application with Feet, copy the `feet.exe` binary into the
application folder, alongside a `main.py` file, and double-click the executable
in your File Explorer or run it from the command line inside the directory.

    ./feet.exe run

Or, simply

    ./feet.exe

### Adding Python Libraries

Feet runs Python apps and games, but much of the strength of Python comes from
the great quality of libraries available. Feet has you covered.

To install a library from PyPI, the Python Package Index, into your project's
`Lib/` directory, use the `library` command. For example, install `pygame`, the
popular game development library for Python, like this:

    ./feet.exe library pygame

To install a specific version of a library, specify it with the name, like so:

    ./feet.exe library pygame==1.9.6

When you zip up and share your app or game, the libraries in the `Lib/` folder
can be shared along with the rest of your program. Feet takes care of providing
these libraries to your code at runtime.

### Debugging

Some times, things go wrong. When that happens, more experienced Python
developers might want to inspect the special environment Feet runs programs in.

Run a Python shell in the Feet environment with the `shell` command.

    ./feet.exe shell

## Support and Contribution

Python Feet is a prototype. It definitely has bugs and will definitely have
breaking changes. However, if you find it useful, that's great! If you find
problems with it or if you want to help, please file issues on the [Github
page](https://github.com/ironfroggy/feet/issues) with all the details you
can include, or find me on Twitter [@ironfroggy](https://twitter.com/ironfroggy) to thank, complain to, or discuss Python
with.
