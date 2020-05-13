import os
import logging
from functools import wraps
from flask import Flask, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from flask_login import LoginManager, current_user

app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])
app.config['UPLOAD_FOLDER'] = f"static/img/foto"
app.config['SAVE_DIR'] = f"{os.getcwd()}/upb_app/"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
socketio = SocketIO(app)

db = SQLAlchemy(app)
login = LoginManager(app)
login.login_view = 'login'

# DECORATORS
from upb_app.models import Bendungan


def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.role not in ['1', '4']:
            if current_user.role == '3':
                return redirect(url_for('admin.kegiatan'))
            return redirect(url_for('admin.operasi'))
        return f(*args, **kwargs)
    return decorated_function


def petugas_only(f):
    @wraps(f)
    def decorated_function(bendungan_id, *args, **kwargs):
        if current_user.role not in ['2'] or current_user.bendungan_id != int(bendungan_id):
            return redirect(url_for('admin.operasi'))
        return f(bendungan_id, *args, **kwargs)
    return decorated_function


def role_check(f):
    @wraps(f)
    def decorated_function(bendungan_id, *args, **kwargs):
        if current_user.role in ['2'] and current_user.bendungan_id != int(bendungan_id):
            return redirect(url_for('admin.operasi'))

        return f(bendungan_id, *args, **kwargs)
    return decorated_function


def role_check_embung(f):
    @wraps(f)
    def decorated_function(embung_id, *args, **kwargs):
        if current_user.role in ['3'] and current_user.embung_id != int(embung_id):
            return redirect(url_for('admin.kegiatan'))

        return f(embung_id, *args, **kwargs)
    return decorated_function


from upb_app.api import bp as api_bp
app.register_blueprint(api_bp, url_prefix='/api')

from upb_app.main import bp as main_bp
app.register_blueprint(main_bp, url_prefix='')

from upb_app.map import bp as map_bp
app.register_blueprint(map_bp, url_prefix='/map')

from upb_app.about import bp as about_bp
app.register_blueprint(about_bp, url_prefix='/profile')

from upb_app.admin import bp as admin_bp
app.register_blueprint(admin_bp, url_prefix='/admin')

from upb_app.bendungan import bp as bendungan_bp
app.register_blueprint(bendungan_bp, url_prefix='/bendungan')

from upb_app.embung import bp as embung_bp
app.register_blueprint(embung_bp, url_prefix='/embung')

from upb_app import main, models, command

if __name__ == '__main__':
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)
    socketio.run(app)
