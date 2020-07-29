from flask import Flask, render_template, send_from_directory, session
from flask_session import Session
from jinja2.exceptions import TemplateNotFound

class BaseApi:

    def __init__(self, cfg, logger):
        self.cfg = cfg
        self.logger = logger

    def version(self):
        return "1.0"


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
