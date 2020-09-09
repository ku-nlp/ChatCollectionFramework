import os
import os.path
import pytest
import subprocess

def test_command(command):
    stream = os.popen(command)
    output = stream.read()
    return output


def test_start_server():
    print(f"pwd={os.path.abspath(__file__)}")
    print(f"cwd={os.getcwd()}")
    print(f"listdir={os.listdir()}")
    print(f"exists?={os.path.exists('App.py')}")

    print(f"ls -l={test_command('ls -l')}")
    print(f"which python={test_command('which python')}")
    print(f"python --version={test_command('python --version')}")

    assert 1 == 1
