from flask import Flask

class BaseApi:

    def __init__(self, cfg):
        self.cfg = cfg

    def version(self):
        return "1.0"


class BaseApp(Flask):

    def __init__(self, import_name, api):
        Flask.__init__(self, import_name)
        self.api = api
        self.cfg = api.cfg

        @self.route('/{}/version'.format(self.cfg['web_context']))
        def version():
            return self.version()


    def version(self):
        return self.api.version()