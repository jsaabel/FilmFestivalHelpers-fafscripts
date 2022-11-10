from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from fafscripts.config import Config
import logging
from logging.handlers import RotatingFileHandler
# from markupsafe import escape

db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = 'users.login'
login_manager.login_message_category = 'info'



def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)

    from fafscripts.users.routes import users
    from fafscripts.main.routes import main
    from fafscripts.scripts.routes import scripts
    from fafscripts.dbviews.routes import dbviews
    app.register_blueprint(users)
    app.register_blueprint(main)
    app.register_blueprint(scripts)
    app.register_blueprint(dbviews)

    handler = RotatingFileHandler('logs/log.log',
            maxBytes=100_000, backupCount=5)
    logging.basicConfig(handlers=[handler], level=logging.INFO, 
            format=f'%(asctime)s %(levelname)s %(name)s * %(message)s')
    
    return app

