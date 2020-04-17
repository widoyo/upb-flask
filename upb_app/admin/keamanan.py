from flask import Blueprint, request, render_template, redirect, url_for, jsonify, flash
from flask_login import login_required, current_user
from flask_wtf.csrf import generate_csrf
from sqlalchemy import extract, and_
from psycopg2 import IntegrityError
from upb_app.models import ManualVnotch, ManualPiezo, Bendungan
from upb_app.forms import AddVnotch, AddPiezo
from upb_app import db, petugas_only, role_check
import datetime
import calendar

from upb_app.admin import bp
# bp = Blueprint('keamanan', __name__)


@bp.route('/keamanan')
@login_required
def keamanan():
    if current_user.role == "2":
        return redirect(url_for('admin.keamanan_bendungan', bendungan_id=current_user.bendungan_id))
    return redirect(url_for('admin.operasi_harian'))


@bp.route('/bendungan/keamanan/<bendungan_id>')
@login_required  # @petugas_only
@role_check
def keamanan_bendungan(bendungan_id):
    bend = Bendungan.query.get(bendungan_id)

    date = request.values.get('sampling')
    date = datetime.datetime.strptime(date, "%Y-%m-%d") if date else datetime.datetime.utcnow()
    sampling = datetime.datetime.strptime(f"{date.year}-{date.month}-01", "%Y-%m-%d") + datetime.timedelta(hours=8)

    now = datetime.datetime.now()
    if sampling.year == now.year and sampling.month == now.month:
        day = now.day
    else:
        day = calendar.monthrange(sampling.year, sampling.month)[1]
    end = datetime.datetime.strptime(f"{date.year}-{date.month}-{day} 23:59:59", "%Y-%m-%d %H:%M:%S")

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
                            name=bend.name,
                            csrf=generate_csrf(),
                            bend_id=bend.id,
                            periodik=periodik,
                            sampling=datetime.datetime.today())


@bp.route('/bendungan/keamanan/<bendungan_id>/vnotch', methods=['POST'])
@login_required  # @petugas_only
@role_check
def keamanan_vnotch(bendungan_id):
    form = AddVnotch()
    print(form.sampling.data)
    if form.validate_on_submit():
        try:
            obj_dict = {
                'sampling': form.sampling.data,
                'vn1_tma': form.vn1_tma.data,
                'vn1_deb': form.vn1_deb.data,
                'vn2_tma': form.vn2_tma.data,
                'vn2_deb': form.vn2_deb.data,
                'vn3_tma': form.vn3_tma.data,
                'vn3_deb': form.vn3_deb.data,
                'bendungan_id': bendungan_id
            }
            vn = ManualVnotch.query.filter(
                                        ManualVnotch.sampling == obj_dict['sampling'],
                                        ManualVnotch.bendungan_id == obj_dict['bendungan_id']
                                    ).first()
            if vn:
                for key, value in obj_dict.items():
                    setattr(vn, key, value)
            else:
                vnotch = ManualVnotch(**obj_dict)
                db.session.add(vnotch)
            db.session.commit()
            flash('Tambah Vnotch berhasil !', 'success')
        except Exception as e:
            db.session.rollback()
            print(f"VNotch Manual Error : {e.__class__.__name__}")
            flash(f"Terjadi kesalahan saat mencoba menyimpan data", 'danger')

    return redirect(url_for('admin.keamanan_bendungan', bendungan_id=bendungan_id))


@bp.route('/bendungan/keamanan/vnotch/update', methods=['POST'])  # @login_required
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


@bp.route('/bendungan/keamanan/<bendungan_id>/piezo', methods=['POST'])
@login_required  # @petugas_only
@role_check
def keamanan_piezo(bendungan_id):
    form = AddPiezo()
    if form.validate_on_submit():
        try:
            obj_dict = {
                'sampling': form.sampling.data,
                'p1a': form.p1a.data,
                'p1b': form.p1b.data,
                'p1c': form.p1c.data,
                'p2a': form.p2a.data,
                'p2b': form.p2b.data,
                'p2c': form.p2c.data,
                'p3a': form.p3a.data,
                'p3b': form.p3b.data,
                'p3c': form.p3c.data,
                'p4a': form.p4a.data,
                'p4b': form.p4b.data,
                'p4c': form.p4c.data,
                'p5a': form.p5a.data,
                'p5b': form.p5b.data,
                'p5c': form.p5c.data,
                'bendungan_id': bendungan_id
            }
            pie = ManualPiezo.query.filter(
                                        ManualPiezo.sampling == obj_dict['sampling'],
                                        ManualPiezo.bendungan_id == obj_dict['bendungan_id']
                                    ).first()
            if pie:
                for key, value in obj_dict.items():
                    setattr(pie, key, value)
            else:
                piezo = ManualPiezo(**obj_dict)
                db.session.add(piezo)
            db.session.commit()
            flash('Tambah Piezo berhasil !', 'success')
        except Exception as e:
            db.session.rollback()
            print(f"Piezo Manual Error : {e.__class__.__name__}")
            flash(f"Terjadi kesalahan saat mencoba menyimpan data", 'danger')

    return redirect(url_for('admin.keamanan_bendungan', bendungan_id=bendungan_id))


@bp.route('/bendungan/keamanan/piezo/update', methods=['POST'])  # @login_required
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
