from flask import Flask
from flask.ext.bootstrap import Bootstrap
from flask.ext.mail import Mail
from flask.ext.moment import Moment
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager
from flask.ext.pagedown import PageDown
from config import config
from flask_oauthlib.client import OAuth
from flask.ext.admin import Admin
from flask.ext.admin.contrib.sqla import ModelView
from flask.ext.login import current_user

bootstrap = Bootstrap()
mail = Mail()
moment = Moment()
db = SQLAlchemy()
pagedown = PageDown()
oauth = OAuth()
admin = Admin(name='DD-CSS')

login_manager = LoginManager()
login_manager.session_protection = 'strong'
login_manager.login_view = 'auth.login'


def create_app(config_name):
    #app = Flask(__name__)
    app = Flask(__name__.split('.')[0])
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    bootstrap.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)
    pagedown.init_app(app)
    oauth.init_app(app)

    
    class MyUser(ModelView):
        # Disable model creation
        can_create = False
    
        # Override displayed fields
        column_list = ('email','username','confirmed','name','location','about_me','member_since','last_seen')
    
        def __init__(self, session, **kwargs):
            # You can pass name and other parameters if you want to
            super(MyUser, self).__init__(User, session, **kwargs)
    
        def is_accessible(self):
            return current_user.get_id() == u'1'

    from models import User
    admin.init_app(app)
    admin.add_view(MyUser(db.session))
    
    
    """
    if not app.debug and not app.testing and not app.config['SSL_DISABLE']:
        from flask.ext.sslify import SSLify
        sslify = SSLify(app)
    """

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    from .tw import tw as tw_blueprint
    app.register_blueprint(tw_blueprint, url_prefix='/tw')

    from .fb import fb as fb_blueprint
    app.register_blueprint(fb_blueprint, url_prefix='/fb')
#    from .api_1_0 import api as api_1_0_blueprint
#    app.register_blueprint(api_1_0_blueprint, url_prefix='/api/v1.0')

    return app

