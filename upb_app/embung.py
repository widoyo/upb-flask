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
    alltmavol = [(t.embung_id, {'jam': t.sampling.strftime('%H'), 'tma': t.tma, 'vol': t.vol}) for t in ManualTmaEmbung.query.filter(and_(
                                        extract('month', ManualTmaEmbung.sampling) == sampling.month,
                                        extract('year', ManualTmaEmbung.sampling) == sampling.year,
                                        extract('day', ManualTmaEmbung.sampling) == sampling.day)).order_by(ManualTmaEmbung.sampling.asc())]
    e_hulu = [e for e in embung if e.wil_sungai == '1']
    e_madiun = [e for e in embung if e.wil_sungai == '2']
    e_hilir = [e for e in embung if e.wil_sungai == '3']
    tmavol = {}
    for t in alltmavol:
        if t[0] in tmavol:
            tmavol[t[0]].update({'_' + t[1]['jam']: t[1]})
        else:
            tmavol.update({t[0]: {'_' + t[1]['jam']: t[1]}})
            
    # {embung_id: {_6: {'vol': 1, 'tma': 2}, _18: {'vol': 2, 'tma': 3}}}
    
    for e in e_hulu:
        data = tmavol.get(e.id, None)
        if data:
            for k, v in data.items():
                setattr(e, k, v)
                
    for e in e_madiun:
        data = tmavol.get(e.id, None)
        if data:
            for k, v in data.items():
                setattr(e, k, v)
    for e in e_hilir:
        data = tmavol.get(e.id, None)
        if data:
            for k, v in data.items():
                setattr(e, k, v)

    ctx = {
        'sampling': sampling,
        'hulu': {
            'all_embung': e_hulu,
            'tampungan': sum([e.tampungan for e in e_hulu if e.tampungan]),
            'irigasi': sum([e.irigasi for e in e_hulu if e.irigasi]),
            'vol_06': sum([e._06['vol'] for e in e_hulu if hasattr(e, '_06')]),
            'vol_18': sum([e._18['vol'] for e in e_hulu if hasattr(e, '_18')]),
        },
        'madiun': {
            'all_embung': e_madiun,
            'tampungan': sum([e.tampungan for e in e_madiun if e.tampungan]),
            'irigasi': sum([e.irigasi for e in e_madiun if e.irigasi]),
            'vol_06': sum([e._06['vol'] for e in e_madiun if hasattr(e, '_06')]),
            'vol_18': sum([e._18['vol'] for e in e_madiun if hasattr(e, '_18')]),
        },
        'hilir': {
            'all_embung': e_hilir,
            'tampungan': sum([e.tampungan for e in e_hilir if e.tampungan]),
            'irigasi': sum([e.irigasi for e in e_hilir if e.irigasi]),
            'vol_06': sum([e._06['vol'] for e in e_hilir if hasattr(e, '_06')]),
            'vol_18': sum([e._18['vol'] for e in e_hilir if hasattr(e, '_18')]),
        }
    }

    return render_template('embung/index.html', ctx=ctx)
