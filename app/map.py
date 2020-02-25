from flask import Blueprint, render_template
from app.models import Bendungan, Embung

bp = Blueprint('map', __name__)


@bp.route('/bendungan')
def bendungan():
    ''' Map Bendungan '''
    return render_template('map/bendungan.html')


@bp.route('/embung')
def embung():
    ''' Map Embung '''
    return render_template('map/embung.html')
