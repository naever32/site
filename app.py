from os import environ

from flask_migrate import Migrate

from pysite.route_manager import RouteManager

manager = RouteManager()
app = manager.app
migrate = Migrate(app, manager.postgres)

debug = environ.get('TEMPLATES_AUTO_RELOAD', "no")
if debug == "yes":
    app.jinja_env.auto_reload = True

if __name__ == '__main__':
    manager.run()
