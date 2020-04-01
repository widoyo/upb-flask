from flask import Blueprint, request, render_template, redirect, url_for, jsonify, flash
from flask_login import login_required, current_user
from sqlalchemy import and_, extract
from sqlalchemy.exc import IntegrityError
from app.models import ManualDaily, ManualTma, ManualPiezo, ManualVnotch
from app.models import Bendungan
from app.forms import AddDaily, AddTma
from app import db, admin_only, petugas_only, get_bendungan
import datetime
import calendar

from app.admin import bp
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
    waduk = Bendungan.query.all()
    date = request.values.get('sampling')
    def_date = datetime.datetime.utcnow()
    sampling = datetime.datetime.strptime(date, "%Y-%m-%d") if date else def_date
    end = sampling + datetime.timedelta(days=1)

    data = []
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
        # if daily:
        #     print(daily.sampling)
        # if tma:
        #     print(tma[0].sampling)
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
            tma_d[f"{t.sampling.hour}"]['vol'] = None if not t.vol else round(t.tma, 2)

        arr = w.nama.split('_')
        name = f"{arr[0].title()}.{arr[1].title()}"
        data.append({
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
    for i in range(day):
        sampl = datetime.datetime.strptime(f"{sampling.year}-{sampling.month}-{i+1}", "%Y-%m-%d")
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
                            name=name,
                            bend_id=bend.id,
                            periodik=periodik,
                            sampling=sampling)


@bp.route('/operasi/bendungan/tma')
@login_required
def operasi_tma_add():
    bendungan_id = current_user.bendungan_id
    form = AddTma()
    if form.validate_on_submit():
        try:
            s_string = f"{form.values.get('hari')} {form.values.get('jam')}:00:00"
            sampling = datetime.datetime.strptime(s_string, "%Y-%m-%d %H:%M:%S")
            tma = ManualTma(
                sampling=sampling,
                tma=form.values.get('tma'),
                vol=form.values.get('volume'),
                bendungan_id=bendungan_id
            )
            db.session.add(tma)
            db.session.commit()
            flash('Tambah TMA berhasil !', 'success')
            return redirect(url_for('admin.operasi_bendungan'))

        except IntegrityError:
            db.session.rollback()
            flash('Data sudah ada, mohon update untuk mengubah', 'danger')

    return render_template('operasi/tma_add.html',
                            form=form)


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


@bp.route('/operasi/bendungan/daily')
@login_required
def operasi_daily_add():
    bendungan_id = current_user.bendungan_id
    form = AddDaily()
    if form.validate_on_submit():
        try:
            daily = ManualDaily(
                sampling=form.values.get('sampling'),
                curahhujan=form.values.get('curahhujan'),
                inflow_deb=form.values.get('inflow_deb'),
                inflow_vol=form.values.get('inflow_vol'),
                outflow_deb=form.values.get('outflow_deb'),
                outflow_vol=form.values.get('outflow_vol'),
                spillway_deb=form.values.get('spillway_deb'),
                spillway_vol=form.values.get('spillway_vol'),
                bendungan_id=bendungan_id
            )
            db.session.add(daily)
            db.session.commit()
            flash('Tambah Daily berhasil !', 'success')
            return redirect(url_for('admin.operasi_bendungan'))

        except IntegrityError:
            db.session.rollback()
            flash('Data sudah ada, mohon update untuk mengubah', 'danger')

    return render_template('operasi/daily_add.html',
                            form=form)


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
