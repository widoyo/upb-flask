from flask import Blueprint, request, render_template, redirect
from flask import url_for, jsonify, flash, Response
from flask_login import login_required, current_user
from flask_wtf.csrf import generate_csrf
from sqlalchemy import and_, extract
from sqlalchemy.exc import IntegrityError
from upb_app.models import ManualDaily, ManualTma, ManualPiezo, ManualVnotch
from upb_app.models import Bendungan, BendungAlert, CurahHujanTerkini
from upb_app.forms import AddDaily, AddTma, LaporBanjir, CHTerkini
from upb_app import app, db, admin_only, petugas_only, role_check
import datetime
import calendar
import csv
import io

from upb_app.admin import bp
# bp = Blueprint('operasi', __name__)


@bp.route('/operasi')
@login_required
def operasi():
    if current_user.role == "2":
        return redirect(url_for('admin.operasi_bendungan', bendungan_id=current_user.bendungan_id))
    return redirect(url_for('admin.operasi_harian'))


@bp.route('/operasi/harian')
@login_required
@admin_only
def operasi_harian():
    waduk = Bendungan.query.order_by(Bendungan.wil_sungai, Bendungan.id).all()
    date = request.values.get('sampling')
    def_date = date if date else datetime.datetime.now().strftime("%Y-%m-%d")
    sampling = datetime.datetime.strptime(def_date, "%Y-%m-%d")
    end = sampling + datetime.timedelta(hours=23, minutes=55)

    data = {
        '1': [],
        '2': [],
        '3': []
    }
    count = 1
    for w in waduk:
        daily = ManualDaily.query.filter(
                                    and_(
                                        ManualDaily.sampling >= sampling,
                                        ManualDaily.sampling <= end),
                                    ManualDaily.bendungan_id == w.id
                                    ).first()
        vnotch = ManualVnotch.query.filter(
                                    and_(
                                        ManualVnotch.sampling >= sampling,
                                        ManualVnotch.sampling <= end),
                                    ManualVnotch.bendungan_id == w.id
                                    ).first()
        tma = ManualTma.query.filter(
                                    and_(
                                        ManualTma.sampling >= sampling,
                                        ManualTma.sampling <= end),
                                    ManualTma.bendungan_id == w.id
                                    ).all()
        piezo = ManualPiezo.query.filter(
                                    and_(
                                        ManualPiezo.sampling >= sampling,
                                        ManualPiezo.sampling <= end),
                                    ManualPiezo.bendungan_id == w.id
                                    ).first()

        tma_d = {
            '6': {
                'tma': None,
                'vol': None
            },
            '12': {
                'tma': None,
                'vol': None
            },
            '18': {
                'tma': None,
                'vol': None
            },
        }
        for t in tma:
            tma_d[f"{t.sampling.hour}"]['tma'] = None if not t.tma else round(t.tma, 2)
            tma_d[f"{t.sampling.hour}"]['vol'] = None if not t.vol else round(t.vol, 2)

        arr = w.nama.split('_')
        name = f"{arr[0].title()}.{arr[1].title()}"
        data[w.wil_sungai].append({
            'no': count,
            'id': w.id,
            'nama': name,
            'volume': w.volume,
            'lbi': w.lbi,
            'elev_puncak': w.elev_puncak,
            'muka_air_max': w.muka_air_max,
            'muka_air_min': w.muka_air_min,
            'tma6': tma_d['6'],
            'tma12': tma_d['12'],
            'tma18': tma_d['18'],
            'inflow_deb': None if not daily else daily.inflow_deb,
            'intake_deb': None if not daily else daily.intake_deb,
            'spillway_deb': None if not daily else daily.spillway_deb,
            'curahhujan': None if not daily else daily.ch,
            'tinggi': None if not vnotch else vnotch.vn1_tma,
            'debit': None if not vnotch else vnotch.vn1_deb,
            'piezo': piezo
        })
        count += 1

    return render_template('operasi/index.html',
                            bends=data,
                            sampling=sampling)


@bp.route('/bendungan/operasi/<bendungan_id>')
@login_required  # @petugas_only
@role_check
def operasi_bendungan(bendungan_id):
    bend = Bendungan.query.get(bendungan_id)

    date = request.values.get('sampling')
    date = datetime.datetime.strptime(date, "%Y-%m-%d") if date else datetime.datetime.utcnow()
    sampling = datetime.datetime.strptime(f"{date.year}-{date.month}-01", "%Y-%m-%d")

    now = datetime.datetime.now()
    if sampling.year == now.year and sampling.month == now.month:
        day = now.day
    else:
        day = calendar.monthrange(sampling.year, sampling.month)[1]
    end = datetime.datetime.strptime(f"{date.year}-{date.month}-{day} 23:59:59", "%Y-%m-%d %H:%M:%S")

    arr = bend.nama.split('_')
    name = f"{arr[0].title()}.{arr[1].title()}"

    manual_daily = ManualDaily.query.filter(
                                        ManualDaily.bendungan_id == bendungan_id,
                                        ManualDaily.sampling.between(sampling, end)
                                    ).all()
    tma = ManualTma.query.filter(
                                    ManualTma.bendungan_id == bendungan_id,
                                    ManualTma.sampling.between(sampling, end)
                                ).all()

    periodik = {}
    for i in range(day, 0, -1):
        sampl = datetime.datetime.strptime(f"{sampling.year}-{sampling.month}-{i}", "%Y-%m-%d")
        periodik[sampl] = {
            'daily': None,
            'tma': {
                '06': None,
                '12': None,
                '18': None
            }
        }
    for d in manual_daily:
        periodik[d.sampling]['daily'] = d
    for t in tma:
        sampl = t.sampling.replace(hour=0)
        jam = t.sampling.strftime("%H")
        periodik[sampl]['tma'][jam] = t

    return render_template('operasi/bendungan.html',
                            csrf=generate_csrf(),
                            name=name,
                            bend_id=bend.id,
                            periodik=periodik,
                            sampling=datetime.datetime.now(),
                            sampling_dt=sampling)


@bp.route('/bendungan/operasi/<bendungan_id>/tma', methods=['GET', 'POST'])
@login_required
@role_check
def operasi_tma_add(bendungan_id):
    bend = Bendungan.query.get(bendungan_id)
    form = AddTma()
    if form.validate_on_submit():
        insert_tma(
            bend_id=bend.id,
            hari=form.hari.data,
            jam=form.jam.data,
            tma=form.tma.data,
            vol=form.vol.data
        )

    return redirect(url_for('admin.operasi_bendungan', bendungan_id=bend.id))


def insert_tma(bend_id, hari, jam, tma, vol):
    s_string = f"{hari} {jam}:00:00"
    sampling = datetime.datetime.strptime(s_string, "%Y-%m-%d %H:%M:%S")
    try:
        obj_dict = {
            "sampling": sampling,
            "tma": tma,
            "vol": vol,
            "bendungan_id": bend_id
        }
        row = ManualTma.query.filter(
                                    ManualTma.sampling == obj_dict['sampling'],
                                    ManualTma.bendungan_id == obj_dict['bendungan_id']
                                ).first()
        if row:
            for key, value in obj_dict.items():
                setattr(row, key, value)
        else:
            tma = ManualTma(**obj_dict)
            db.session.add(tma)
        db.session.commit()
        flash('TMA berhasil ditambahkan !', 'success')
    except Exception as e:
        db.session.rollback()
        print(f"TMA Manual Error : {e.__class__.__name__}")
        flash(f"Terjadi kesalahan saat mencoba menyimpan data", 'danger')


@bp.route('/bendungan/operasi/tma/update', methods=['POST'])  # @login_required
def operasi_tma_update():
    pk = request.values.get('pk')
    attr = request.values.get('name')
    val = request.values.get('value')

    row = ManualTma.query.get(pk)
    setattr(row, attr, val)
    db.session.commit()

    result = {
        "name": attr,
        "pk": pk,
        "value": val
    }
    return jsonify(result)


@bp.route('/bendungan/operasi/<bendungan_id>/daily', methods=['GET', 'POST'])
@login_required
@role_check
def operasi_daily_add(bendungan_id):
    bend = Bendungan.query.get(bendungan_id)
    form = AddDaily()
    if form.validate_on_submit():
        # insert tma
        insert_tma(
            bend_id=bend.id,
            hari=form.sampling.data,
            jam=form.jam.data,
            tma=form.tma.data,
            vol=form.vol.data
        )
        # insert daily
        try:
            obj_dict = {
                "sampling": form.sampling.data,
                "ch": form.curahhujan.data,
                "inflow_deb": form.inflow_deb.data,
                "inflow_vol": form.inflow_vol.data,
                "intake_deb": form.intake_deb.data,
                "intake_vol": form.intake_vol.data,
                "spillway_deb": form.spillway_deb.data,
                "spillway_vol": form.spillway_vol.data,
                "bendungan_id": bend.id
            }
            row = ManualDaily.query.filter(
                                        ManualDaily.sampling == obj_dict['sampling'],
                                        ManualDaily.bendungan_id == obj_dict['bendungan_id']
                                    ).first()
            if row:
                for key, value in obj_dict.items():
                    setattr(row, key, value)
            else:
                daily = ManualDaily(**obj_dict)
                db.session.add(daily)
            db.session.commit()
            flash('Data Harian berhasil ditambahkan !', 'success')
            return redirect(url_for('admin.operasi_bendungan', bendungan_id=bend.id))

        except Exception as e:
            db.session.rollback()
            print(f"Daily Manual Error : {e.__class__.__name__}")
            flash(f"Terjadi kesalahan saat mencoba menyimpan data", 'danger')

    return redirect(url_for('admin.operasi_bendungan', bendungan_id=bend.id))


@bp.route('/bendungan/operasi/daily/update', methods=['POST'])  # @login_required
def operasi_daily_update():
    pk = request.values.get('pk')
    attr = request.values.get('name')
    val = request.values.get('value')

    row = ManualDaily.query.get(pk)
    setattr(row, attr, val)
    db.session.commit()

    result = {
        "name": attr,
        "pk": pk,
        "value": val
    }
    return jsonify(result)


@bp.route('/bendungan/operasi/<bendungan_id>/banjir', methods=['POST'])
@login_required
@role_check
def banjir_add(bendungan_id):
    form = LaporBanjir()
    if form.validate_on_submit():
        try:
            tgl = form.tanggal.data
            jam = form.jam.data.replace('.', ':')
            sampling = datetime.datetime.strptime(f"{tgl} {jam}", "%Y-%m-%d %H:%M:%S")
            alert = BendungAlert(
                sampling=sampling,
                tma=form.tma.data,
                spillway_deb=form.spillway_deb.data,
                bendungan_id=bendungan_id
            )
            db.session.add(alert)
            db.session.commit()
            flash('Laporan Banjir berhasil ditambahkan !', 'success')

        except Exception as e:
            db.session.rollback()
            flash("Terjadi Error", 'danger')

    return redirect(url_for('admin.operasi_bendungan', bendungan_id=bendungan_id))


@bp.route('/bendungan/operasi/<bendungan_id>/curahhujan', methods=['POST'])
@login_required
@role_check
def ch_terkini(bendungan_id):
    form = CHTerkini()
    if form.validate_on_submit():
        try:
            tgl = form.tanggal.data
            jam = form.jam.data.replace('.', ':')
            sampling = datetime.datetime.strptime(f"{tgl} {jam}", "%Y-%m-%d %H:%M:%S")
            alert = CurahHujanTerkini(
                sampling=sampling,
                ch=form.ch.data,
                bendungan_id=bendungan_id
            )
            print(alert.ch)
            db.session.add(alert)
            db.session.commit()
            flash('Curah Hujan Terkini berhasil ditambahkan !', 'success')

        except Exception as e:
            db.session.rollback()
            print(f"{e}")
            flash("Terjadi Error", 'danger')

    return redirect(url_for('admin.operasi_bendungan', bendungan_id=bendungan_id))


@bp.route('/bendungan/operasi/<bendungan_id>/csv', methods=['GET'])
@login_required
@role_check
def operasi_csv(bendungan_id):
    bend = Bendungan.query.get(bendungan_id)

    date = request.values.get('sampling')
    date = datetime.datetime.strptime(date, "%Y-%m-%d") if date else datetime.datetime.utcnow()
    sampling = datetime.datetime.strptime(f"{date.year}-{date.month}-01", "%Y-%m-%d")

    now = datetime.datetime.now()
    if sampling.year == now.year and sampling.month == now.month:
        day = now.day
    else:
        day = calendar.monthrange(sampling.year, sampling.month)[1]
    end = datetime.datetime.strptime(f"{date.year}-{date.month}-{day} 23:59:59", "%Y-%m-%d %H:%M:%S")

    manual_daily = ManualDaily.query.filter(
                                        ManualDaily.bendungan_id == bendungan_id,
                                        ManualDaily.sampling.between(sampling, end),
                                        # extract('month', ManualDaily.sampling) == sampling.month,
                                        # extract('year', ManualDaily.sampling) == sampling.year
                                    ).all()
    tma = ManualTma.query.filter(
                                    ManualTma.bendungan_id == bendungan_id,
                                    ManualTma.sampling.between(sampling, end),
                                    # extract('month', ManualTma.sampling) == sampling.month,
                                    # extract('year', ManualTma.sampling) == sampling.year
                                ).all()
    vnotch = ManualVnotch.query.filter(
                                    ManualVnotch.bendungan_id == bendungan_id,
                                    ManualVnotch.sampling.between(sampling, end),
                                    # extract('month', ManualTma.sampling) == sampling.month,
                                    # extract('year', ManualTma.sampling) == sampling.year
                                ).all()
    piezo = ManualPiezo.query.filter(
                                    ManualPiezo.bendungan_id == bendungan_id,
                                    ManualPiezo.sampling.between(sampling, end),
                                    # extract('month', ManualTma.sampling) == sampling.month,
                                    # extract('year', ManualTma.sampling) == sampling.year
                                ).all()

    periodik = {}
    for i in range(day):
        sampl = datetime.datetime.strptime(f"{sampling.year}-{sampling.month}-{i+1}", "%Y-%m-%d")
        periodik[sampl] = {
            'daily': None,
            'tma': {
                '06': None,
                '12': None,
                '18': None
            },
            'vnotch': None,
            'piezo': None
        }
    for d in manual_daily:
        periodik[d.sampling]['daily'] = d
    for t in tma:
        sampl = t.sampling.replace(hour=0)
        jam = t.sampling.strftime("%H")
        periodik[sampl]['tma'][jam] = t
    for v in vnotch:
        periodik[d.sampling]['vnotch'] = v
    for p in piezo:
        periodik[d.sampling]['piezo'] = p

    pre_csv = []
    pre_csv.append([
        'waktu','curahhujan','tma6','vol6','tma12','vol12','tma18','vol18',
        'inflow_q','inflow_v','intake_q','intake_v','outflow_q','outflow_v','spillway_q','spillway_v',
        'vnotch_tin1','vnotch_q1','vnotch_tin2','vnotch_q2','vnotch_tin3','vnotch_q3',
        'a1','a2','a3','a4','a5','b1','b2','b3','b4','b5','c1','c2','c3','c4','c5'
    ])
    for sampl, data in periodik.items():
        pre_csv.append([
            sampl.strftime('%Y-%m-%d %H:%M:%S'),
            data['daily'].ch if data['daily'] else None,
            data['tma']['06'].tma if data['tma']['06'] else None,
            data['tma']['06'].vol if data['tma']['06'] else None,
            data['tma']['12'].tma if data['tma']['12'] else None,
            data['tma']['12'].vol if data['tma']['12'] else None,
            data['tma']['18'].tma if data['tma']['18'] else None,
            data['tma']['18'].vol if data['tma']['18'] else None,
            data['daily'].inflow_deb if data['daily'] else None,
            data['daily'].inflow_vol if data['daily'] else None,
            data['daily'].intake_deb if data['daily'] else None,
            data['daily'].intake_vol if data['daily'] else None,
            data['daily'].outflow_deb if data['daily'] else None,
            data['daily'].outflow_vol if data['daily'] else None,
            data['daily'].spillway_deb if data['daily'] else None,
            data['daily'].spillway_vol if data['daily'] else None,
            data['vnotch'].vn1_tma if data['vnotch'] else None,
            data['vnotch'].vn1_deb if data['vnotch'] else None,
            data['vnotch'].vn2_tma if data['vnotch'] else None,
            data['vnotch'].vn2_deb if data['vnotch'] else None,
            data['vnotch'].vn3_tma if data['vnotch'] else None,
            data['vnotch'].vn3_deb if data['vnotch'] else None,
            data['piezo'].p1a if data['piezo'] else None,
            data['piezo'].p2a if data['piezo'] else None,
            data['piezo'].p3a if data['piezo'] else None,
            data['piezo'].p4a if data['piezo'] else None,
            data['piezo'].p5a if data['piezo'] else None,
            data['piezo'].p1b if data['piezo'] else None,
            data['piezo'].p2b if data['piezo'] else None,
            data['piezo'].p3b if data['piezo'] else None,
            data['piezo'].p4b if data['piezo'] else None,
            data['piezo'].p5b if data['piezo'] else None,
            data['piezo'].p1c if data['piezo'] else None,
            data['piezo'].p2c if data['piezo'] else None,
            data['piezo'].p3c if data['piezo'] else None,
            data['piezo'].p4c if data['piezo'] else None,
            data['piezo'].p5c if data['piezo'] else None
        ])
    output = io.StringIO()
    writer = csv.writer(output, delimiter='\t')
    for l in pre_csv:
        writer.writerow(l)
    output.seek(0)

    return Response(output,
                    mimetype="text/csv",
                    headers={
                        "Content-Disposition": f"attachment;filename={bend.nama}-{sampling.strftime('%d %B %Y')}.csv"
                    })
