import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from flask_login import LoginManager

app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
socketio = SocketIO(app)

db = SQLAlchemy(app)
login = LoginManager(app)
login.login_view = 'login'

from app.api import bp as api_bp
app.register_blueprint(api_bp, url_prefix='/api')

from app.main import bp as main_bp
app.register_blueprint(main_bp, url_prefix='')

from app.about import bp as about_bp
app.register_blueprint(about_bp, url_prefix='/profile')

# from app.operasi import bp as operasi_bp
# app.register_blueprint(operasi_bp, url_prefix='/operasi')
#
# from app.keamanan import bp as keamanan_bp
# app.register_blueprint(keamanan_bp, url_prefix='/keamanan')
#
# from app.kinerja import bp as kinerja_bp
# app.register_blueprint(kinerja_bp, url_prefix='/kinerja')
#
# from app.kegiatan import bp as kegiatan_bp
# app.register_blueprint(kegiatan_bp, url_prefix='/kegiatan')
#
# from app.users import bp as users_bp
# app.register_blueprint(users_bp, url_prefix='/users')

from app.bendungan import bp as bendungan_bp
app.register_blueprint(bendungan_bp, url_prefix='/bendungan')

from app.embung import bp as embung_bp
app.register_blueprint(embung_bp, url_prefix='/embung')

from app import main, models, command

if __name__ == '__main__':
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)
    socketio.run(app)
