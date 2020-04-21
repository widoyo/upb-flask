from flask import request, render_template, redirect, url_for, jsonify, flash
from flask_login import login_required, current_user
from flask_wtf.csrf import generate_csrf
from sqlalchemy.exc import IntegrityError
from upb_app.models import Bendungan, Petugas
from upb_app.forms import AddPetugas
from upb_app import db, admin_only
import datetime

from upb_app.admin import bp


@bp.route('/bendungan/petugas')
@login_required
@admin_only
def petugas_bendungan():
    waduk = Bendungan.query.all()
    petugas = Petugas.query.all()

    data = {}
    for w in waduk:
        data[w.id] = {
            'nama': w.name,
            'petugas': []
        }
    for p in petugas:
        data[p.bendungan.id]['petugas'].append(p)

    return render_template('petugas/bendungan.html',
                            bendungan=waduk,
                            data=data,
                            csrf=generate_csrf(),
                            sampling=datetime.datetime.now())


@bp.route('/bendungan/petugas/add', methods=['POST'])
@login_required
@admin_only
def petugas_bendungan_add():
    form = AddPetugas()
    if form.validate_on_submit():
        try:
            obj_dict = {
                'nama': form.nama.data,
                'tugas': form.jabatan.data,
                'bendungan_id': int(form.bendungan.data),
                'tgl_lahir': form.tgl_lahir.data or None,
                'alamat': form.alamat.data or None,
                'kab': form.kab.data or None,
                'pendidikan': form.pendidikan.data or None
            }
            obj = Petugas(**obj_dict)
            db.session.add(obj)
            db.session.commit()
            flash(f"Petugas berhasil ditambahkan", 'success')
        except Exception as e:
            flash(f"Terjadi kesalahan saat mencoba menyimpan data", 'danger')

    return redirect(url_for('admin.petugas_bendungan'))


@bp.route('/bendungan/petugas/<petugas_id>/del', methods=['POST'])
@login_required
@admin_only
def petugas_bendungan_del(petugas_id):
    obj = Petugas.query.get(petugas_id)
    db.session.delete(obj)
    db.session.commit()

    flash(f"Data petugas berhasil dihapus", 'success')
    return redirect(url_for('admin.petugas_bendungan'))
