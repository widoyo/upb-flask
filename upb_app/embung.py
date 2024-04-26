import datetime
from flask import Blueprint, render_template, request
from sqlalchemy import and_, extract

from upb_app.models import Embung, ManualTmaEmbung

bp = Blueprint('embung', __name__)


@bp.route('/', strict_slashes=False)
def index():
    ''' Home Embung '''
    s = request.args.get('s', None)
    try:
        sampling = datetime.datetime.strptime(s, '%Y-%m-%d')
        _sampling = sampling - datetime.timedelta(days=1)
        sampling_ = sampling + datetime.timedelta(days=1)
    except:
        sampling = datetime.datetime.now()
        _sampling = sampling - datetime.timedelta(days=1)
        sampling_ = None
    if sampling.date() >= datetime.date.today():
        sampling_ = None

    embung = Embung.query.filter(Embung.is_verified=='1').order_by(Embung.wil_sungai, Embung.nama).all()
    tmavol = dict([(t.embung_id, {'tma': t.tma, 'vol': t.vol}) for t in ManualTmaEmbung.query.filter(and_(
                                        extract('month', ManualTmaEmbung.sampling) == sampling.month,
                                        extract('year', ManualTmaEmbung.sampling) == sampling.year,
                                        extract('day', ManualTmaEmbung.sampling) == sampling.day)).order_by(ManualTmaEmbung.sampling.asc())])
    _tmavol = dict([(t.embung_id, {'tma': t.tma, 'vol': t.vol}) for t in ManualTmaEmbung.query.filter(and_(
                                        extract('month', ManualTmaEmbung.sampling) == sampling.month,
                                        extract('year', ManualTmaEmbung.sampling) == sampling.year,
                                        extract('day', ManualTmaEmbung.sampling) == _sampling.day)).order_by(ManualTmaEmbung.sampling.asc())])
    e_hulu = [e for e in embung if e.wil_sungai == '1']
    e_madiun = [e for e in embung if e.wil_sungai == '2']
    e_hilir = [e for e in embung if e.wil_sungai == '3']
    
    for e in e_hulu:
        data = tmavol.get(e.id, None)
        _data = _tmavol.get(e.id, None)
        if data:
            e.tma = data.get('tma')
            e.vol = data.get('vol')
        if _data:
            e._vol = _data.get('vol')
    for e in e_madiun:
        data = tmavol.get(e.id, None)
        _data = _tmavol.get(e.id, None)
        if data:
            e.tma = data.get('tma')
            e.vol = data.get('vol')
        if _data:
            e._vol = _data.get('vol')
    for e in e_hilir:
        data = tmavol.get(e.id, None)
        _data = _tmavol.get(e.id, None)
        if data:
            e.tma = data.get('tma')
            e.vol = data.get('vol')
        if _data:
            e._vol = _data.get('vol')

    ctx = {
        'hulu': {
            'all_embung': e_hulu,
            'tampungan': sum([e.tampungan for e in e_hulu if e.tampungan]),
            'vol': sum([e.vol for e in e_hulu if hasattr(e, 'vol')]),
            '_vol':  sum([e.vol for e in e_hulu if hasattr(e, 'vol')])
        },
        'madiun': {
            'all_embung': e_madiun,
            'tampungan': sum([e.tampungan for e in e_madiun if e.tampungan]),
            'vol': sum([e.vol for e in e_madiun if hasattr(e, 'vol')]),
            '_vol':  sum([e.vol for e in e_hulu if hasattr(e, 'vol')])
        },
        'hilir': {
            'all_embung': e_hilir,
            'tampungan': sum([e.tampungan for e in e_hilir if e.tampungan]),
            'vol': sum([e.vol for e in e_hilir if hasattr(e, 'vol')]),
            '_vol':  sum([e.vol for e in e_hulu if hasattr(e, 'vol')])
        }
    }
    

    return render_template('embung/index.html', ctx=ctx)
