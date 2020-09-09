import os
import os.path
import pytest
import subprocess

@pytest.fixture
def run_command(command):
    stream = os.popen(command)
    output = stream.read()
    return output


def test_start_server():
    print(f"pwd={os.path.abspath(__file__)}")
    print(f"cwd={os.getcwd()}")
    print(f"listdir={os.listdir()}")
    print(f"exists?={os.path.exists('App.py')}")

    print(f"ls -l={run_command('ls -l')}")
    print(f"which python={run_command('which python')}")
    print(f"python --version={run_command('python --version')}")

    assert 1 == 1
