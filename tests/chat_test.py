import bs4
import json
import os
import os.path
import psutil
import pytest
from random import randint, random, seed
import re
import signal
import subprocess
import time


seed(1)


START_SERVER_DELAY = 30


greetings = [
    "Hello",
    "Hi",
    "Good morning!",
    "Good afternoon!",
    "Hi, what's up?",
    "こんにちは。",
    "おはようございます。",
    "こんばんは。"
]

messages = [
    "How are you?",
    "What a lovely day!",
    "What do you think about death penalty?",
    "I wonder if it's going to rain today.",
    "Do you play soccer?",
    "I do.",
    "I don't think so.",
    "It never happened to me.",
    "I'd rather die than do that.",
    "What could be wrong if I do that?",
    "Do you know how to drive a car?",
    "That will do.",
    "お元気ですか？",
    "お名前はなんですか？",
    "今日の天気がどうですか？",
    "この映画を見たことがありますか？",
    "野球が大好きです。",
    "来年、カナダに行きたいです。",
    "英語が難しいですね。",
    "冬があまり好きじゃない。"
]

farewells = [
    "I have to go, Bye!",
    "It was fun to chat with you.",
    "See you again!",
    "Thanks for your time.",
    "ありがとうございます。",
    "楽しかったです。",
    "もう時間がない。バイ！",
    "またね！"
]


def get_chatroom_id(script_base):
    if script_base == None or script_base.string == None:
        return None

    for line in script_base.string.splitlines():
        p = re.compile(r"^\s+var chatroomId = '(.+)';$")
        m = p.match(line)
        if m:
            return m.group(1)

    return None


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


def test_admin_several_users():
    server_process = subprocess.Popen(["python App.py --config config.json.sample --log_config logging.conf.sample"], shell=True)

    try:
        # Wait a few seconds to make sure that the server has started properly.
        time.sleep(START_SERVER_DELAY)

        for u in range(20):
            session_id = f'1234abcd-aaaa-bbbb-cccc-0000000000{u:02}'
            resp_user = run_command(f'curl -X POST http://127.0.0.1:8993/ChatCollectionServer/join -d "clientTabId=11111" --cookie "CGISESSID={session_id}"')
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
        assert first_h3_text == 'チャットルーム(Active) (10)'

    finally:
        # Kill the server and its children processes.
        parent = psutil.Process(server_process.pid)
        children = parent.children(recursive=True)
        for process in children:
            process.send_signal(signal.SIGTERM)
        server_process.terminate()


def test_admin_several_users_chatting_together():
    server_process = subprocess.Popen(["python App.py --config config.json.sample --log_config logging.conf.sample"], shell=True)

    try:
        # Wait a few seconds to make sure that the server has started properly.
        time.sleep(START_SERVER_DELAY)

        user_count = 10
        msg_count = 80
        user_chatrooms = []
        for u in range(user_count):
            session_id = f'1234abcd-aaaa-bbbb-cccc-0000000000{u:02}'
            resp_user = run_command(f'curl -X POST http://127.0.0.1:8993/ChatCollectionServer/join -d "clientTabId=11111" --cookie "CGISESSID={session_id}"')
            soup = bs4.BeautifulSoup(resp_user, 'html.parser')
            main_box = soup.find(id="main-box")
            assert main_box != None

            send_button = soup.find(id="send")
            assert send_button != None

            script_base = soup.find(id="script-base")
            chatroom_id = get_chatroom_id(script_base)

            user_chatrooms.append(chatroom_id)

        for u in range(user_count):
            msg = greetings[randint(0, len(greetings) - 1)]
            session_id = f'1234abcd-aaaa-bbbb-cccc-0000000000{u:02}'
            resp_greeting_msg = run_command(f'curl -X POST http://127.0.0.1:8993/ChatCollectionServer/post -d "clientTabId=11111" -d "chatroom={user_chatrooms[u]}" -d "message={msg}" --cookie "CGISESSID={session_id}"')
            resp_json = json.loads(resp_greeting_msg.strip().encode('utf-8').decode('unicode_escape')[1:-1])
            assert resp_json['id'] == user_chatrooms[u]

        for m in range(msg_count):
            msg = messages[randint(0, len(messages) -1)]
            user = randint(0, user_count - 1)
            session_id = f'1234abcd-aaaa-bbbb-cccc-0000000000{user:02}'
            resp_msg = run_command(f'curl -X POST http://127.0.0.1:8993/ChatCollectionServer/post -d "clientTabId=11111" -d "chatroom={user_chatrooms[user]}" -d "message={msg}" --cookie "CGISESSID={session_id}"')
            resp_json = json.loads(resp_msg.strip().encode('utf-8').decode('unicode_escape')[1:-1])
            assert resp_json['id'] == user_chatrooms[user]

        for u in range(user_count):
            msg = farewells[randint(0, len(farewells) - 1)]
            session_id = f'1234abcd-aaaa-bbbb-cccc-0000000000{u:02}'
            resp_farewell_msg = run_command(f'curl -X POST http://127.0.0.1:8993/ChatCollectionServer/post -d "clientTabId=11111" -d "chatroom={user_chatrooms[u]}" -d "message={msg}" --cookie "CGISESSID={session_id}"')
            resp_json = json.loads(resp_farewell_msg.strip().encode('utf-8').decode('unicode_escape')[1:-1])
            assert resp_json['id'] == user_chatrooms[u]

        resp_admin = run_command('curl http://127.0.0.1:8993/ChatCollectionServer/admin')
        soup_admin = bs4.BeautifulSoup(resp_admin, 'html.parser')

        h3s = soup_admin.find_all('h3')
        assert len(h3s) == 2

        total_msg_count = 0
        tables = soup_admin.find_all('table')
        first_table = tables[0]
        rows = first_table.find_all('tr')
        for index, row in enumerate(rows):
            if index == 0:
                continue
            cells = row.find_all('td')
            msg_count_cell = cells[2]
            total_msg_count += int(msg_count_cell.string)

        assert total_msg_count == user_count * 2 + msg_count

    finally:
        # Kill the server and its children processes.
        parent = psutil.Process(server_process.pid)
        children = parent.children(recursive=True)
        for process in children:
            process.send_signal(signal.SIGTERM)
        server_process.terminate()
