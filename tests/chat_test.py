import bs4
import os
import os.path
import psutil
import pytest
import signal
import subprocess
import time


START_SERVER_DELAY = 30


def run_command(command):
    stream = os.popen(command)
    output = stream.read()
    return output


def test_version():
    server_process = subprocess.Popen(["python App.py --config config.json.sample --log_config logging.conf.sample"], shell=True)

    try:
        # Wait a few seconds to make sure that the server has started properly.
        time.sleep(START_SERVER_DELAY)

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


def test_index():
    server_process = subprocess.Popen(["python App.py --config config.json.sample --log_config logging.conf.sample"], shell=True)

    try:
        # Wait a few seconds to make sure that the server has started properly.
        time.sleep(START_SERVER_DELAY)

        resp = run_command('curl http://127.0.0.1:8993/ChatCollectionServer/index')
        soup = bs4.BeautifulSoup(resp, 'html.parser')
        form = soup.find('form')
        assert form['id'] == 'form-join'
        assert form['action'] == 'join'
        assert form['method'] == 'POST'

    finally:
        # Kill the server and its children processes.
        parent = psutil.Process(server_process.pid)
        children = parent.children(recursive=True)
        for process in children:
            process.send_signal(signal.SIGTERM)
        server_process.terminate()


def test_admin_no_users():
    server_process = subprocess.Popen(["python App.py --config config.json.sample --log_config logging.conf.sample"], shell=True)

    try:
        # Wait a few seconds to make sure that the server has started properly.
        time.sleep(START_SERVER_DELAY)

        resp = run_command('curl http://127.0.0.1:8993/ChatCollectionServer/admin')
        soup = bs4.BeautifulSoup(resp, 'html.parser')

        h2 = soup.find('h2')
        h2_text = h2.string.strip()
        assert h2_text == 'チャットサーバー (対話: 123)'

        h3s = soup.find_all('h3')
        assert len(h3s) == 2

        first_h3_text = h3s[0].string.strip()
        assert first_h3_text == 'チャットルーム(Active) (0)'

        second_h3_text = h3s[1].string.strip()
        assert second_h3_text == 'チャットルーム(Disactive) (0)'

    finally:
        # Kill the server and its children processes.
        parent = psutil.Process(server_process.pid)
        children = parent.children(recursive=True)
        for process in children:
            process.send_signal(signal.SIGTERM)
        server_process.terminate()


def test_admin_1_user():
    server_process = subprocess.Popen(["python App.py --config config.json.sample --log_config logging.conf.sample"], shell=True)

    try:
        # Wait a few seconds to make sure that the server has started properly.
        time.sleep(START_SERVER_DELAY)

        resp_user = run_command('curl -X POST http://127.0.0.1:8993/ChatCollectionServer/join -d "clientTabId=11111"')
        soup = bs4.BeautifulSoup(resp_user, 'html.parser')
        main_box = soup.find(id="main-box")
        assert main_box != None

        send_button = soup.find(id="send")
        assert send_button != None

        resp_admin = run_command('curl http://127.0.0.1:8993/ChatCollectionServer/admin')
        soup_admin = bs4.BeautifulSoup(resp_admin, 'html.parser')

        h3s = soup_admin.find_all('h3')
        assert len(h3s) == 2

        first_h3_text = h3s[0].string.strip()
        assert first_h3_text == 'チャットルーム(Active) (1)'

    finally:
        # Kill the server and its children processes.
        parent = psutil.Process(server_process.pid)
        children = parent.children(recursive=True)
        for process in children:
            process.send_signal(signal.SIGTERM)
        server_process.terminate()


def test_admin_1_user_2_tabs_forbidden_access():
    server_process = subprocess.Popen(["python App.py --config config.json.sample --log_config logging.conf.sample"], shell=True)

    try:
        # Wait a few seconds to make sure that the server has started properly.
        time.sleep(START_SERVER_DELAY)

        resp_user_tab_1 = run_command('curl -X POST http://127.0.0.1:8993/ChatCollectionServer/join -d "clientTabId=11111" --cookie "CGISESSID=1234abcd-aaaa-bbbb-cccc-000000000000"')
        soup = bs4.BeautifulSoup(resp_user_tab_1, 'html.parser')
        main_box = soup.find(id="main-box")
        assert main_box != None

        send_button = soup.find(id="send")
        assert send_button != None

        resp_user_tab_2 = run_command('curl -X POST http://127.0.0.1:8993/ChatCollectionServer/join -d "clientTabId=22222" --cookie "CGISESSID=1234abcd-aaaa-bbbb-cccc-000000000000"')
        soup = bs4.BeautifulSoup(resp_user_tab_2, 'html.parser')
        main_box = soup.find(id="main-box")
        assert main_box == None

        send_button = soup.find(id="send")
        assert send_button == None

        resp_admin = run_command('curl http://127.0.0.1:8993/ChatCollectionServer/admin')
        soup_admin = bs4.BeautifulSoup(resp_admin, 'html.parser')

        h3s = soup_admin.find_all('h3')
        assert len(h3s) == 2

        first_h3_text = h3s[0].string.strip()
        assert first_h3_text == 'チャットルーム(Active) (1)'

    finally:
        # Kill the server and its children processes.
        parent = psutil.Process(server_process.pid)
        children = parent.children(recursive=True)
        for process in children:
            process.send_signal(signal.SIGTERM)
        server_process.terminate()


