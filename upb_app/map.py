from flask import Blueprint, render_template
from upb_app.models import Bendungan, Embung, wil_sungai

bp = Blueprint('map', __name__)


@bp.route('/bendungan')
def bendungan():
    ''' Map Bendungan '''
    bendungan = Bendungan.query.all()
    data = []
    for b in bendungan:
        arr = b.nama.split('_')
        name = f"{arr[0].title()}.{arr[1].title()}"
        data.append({
            'id': b.id,
            'nama': name,
            'kab': b.kab,
            'll': b.ll,
            'wil': wil_sungai[b.wil_sungai],
            'vol': "{:,.0f}".format(b.volume),
            'lbi': "{:,.0f}".format(b.lbi),
            'bend': b
        })
    return render_template('map/bendungan.html', bendungan=data)


@bp.route('/embung')
def embung():
    ''' Map Embung '''
    embung = Embung.query.filter(Embung.is_verified == '1').all()
    data = []
    for e in embung:
        data.append({
            'vol': "{:,.0f}".format(e.tampungan) if e.tampungan else "-",
            'lbi': "{:,.2f}".format(e.irigasi) if e.irigasi else "-",
            'emb': e
        })
    return render_template('map/embung.html', embung=data)
