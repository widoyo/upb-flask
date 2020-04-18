from flask import Blueprint, render_template
from sqlalchemy import and_
from upb_app.models import Bendungan, Embung, ManualTma, wil_sungai
import datetime

bp = Blueprint('map', __name__)


@bp.route('/bendungan')
def bendungan():
    ''' Map Bendungan '''
    bendungan = Bendungan.query.all()
    data = []
    for b in bendungan:
        now = datetime.datetime.now() + datetime.timedelta(hours=7)
        # now = datetime.datetime.strptime("2020-01-01", "%Y-%m-%d")
        start = datetime.datetime.strptime(f"{now.year}-{now.month}-{now.day} 00:00:00", "%Y-%m-%d %H:%M:%S")
        tma = ManualTma.query.filter(
                                    and_(
                                        ManualTma.sampling >= start,
                                        ManualTma.sampling <= now),
                                    ManualTma.bendungan_id == b.id
                                    ).order_by(ManualTma.sampling.desc()).first()
        latest = None
        if tma:
            latest = {
                'hour': tma.sampling.hour or "-",
                'vol': "{:,.0f}".format(tma.vol) if tma.vol else "-",
                'tma': "{:,.2f}".format(tma.tma) if tma.tma else "-",
            }
        data.append({
            'id': b.id,
            'nama': b.name,
            'kab': b.kab,
            'll': b.ll,
            'wil': wil_sungai[b.wil_sungai],
            'vol': "{:,.0f}".format(b.volume),
            'lbi': "{:,.0f}".format(b.lbi),
            'latest': latest or None,
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
