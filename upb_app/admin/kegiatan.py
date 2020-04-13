from flask import Blueprint, request, render_template, redirect, url_for, jsonify, flash
from flask_login import login_required, current_user
from flask_wtf.csrf import generate_csrf
from sqlalchemy import extract
from sqlalchemy.exc import IntegrityError
from upb_app.models import Kegiatan, Foto, Bendungan
from upb_app.forms import AddKegiatan
from upb_app import app, db, petugas_only, role_check
import datetime
import calendar
import base64
import os

from upb_app.admin import bp
# bp = Blueprint('kegiatan', __name__)

petugas = [
    "Tidak Ada",
    "Koordinator",
    "Keamanan",
    "Pemantauan",
    "Operasi",
    "Pemeliharaan"
]


@bp.route('/kegiatan')
@login_required
def kegiatan():
    if current_user.role == "2":
        return redirect(url_for('admin.kegiatan_bendungan', bendungan_id=current_user.bendungan_id))
    bends = Bendungan.query.all()
    return render_template('kegiatan/index.html',
                            bends=bends)


@bp.route('/bendungan/kegiatan/<bendungan_id>')
@login_required
@role_check
def kegiatan_bendungan(bendungan_id):
    bend = Bendungan.query.get(bendungan_id)

    date = request.values.get('sampling')
    date = datetime.datetime.strptime(date, "%Y-%m-%d") if date else datetime.datetime.utcnow()
    sampling = datetime.datetime.strptime(f"{date.year}-{date.month}-01", "%Y-%m-%d")

    all_kegiatan = Kegiatan.query.filter(
                                    Kegiatan.bendungan_id == bendungan_id,
                                    extract('month', Kegiatan.sampling) == sampling.month,
                                    extract('year', Kegiatan.sampling) == sampling.year
                                ).all()
    kegiatan = {}
    now = datetime.datetime.now()
    if sampling.year == now.year and sampling.month == now.month:
        day = now.day
    else:
        day = calendar.monthrange(sampling.year, sampling.month)[1]
    for i in range(day, 0, -1):
        sampl = datetime.datetime.strptime(f"{sampling.year}-{sampling.month}-{i}", "%Y-%m-%d")
        kegiatan[sampl] = {
            'id': 0,
            'koordinator': [],
            'keamanan': [],
            'pemantauan': [],
            'operasi': [],
            'pemeliharaan': []
        }

    for keg in all_kegiatan:
        if keg.sampling not in kegiatan:
            kegiatan[keg.sampling] = {
                'id': 0,
                'koordinator': [],
                'keamanan': [],
                'pemantauan': [],
                'operasi': [],
                'pemeliharaan': []
            }
        kegiatan[keg.sampling]['id'] = keg.id
        kegiatan[keg.sampling][keg.petugas.lower()].append(keg.uraian)

    return render_template('kegiatan/bendungan.html',
                            csrf=generate_csrf(),
                            bend_id=bend.id,
                            name=bend.name,
                            petugas=petugas,
                            kegiatan=kegiatan,
                            sampling=datetime.datetime.today(),
                            sampling_dt=sampling)


@bp.route('/bendungan/kegiatan/<bendungan_id>/paper')
@login_required
@role_check
def kegiatan_paper(bendungan_id):
    bend = Bendungan.query.get(bendungan_id)

    date = request.values.get('sampling')
    sampling = datetime.datetime.strptime(date, "%Y-%m-%d") if date else datetime.datetime.utcnow()

    bendungan_id = bend.id

    kegiatan = Kegiatan.query.filter(
                                    Kegiatan.bendungan_id == bendungan_id,
                                    extract('day', Kegiatan.sampling) == sampling.day,
                                    extract('month', Kegiatan.sampling) == sampling.month,
                                    extract('year', Kegiatan.sampling) == sampling.year
                                ).all()
    data = []
    for keg in kegiatan:
        data.append({
            'kegiatan': keg,
            'foto': Foto.query.get(keg.foto_id)
        })

    return render_template('kegiatan/paper.html',
                            bend=bend,
                            kegiatan=data,
                            sampling=sampling)


@bp.route('/bendungan/kegiatan/<bendungan_id>/add', methods=['POST'])
@login_required
@role_check
def kegiatan_add(bendungan_id):
    bend = Bendungan.query.get(bendungan_id)

    form = AddKegiatan()
    if form.validate_on_submit():
        last_foto = Foto.query.order_by(Foto.id.desc()).first()
        new_id = 1 if not last_foto else (last_foto.id + 1)
        print(new_id)
        try:
            raw = form.foto.data
            # imageStr = base64.b64encode(raw).decode('ascii')
            imageStr = raw.split(',')[1]
            filename = f"kegiatan_{new_id}_{form.filename.data}"
            foto = save_image(imageStr, filename)
            foto.keterangan = form.keterangan.data

            kegiatan = Kegiatan(
                sampling=form.sampling.data,
                petugas=form.petugas.data,
                uraian=form.keterangan.data,
                bendungan_id=bendungan_id
            )
            print("saving kegiatan")
            db.session.add(kegiatan)
            db.session.add(foto)
            db.session.commit()

            foto.obj_id = kegiatan.id
            kegiatan.foto_id = foto.id
            db.session.commit()

            flash('Tambah Kegiatan berhasil !', 'success')
            return redirect(url_for('admin.kegiatan_bendungan', bendungan_id=bend.id))
        except Exception as e:
            db.session.rollback()
            print(e)
            flash(f"Terjadi Error saat menyimpan data Kegiatan", 'danger')

    return redirect(url_for('admin.kegiatan_bendungan', bendungan_id=bend.id))


@bp.route('/bendungan/kegiatan/update', methods=['POST'])  # @login_required
def kegiatan_update():
    pk = request.values.get('pk')
    attr = request.values.get('name')
    val = request.values.get('value')
    row = Kegiatan.query.get(pk)
    setattr(row, attr, val)
    db.session.commit()

    result = {
        "name": attr,
        "pk": pk,
        "value": val
    }
    return jsonify(result)


def save_image(imageStr, filename):
    # print(file_name)
    img_file = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    save_file = os.path.join(app.config['SAVE_DIR'], img_file)

    # convert base64 into image file and then save it
    imgdata = base64.b64decode(imageStr)
    # print(imgdata)
    with open(save_file, 'wb') as f:
        f.write(imgdata)

    print("saving image !")
    foto = Foto(
        url=img_file,
        obj_type="kegiatan"
    )
    return foto
