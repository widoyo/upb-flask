from flask import Blueprint, request, render_template, redirect, url_for, jsonify, flash
from flask_login import login_required, current_user
from flask_wtf.csrf import generate_csrf
from sqlalchemy import extract, and_
from sqlalchemy.exc import IntegrityError
from upb_app.models import ManualVnotch, ManualPiezo, Bendungan
from upb_app.forms import AddVnotch, AddPiezo
from upb_app import db, petugas_only, get_bendungan
import datetime
import calendar

from upb_app.admin import bp
# bp = Blueprint('keamanan', __name__)


@bp.route('/keamanan')
@login_required
def keamanan():
    if current_user.role == "2":
        return redirect(url_for('admin.keamanan_bendungan'))
    return redirect(url_for('admin.operasi_harian'))


@bp.route('/keamanan/bendungan')
@login_required  # @petugas_only
@get_bendungan
def keamanan_bendungan(bend):
    date = request.values.get('sampling')
    date = datetime.datetime.strptime(date, "%Y-%m-%d") if date else datetime.datetime.utcnow()
    sampling = datetime.datetime.strptime(f"{date.year}-{date.month}-01", "%Y-%m-%d")

    now = datetime.datetime.now()
    if sampling.year == now.year and sampling.month == now.month:
        day = now.day
    else:
        day = calendar.monthrange(sampling.year, sampling.month)[1]
    end = datetime.datetime.strptime(f"{date.year}-{date.month}-{day} 23:59:59", "%Y-%m-%d %H:%M:%S")

    bendungan_id = bend.id
    arr = bend.nama.split('_')
    name = f"{arr[0].title()}.{arr[1].title()}"

    vnotch = ManualVnotch.query.filter(
                                        ManualVnotch.bendungan_id == bendungan_id,
                                        ManualVnotch.sampling.between(sampling, end)
                                    ).all()
    piezo = ManualPiezo.query.filter(
                                    ManualPiezo.bendungan_id == bendungan_id,
                                    ManualPiezo.sampling.between(sampling, end)
                                ).all()

    periodik = {}
    for i in range(day, 0, -1):
        sampl = datetime.datetime.strptime(f"{sampling.year}-{sampling.month}-{i}", "%Y-%m-%d")
        periodik[sampl] = {
            'vnotch': None,
            'piezo': None
        }
    for v in vnotch:
        periodik[v.sampling]['vnotch'] = v
    for p in piezo:
        periodik[p.sampling]['piezo'] = p

    return render_template('keamanan/bendungan.html',
                            name=name,
                            csrf=generate_csrf(),
                            bend_id=bend.id,
                            periodik=periodik,
                            sampling=datetime.datetime.today())


@bp.route('/keamanan/bendungan/vnotch', methods=['POST'])
@login_required  # @petugas_only
@get_bendungan
def keamanan_vnotch(bend):
    bendungan_id = bend.id
    form = AddVnotch()
    if form.validate_on_submit():
        try:
            vnotch = ManualVnotch(
                sampling=form.sampling.data,
                vn1_tma=form.vn1_tma.data,
                vn1_deb=form.vn1_deb.data,
                vn2_tma=form.vn2_tma.data,
                vn2_deb=form.vn2_deb.data,
                vn3_tma=form.vn3_tma.data,
                vn3_deb=form.vn3_deb.data,
                bendungan_id=bendungan_id
            )
            db.session.add(vnotch)
            db.session.commit()
            flash('Tambah Vnotch berhasil !', 'success')
            return redirect(url_for('admin.keamanan_bendungan'))
        except IntegrityError:
            db.session.rollback()
            flash('Data sudah ada, mohon update untuk mengubah', 'danger')

    return redirect(url_for('admin.keamanan_bendungan', bend_id=bend.id))


@bp.route('/keamanan/vnotch/update', methods=['POST'])  # @login_required
def keamanan_vnotch_update():
    pk = request.values.get('pk')
    attr = request.values.get('name')
    val = request.values.get('value')
    row = ManualVnotch.query.get(pk)
    setattr(row, attr, val)
    db.session.commit()

    result = {
        "name": attr,
        "pk": pk,
        "value": val
    }
    return jsonify(result)


@bp.route('/keamanan/bendungan/piezo', methods=['POST'])
@login_required  # @petugas_only
@get_bendungan
def keamanan_piezo(bend):
    bendungan_id = bend.id
    form = AddPiezo()
    if form.validate_on_submit():
        try:
            piezo = ManualPiezo(
                sampling=form.sampling.data,
                p1a=form.p1a.data,
                p1b=form.p1b.data,
                p1c=form.p1c.data,
                p2a=form.p2a.data,
                p2b=form.p2b.data,
                p2c=form.p2c.data,
                p3a=form.p3a.data,
                p3b=form.p3b.data,
                p3c=form.p3c.data,
                p4a=form.p4a.data,
                p4b=form.p4b.data,
                p4c=form.p4c.data,
                p5a=form.p5a.data,
                p5b=form.p5b.data,
                p5c=form.p5c.data,
                bendungan_id=bendungan_id
            )
            db.session.add(piezo)
            db.session.commit()
            flash('Tambah Piezo berhasil !', 'success')
            return redirect(url_for('admin.keamanan_bendungan'))
        except IntegrityError:
            db.session.rollback()
            flash('Data sudah ada, mohon update untuk mengubah', 'danger')

    return redirect(url_for('admin.keamanan_bendungan', bend_id=bend.id))


@bp.route('/keamanan/piezo/update', methods=['POST'])  # @login_required
def keamanan_piezo_update():
    pk = request.values.get('pk')
    attr = request.values.get('name')
    val = request.values.get('value')
    row = ManualPiezo.query.get(pk)
    setattr(row, attr, val)
    db.session.commit()

    result = {
        "name": attr,
        "pk": pk,
        "value": val
    }
    return jsonify(result)
