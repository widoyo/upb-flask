from flask import Blueprint, jsonify, request
from upb_app.helper import day_range
from upb_app.models import Bendungan, ManualDaily, ManualTma, ManualPiezo, ManualVnotch
from sqlalchemy import and_


bp = Blueprint('api', __name__)


@bp.route('/bendungan/periodic')
def bendungan_periodic():
    sampling, end = day_range(request.values.get('sampling'))

    result = []
    bendungan = Bendungan.query.all()
    for bend in bendungan:
        daily = ManualDaily.query.filter(
                                    and_(
                                        ManualDaily.sampling >= sampling,
                                        ManualDaily.sampling <= end),
                                    ManualDaily.bendungan_id == bend.id
                                    ).first()
        vnotch = ManualVnotch.query.filter(
                                    and_(
                                        ManualVnotch.sampling >= sampling,
                                        ManualVnotch.sampling <= end),
                                    ManualVnotch.bendungan_id == bend.id
                                    ).first()
        tma = ManualTma.query.filter(
                                    and_(
                                        ManualTma.sampling >= sampling,
                                        ManualTma.sampling <= end),
                                    ManualTma.bendungan_id == bend.id
                                    ).all()
        piezo = ManualPiezo.query.filter(
                                    and_(
                                        ManualPiezo.sampling >= sampling,
                                        ManualPiezo.sampling <= end),
                                    ManualPiezo.bendungan_id == bend.id
                                    ).first()
        tma_d = {
            '6': {'tma': None, 'vol': None},
            '12': {'tma': None, 'vol': None},
            '18': {'tma': None, 'vol': None},
        }
        for t in tma:
            tma_d[f"{t.sampling.hour}"]['tma'] = None if not t.tma else round(t.tma, 2)
            tma_d[f"{t.sampling.hour}"]['vol'] = None if not t.vol else round(t.vol, 2)
        result.append(
            {
                "sampling": sampling.strftime("%Y-%m-%d %H:%M:%S"),
                "tma6": tma_d['6']['tma'],
                "tma12": tma_d['12']['tma'],
                "tma18": tma_d['18']['tma'],
                "vol6": tma_d['6']['vol'],
                "vol12": tma_d['12']['vol'],
                "vol18": tma_d['18']['vol'],
                "name": bend.nama,
                "curahhujan": daily.ch if daily else None,
                "intake_q": daily.intake_deb if daily else None,
                "inflow_v": daily.inflow_vol if daily else None,
                "inflow_q": daily.inflow_deb if daily else None,
                "intake_v": daily.intake_vol if daily else None,
                "spillway_v": daily.spillway_vol if daily else None,
                "spillway_q": daily.spillway_deb if daily else None,
                "a1": piezo.p1a if piezo else None,
                "a2": piezo.p2a if piezo else None,
                "a3": piezo.p3a if piezo else None,
                "a4": piezo.p4a if piezo else None,
                "a5": piezo.p5a if piezo else None,
                "b1": piezo.p1b if piezo else None,
                "b2": piezo.p2b if piezo else None,
                "b3": piezo.p3b if piezo else None,
                "b4": piezo.p4b if piezo else None,
                "b5": piezo.p5b if piezo else None,
                "c1": piezo.p1c if piezo else None,
                "c2": piezo.p2c if piezo else None,
                "c3": piezo.p3c if piezo else None,
                "c4": piezo.p4c if piezo else None,
                "c5": piezo.p5c if piezo else None,
                "vnotch_q1": vnotch.vn1_deb if vnotch else None,
                "vnotch_q2": vnotch.vn2_deb if vnotch else None,
                "vnotch_q3": vnotch.vn3_deb if vnotch else None,
                "vnotch_tin1": vnotch.vn1_tma if vnotch else None,
                "vnotch_tin2": vnotch.vn2_tma if vnotch else None,
                "vnotch_tin3": vnotch.vn3_tma if vnotch else None
            }
        )
    return jsonify(result)
