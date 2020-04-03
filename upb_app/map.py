from flask import Blueprint, render_template
from upb_app.models import Bendungan, Embung

bp = Blueprint('map', __name__)


@bp.route('/bendungan')
def bendungan():
    ''' Map Bendungan '''
    bendungan = Bendungan.query.all()
    return render_template('map/bendungan.html', bendungan=bendungan)


@bp.route('/embung')
def embung():
    ''' Map Embung '''
    embung = Embung.query.all()
    return render_template('map/embung.html', embung=embung)
