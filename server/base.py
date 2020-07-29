from flask import Flask, render_template, send_from_directory, session
from flask_session import Session
from jinja2.exceptions import TemplateNotFound
import pytz
import threading


tz = pytz.timezone('Asia/Tokyo')

def utc_to_local(utc_timestamp):
    return datetime.fromisoformat("{}+00:00".format(utc_timestamp)).astimezone(tz).isoformat() if utc_timestamp else ""

def convert_chatroom_to_dict(chatroom):
    return {
        "id": chatroom.id,
        "experimentId": chatroom.experiment_id,
        "users": chatroom.users,
        "created": chatroom.created,
        "modified": chatroom.modified,
        "initiator": chatroom.initiator,
        "closed": chatroom.closed,
        "events": len(chatroom.events),
        "poll_requests": chatroom.poll_requests
    }


class BaseApi:

    def __init__(self, cfg, logger):
        self.cfg = cfg
        self.logger = logger

        self.mutex = threading.Lock()

        self.users = {}

        # Dictionaries organized by chatroom ids.
        self.chatrooms = {}
        self.chatroom_locks = {}
        self.released_chatrooms = {}

    def version(self):
        return "1.0"

    def get_chatrooms(self):
        return {
            "chatrooms": list(self.chatrooms.values()),
            "released_chatrooms": list(self.released_chatrooms.values())
        }


class BaseApp(Flask):

    def __init__(self, import_name, api):
        Flask.__init__(self, import_name)
        self.api = api
        self.cfg = api.cfg
        self.logger = api.logger

        self.SESSION_TYPE = 'filesystem'
        self.SESSION_COOKIE_NAME = 'CGISESSID'
        self.SESSION_FILE_DIR = self.cfg['sessions']
        self.SESSION_COOKIE_PATH = self.cfg['cookiePath']
        self.SESSION_COOKIE_SECURE = True

        self.config.from_object(self)
        Session(self)

        @self.route('/{}/static/<path:path>'.format(self.cfg['web_context']))
        def get_static(path):
            return self.get_static(path)

        @self.route('/{}/version'.format(self.cfg['web_context']))
        def version():
            return self.version()

        @self.route('/{}/index'.format(self.cfg['web_context']))
        def index():
            return self.index()

        @self.route('/{}/admin'.format(self.cfg['web_context']))
        def admin():
            return self.admin()

    def get_static(self, path):
        return send_from_directory('static', path)

    def version(self):
        version = self.api.version()
        try:
            return render_template('version.html', version=version)
        except TemplateNotFound:
            return render_template('default_version.html', version=version)

    def index(self):
        try:
            return render_template('index.html')
        except TemplateNotFound:
            return render_template('default_index.html')

    def admin(self):
        data = self.api.get_chatrooms()
        chatrooms = [convert_chatroom_to_dict(chatroom) for chatroom in data['chatrooms']]
        released_chatrooms = [convert_chatroom_to_dict(released_chatrooms)
                                for released_chatrooms in data['released_chatrooms']]
        try:
            return render_template(
                'admin.html',
                chatrooms=chatrooms,
                released_chatrooms=released_chatrooms,
                experiment_id=self.cfg['experiment_id'],
                utc_to_local=utc_to_local)
        except TemplateNotFound:
            return render_template(
                'default_admin.html',
                chatrooms=chatrooms,
                released_chatrooms=released_chatrooms,
                experiment_id=self.cfg['experiment_id'],
                utc_to_local=utc_to_local)
