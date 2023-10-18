from gunicorn.app.base import BaseApplication
from server_app import app
import os
import shutil

class FlaskApp(BaseApplication):
    def __init__(self, app, options=None):
        self.options = options or {}
        self.application = app
        super().__init__()

    def load_config(self):
        for key, value in self.options.items():
            if key in self.cfg.settings and value is not None:
                self.cfg.set(key.lower(), value)

    def load(self):
        return self.application

if __name__ == '__main__':
    options = {
        'bind': '0.0.0.0:4000',
        'workers': 4,
    }

    if os.path.exists("backend_runtime"):
        shutil.rmtree("backend_runtime")

    os.makedirs("backend_runtime")

    FlaskApp(app, options).run()
