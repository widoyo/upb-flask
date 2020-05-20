from flask import Blueprint, render_template, request
from upb_app.models import Embung

bp = Blueprint('embung', __name__)


@bp.route('/')
def index():
    ''' Home Embung '''
    view = request.values.get('view')
    if view == 'all':
        embung = Embung.query.all()
    else:
        embung = Embung.query.filter(Embung.is_verified == '1').all()

    embung_a = []
    embung_b = []
    for e in embung:
        if e.jenis == 'a':
            embung_a.append(e)
        elif e.jenis == 'b':
            embung_b.append(e)
    return render_template('embung/index.html',
                            embung_a=embung_a,
                            embung_b=embung_b)
