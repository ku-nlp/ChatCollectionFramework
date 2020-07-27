from flask import Flask

class BaseApp(Flask):

    def __init__(self, import_name, cfg):
        Flask.__init__(self, import_name)
        self.cfg = cfg

        @self.route('/{}/version'.format(self.cfg['web_context']))
        def version():
            return "1.0"
