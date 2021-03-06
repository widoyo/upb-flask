from flask import Blueprint, request, render_template, redirect, url_for, jsonify, flash
from flask_login import login_required, current_user
from flask_wtf.csrf import generate_csrf
from sqlalchemy import and_, extract
from sqlalchemy.exc import IntegrityError
from upb_app.models import ManualDaily, ManualTma, ManualPiezo, ManualVnotch
from upb_app.models import Bendungan
from upb_app.forms import AddDaily, AddTma
from upb_app import app, db, admin_only, petugas_only, get_bendungan
import datetime
import calendar

from upb_app.admin import bp
# bp = Blueprint('operasi', __name__)


@bp.route('/operasi')
@login_required
def operasi():
    if current_user.role == "2":
        return redirect(url_for('admin.operasi_bendungan'))
    return redirect(url_for('admin.operasi_harian'))


@bp.route('/operasi/harian')
@login_required
@admin_only
def operasi_harian():
    waduk = Bendungan.query.order_by(Bendungan.wil_sungai, Bendungan.id).all()
    date = request.values.get('sampling')
    def_date = date if date else datetime.datetime.now().strftime("%Y-%m-%d")
    sampling = datetime.datetime.strptime(def_date, "%Y-%m-%d")
    end = sampling + datetime.timedelta(days=1)

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
                                    ).all()

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
            'outflow_deb': None if not daily else daily.outflow_deb,
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


@bp.route('/operasi/bendungan')
@login_required  # @petugas_only
@get_bendungan
def operasi_bendungan(bend):
    date = request.values.get('sampling')
    date = datetime.datetime.strptime(date, "%Y-%m-%d") if date else datetime.datetime.utcnow()
    sampling = datetime.datetime.strptime(f"{date.year}-{date.month}-01", "%Y-%m-%d")

    bendungan_id = bend.id
    arr = bend.nama.split('_')
    name = f"{arr[0].title()}.{arr[1].title()}"

    manual_daily = ManualDaily.query.filter(
                                        ManualDaily.bendungan_id == bendungan_id,
                                        extract('month', ManualDaily.sampling) == sampling.month,
                                        extract('year', ManualDaily.sampling) == sampling.year
                                    ).all()
    tma = ManualTma.query.filter(
                                    ManualTma.bendungan_id == bendungan_id,
                                    extract('month', ManualTma.sampling) == sampling.month,
                                    extract('year', ManualTma.sampling) == sampling.year
                                ).all()

    now = datetime.datetime.now()
    if sampling.year == now.year and sampling.month == now.month:
        day = now.day
    else:
        day = calendar.monthrange(sampling.year, sampling.month)[1]

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
                            sampling=datetime.datetime.today())


@bp.route('/operasi/bendungan/tma', methods=['GET', 'POST'])
@login_required
@get_bendungan
def operasi_tma_add(bend):
    form = AddTma()
    if form.validate_on_submit():
        try:
            insert_tma(
                bend_id=bend.id,
                hari=form.hari.data,
                jam=form.jam.data,
                tma=form.tma.data,
                vol=form.vol.data
            )
            flash('TMA berhasil ditambahkan !', 'success')
            return redirect(url_for('admin.operasi_bendungan', bend_id=bend.id))

        except IntegrityError:
            db.session.rollback()
            flash('Data TMA sudah ada, mohon update untuk mengubah', 'danger')

    return redirect(url_for('admin.operasi_bendungan', bend_id=bend.id))


def insert_tma(bend_id, hari, jam, tma, vol):
    s_string = f"{hari} {jam}:00:00"
    sampling = datetime.datetime.strptime(s_string, "%Y-%m-%d %H:%M:%S")
    tma = ManualTma(
        sampling=sampling,
        tma=tma,
        vol=vol,
        bendungan_id=bend_id
    )
    db.session.add(tma)
    db.session.commit()


@bp.route('/operasi/bendungan/tma/update', methods=['POST'])  # @login_required
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


@bp.route('/operasi/bendungan/daily', methods=['GET', 'POST'])
@login_required
@get_bendungan
def operasi_daily_add(bend):
    form = AddDaily()
    if form.validate_on_submit():
        # insert tma
        try:
            insert_tma(
                bend_id=bend.id,
                hari=form.sampling.data,
                jam=form.jam.data,
                tma=form.tma.data,
                vol=form.vol.data
            )
            flash('TMA berhasil ditambahkan !', 'success')

        except IntegrityError:
            db.session.rollback()
            flash('Data TMA sudah ada, mohon update untuk mengubah', 'danger')

        # insert daily
        try:
            daily = ManualDaily(
                sampling=form.sampling.data,
                ch=form.curahhujan.data,
                inflow_deb=form.inflow_deb.data,
                inflow_vol=form.inflow_vol.data,
                outflow_deb=form.outflow_deb.data,
                outflow_vol=form.outflow_vol.data,
                spillway_deb=form.spillway_deb.data,
                spillway_vol=form.spillway_vol.data,
                bendungan_id=bend.id
            )
            db.session.add(daily)
            db.session.commit()
            flash('Data Harian berhasil ditambahkan !', 'success')
            return redirect(url_for('admin.operasi_bendungan', bend_id=bend.id))

        except IntegrityError:
            db.session.rollback()
            flash('Data sudah ada, mohon update untuk mengubah', 'danger')

    return redirect(url_for('admin.operasi_bendungan', bend_id=bend.id))


@bp.route('/operasi/daily/update', methods=['POST'])  # @login_required
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
