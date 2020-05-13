import sys
sys.path.append('feet')

from unittest.mock import patch

import pytest

import feet
feet.root = 'c:/__fake__/feet_data'
feet._set_root_relative()


def test_one_file():
    files = []

    with patch('os.listdir') as listdir:
        listdir.return_value = ['main.py']
        include = list(feet.get_app_files(files))
        assert include == ['main.py']


def test_auto_scripts():
    files = []

    with patch('os.listdir') as listdir:
        listdir.return_value = ['main.py', 'foo.py']
        include = list(feet.get_app_files(files))
        assert include == ['main.py', 'foo.py']


def test_excludes():
    files = [
        'dist',
        'foo.pyc',
        'feet_data',
        'feet.exe',
        'main.py',
    ]

    with patch('os.listdir') as listdir:
        listdir.return_value = files
        include = set(feet.get_app_files(None))
        assert include == set(['main.py', 'feet.exe'])
        include = set(feet.get_app_files(None, exclude=['*.exe']))
        assert include == set(['main.py'])