from flask import Flask, render_template, session
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

        @self.route('/{}/version'.format(self.cfg['web_context']))
        def version():
            return self.version()


    def version(self):
        version = self.api.version()
        try:
            return render_template('version.html', version=version)
        except TemplateNotFound:
            return render_template('default_version.html', version=version)
