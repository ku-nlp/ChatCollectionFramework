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
    server_process = subprocess.Popen(["python App.py"], shell=True)

    try:
        print(f"server_process={server_process.pid}")

        # Wait 10 seconds to make sure that the server has started properly.
        time.sleep(20)

        # print(f"get_version: {run_command('curl http://127.0.0.1:8993/ChatCollectionFramework_frederic/version')}")
        print(f"get_version: {run_command('curl http://127.0.0.1:8993/ChatCollectionServer/version')}")

        # time.sleep(20)

    finally:
        # Kill the server and its children processes.
        parent = psutil.Process(server_process.pid)
        children = parent.children(recursive=True)
        for process in children:
            process.send_signal(signal.SIGTERM)
        server_process.terminate()

    assert 1 == 1
