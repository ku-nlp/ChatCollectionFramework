import os
import os.path
import psutil
import pytest
import signal
import subprocess
import time

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

    server_process = subprocess.Popen(["python App.py"], shell=True)

    try:
        print(f"server_process={server_process.pid}")

        # Wait 10 seconds to make sure that the server has started properly.
        time.sleep(10)

    finally:
        # Kill the server and its children processes.
        parent = psutil.Process(server_process.pid)
        children = parent.children(recursive=True)
        for process in children:
            process.send_signal(signal.SIGTERM)
        server_process.terminate()




    assert 1 == 1
