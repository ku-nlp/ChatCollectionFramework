import bs4
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


def test_version():
    server_process = subprocess.Popen(["python App.py --config config.json.sample --log_config logging.conf.sample"], shell=True)

    try:
        print(f"server_process={server_process.pid}")

        # Wait a few seconds to make sure that the server has started properly.
        time.sleep(20)

        resp = run_command('curl http://127.0.0.1:8993/ChatCollectionServer/version')
        soup = bs4.BeautifulSoup(resp, 'html.parser')
        body = soup.find('body')
        version = body.string.strip()

        assert version == 'Version: 1.0'

    finally:
        # Kill the server and its children processes.
        parent = psutil.Process(server_process.pid)
        children = parent.children(recursive=True)
        for process in children:
            process.send_signal(signal.SIGTERM)
        server_process.terminate()

    assert 1 == 1
