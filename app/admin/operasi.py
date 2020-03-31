from flask import Blueprint, request, render_template, redirect, url_for, jsonify, flash
from flask_login import login_required, current_user
from sqlalchemy import and_, extract
from sqlalchemy.exc import IntegrityError
from app.models import ManualDaily, ManualTma, ManualPiezo, ManualVnotch
from app.models import Bendungan
from app.forms import AddDaily, AddTma
from app import db
import datetime

from app.admin import bp
# bp = Blueprint('operasi', __name__)


@bp.route('/operasi')
@login_required
def operasi_index():
    if current_user.role == "2":
        return redirect('operasi.bendungan', bendungan_id=current_user.bendungan_id)
    return redirect(url_for('admin.operasi_harian'))


@bp.route('/operasi/harian')
@login_required
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
            '6': None,
            '12': None,
            '18': None,
        }
        for t in tma:
            tma_d[f"{t.sampling.hour}"] = None if not t.tma else round(t.tma/100, 1)

        data.append({
            'id': w.id,
            'nama': w.nama,
            'volume': w.volume,
            'lbi': w.lbi,
            'elev_puncak': w.elev_puncak,
            'muka_air_max': w.muka_air_max,
            'muka_air_min': w.muka_air_min,
            'tma6': tma_d['6'],
            'tma12': tma_d['12'],
            'tma18': tma_d['18'],
            'outflow_vol': None if not daily else daily.outflow_vol,
            'outflow_deb': None if not daily else daily.outflow_deb,
            'spillway_deb': None if not daily else daily.spillway_deb,
            'curahhujan': None if not daily else daily.ch,
            'debit': None if not vnotch else vnotch.vn_deb,
            'piezo': piezo
        })

    return render_template('operasi/index.html',
                            waduk=data,
                            sampling=sampling)


@bp.route('/operasi/<bendungan_id>')
@login_required
def operasi_bendungan(bendungan_id):
    date = request.values.get('sampling') or datetime.datetime.utcnow()
    sampling = datetime.datetime.strptime(f"{date.year}-{date.month}-01", "%Y-%m-%d")

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
    periodik = {}
    for d in manual_daily:
        periodik[d.sampling] = {
            'daily': d,
            'tma': {
                '06': {},
                '12': {},
                '18': {}
            }
        }
    for t in tma:
        sampl = t.sampling.strftime("%Y-%m-%d")
        jam = t.sampling.strftime("%H")
        periodik[sampl]['tma'][jam] = {
            'tma': t.tma,
            'vol': t.vol
        }

    return render_template('operasi/bendungan.html',
                            periodik=periodik,
                            sampling=sampling)


@bp.route('/operasi/<bendungan_id>/tma')
@login_required
def operasi_tma_add(bendungan_id):
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
            return redirect(url_for('operasi.bendungan', bendungan_id=bendungan_id))

        except IntegrityError:
            db.session.rollback()
            flash('Data sudah ada, mohon update untuk mengubah', 'danger')

    return render_template('operasi/tma_add.html',
                            form=form)


@bp.route('/operasi/<bendungan_id>/tma/update')
@login_required
def operasi_tma_update(bendungan_id):
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


@bp.route('/operasi/<bendungan_id>/daily')
@login_required
def operasi_daily_add(bendungan_id):
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
            return redirect(url_for('operasi.bendungan', bendungan_id=bendungan_id))

        except IntegrityError:
            db.session.rollback()
            flash('Data sudah ada, mohon update untuk mengubah', 'danger')

    return render_template('operasi/daily_add.html',
                            form=form)


@bp.route('/operasi/daily/update', methods=['POST'])
@login_required
def operasi_daily_update(bendungan_id):
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
