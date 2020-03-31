from flask import Blueprint, request, render_template, redirect, url_for, jsonify, flash
from flask_login import login_required, current_user
from sqlalchemy import extract, and_
from sqlalchemy.exc import IntegrityError
from app.models import ManualVnotch, ManualPiezo, Bendungan
from app.forms import AddVnotch, AddPiezo
from app import db, petugas_only
import datetime

from app.admin import bp
# bp = Blueprint('keamanan', __name__)


@bp.route('/keamanan')
@login_required
def keamanan():
    if current_user.role == "2":
        return redirect(url_for('admin.keamanan_bendungan'))
    return redirect(url_for('admin.operasi_harian'))


@bp.route('/keamanan/bendungan')
@login_required
@petugas_only
def keamanan_bendungan():
    bendungan_id = current_user.bendungan_id
    date = request.values.get('sampling') or datetime.datetime.utcnow()
    sampling = datetime.datetime.strptime(f"{date.year}-{date.month}-01", "%Y-%m-%d")

    vnotch = ManualVnotch.query.filter(
                                        ManualVnotch.bendungan_id == bendungan_id,
                                        extract('month', ManualVnotch.sampling) == sampling.month,
                                        extract('year', ManualVnotch.sampling) == sampling.year
                                    ).all()
    piezo = ManualPiezo.query.filter(
                                    ManualPiezo.bendungan_id == bendungan_id,
                                    extract('month', ManualPiezo.sampling) == sampling.month,
                                    extract('year', ManualPiezo.sampling) == sampling.year
                                ).all()
    bend = Bendungan.query.get(bendungan_id)
    periodik = {}
    for v in vnotch:
        periodik[v.sampling] = {
            'vnotch': v,
            'piezo': None
        }
    for p in piezo:
        periodik[p.sampling]['piezo'] = p

    return render_template('keamanan/bendungan.html',
                            bend=bend,
                            periodik=periodik,
                            sampling=sampling)


@bp.route('/keamanan/bendungan/vnotch', methods=['GET', 'POST'])
@login_required
@petugas_only
def keamanan_vnotch():
    bendungan_id = current_user.bendungan_id
    form = AddVnotch()
    if form.validate_on_submit():
        try:
            vnotch = ManualVnotch(
                sampling=form.values.get('sampling'),
                vn1_tma=form.values.get('vn1_tma'),
                vn1_deb=form.values.get('vn1_deb'),
                vn2_tma=form.values.get('vn2_tma'),
                vn2_deb=form.values.get('vn2_deb'),
                vn3_tma=form.values.get('vn3_tma'),
                vn3_deb=form.values.get('vn3_deb'),
                bendungan_id=bendungan_id
            )
            db.session.add(vnotch)
            db.session.commit()
            flash('Tambah Vnotch berhasil !', 'success')
            return redirect(url_for('admin.keamanan_bendungan'))
        except IntegrityError:
            db.session.rollback()
            flash('Data sudah ada, mohon update untuk mengubah', 'danger')

    return render_template('keamanan/vnotch_add.html',
                            form=form)


@bp.route('/keamanan/vnotch/update', methods=['POST'])
@login_required
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


@bp.route('/keamanan/bendungan/piezo', methods=['GET', 'POST'])
@login_required
@petugas_only
def keamanan_piezo():
    bendungan_id = current_user.bendungan_id
    form = AddPiezo()
    if form.validate_on_submit():
        try:
            piezo = ManualPiezo(
                sampling=form.values.get('sampling'),
                p1a=form.values.get('p1a'),
                p1b=form.values.get('p1b'),
                p1c=form.values.get('p1c'),
                p2a=form.values.get('p2a'),
                p2b=form.values.get('p2b'),
                p2c=form.values.get('p2c'),
                p3a=form.values.get('p3a'),
                p3b=form.values.get('p3b'),
                p3c=form.values.get('p3c'),
                p4a=form.values.get('p4a'),
                p4b=form.values.get('p4b'),
                p4c=form.values.get('p4c'),
                p5a=form.values.get('p5a'),
                p5b=form.values.get('p5b'),
                p5c=form.values.get('p5c'),
                bendungan_id=bendungan_id
            )
            db.session.add(piezo)
            db.session.commit()
            flash('Tambah Piezo berhasil !', 'success')
            return redirect(url_for('admin.keamanan_bendungan'))
        except IntegrityError:
            db.session.rollback()
            flash('Data sudah ada, mohon update untuk mengubah', 'danger')

    return render_template('keamanan/piezo_add.html',
                            form=form)


@bp.route('/keamanan/piezo/update', methods=['POST'])
@login_required
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
