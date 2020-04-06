from flask import Blueprint, request, render_template, redirect, url_for, jsonify, flash
from flask_login import login_required, current_user
from sqlalchemy import extract
from sqlalchemy.exc import IntegrityError
from upb_app.models import Kegiatan, Foto, Bendungan
from upb_app.forms import AddKegiatan
from upb_app import app, db, petugas_only, get_bendungan
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
        return redirect(url_for('admin.kegiatan_bendungan'))
    bends = Bendungan.query.all()
    return render_template('kegiatan/index.html',
                            bends=bends)


@bp.route('/kegiatan/bendungan')
@login_required
@get_bendungan
def kegiatan_bendungan(bend):
    date = request.values.get('sampling')
    date = datetime.datetime.strptime(date, "%Y-%m-%d") if date else datetime.datetime.utcnow()
    sampling = datetime.datetime.strptime(f"{date.year}-{date.month}-01", "%Y-%m-%d")

    bendungan_id = bend.id
    arr = bend.nama.split('_')
    name = f"{arr[0].title()}.{arr[1].title()}"

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
                            bend_id=bend.id,
                            name=name,
                            petugas=petugas,
                            kegiatan=kegiatan,
                            sampling=datetime.datetime.today())


@bp.route('/kegiatan/<bendungan_id>/paper')
@login_required
def kegiatan_paper(bendungan_id):
    date = request.values.get('sampling') or datetime.datetime.utcnow()
    sampling = datetime.datetime.strptime(f"{date.year}-{date.month}-{date.day}", "%Y-%m-%d")
    bend = Bendungan.query.get(bendungan_id)

    kegiatan = Kegiatan.query.filter(
                                    Kegiatan.bendungan_id == bendungan_id,
                                    extract('month', Kegiatan.sampling) == sampling.month,
                                    extract('year', Kegiatan.sampling) == sampling.year
                                ).all()

    return render_template('kegiatan/bendungan.html',
                            bend=bend,
                            kegiatan=kegiatan,
                            sampling=sampling)


@bp.route('/kegiatan/bendungan/add', methods=['GET', 'POST'])
@login_required
@petugas_only
def kegiatan_add():
    bendungan_id = current_user.bendungan_id
    form = AddKegiatan()
    bend = Bendungan.query.get(bendungan_id)
    if form.validate_on_submit():
        last_foto = Foto.query.order_by(Foto.id.desc()).first()
        new_id = 1 if not last_foto else (last_foto.id + 1)
        try:
            raw = request.foto.data
            imageStr = base64.b64encode(raw).decode('ascii')
            filename = f"kegiatan_{new_id}_{request.foto.data.filename}"
            foto = save_image(imageStr, filename)
            foto.keterangan = form.values.get("uraian")

            kegiatan = Kegiatan(
                sampling=form.values.get("sampling"),
                petugas=form.values.get("petugas"),
                uraian=form.values.get("uraian"),
                bendungan_id=bendungan_id
            )
            db.session.add(kegiatan)
            db.session.add(foto)
            db.session.commit()

            foto.obj_id = kegiatan.id
            kegiatan.foto_id = foto.id
            db.session.commit()

            flash('Tambah Kegiatan berhasil !', 'success')
            return redirect(url_for('admin.kegiatan_bendungan'))
        except IntegrityError:
            db.session.rollback()
            flash('Data sudah ada, mohon update untuk mengubah', 'danger')

    return render_template('kegiatan/add.html',
                            form=form,
                            bend=bend)


@bp.route('/kegiatan/update', methods=['POST'])  # @login_required
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

    # convert base64 into image file and then save it
    imgdata = base64.b64decode(imageStr)
    # print(imgdata)
    with open(img_file, 'wb') as f:
        f.write(imgdata)

    print("saving image !")
    foto = Foto(
        url=img_file,
        obj_type="kegiatan"
    )
    return foto
