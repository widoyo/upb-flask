from flask import Blueprint, request, render_template, redirect, url_for, jsonify, flash
from flask_login import login_required, current_user
from flask_wtf.csrf import generate_csrf
from sqlalchemy import extract
from sqlalchemy.exc import IntegrityError
from upb_app.helper import month_range, week_range
from upb_app.models import Kegiatan, Foto, Bendungan, Petugas, Pemeliharaan, jenis_pemeliharaan
from upb_app.forms import AddKegiatan, RencanaPemeliharaan, LaporPemeliharaan
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

    sampling, end, day = month_range(request.values.get('sampling'))
    all_kegiatan = Kegiatan.query.filter(
                                    Kegiatan.bendungan_id == bendungan_id,
                                    extract('month', Kegiatan.sampling) == sampling.month,
                                    extract('year', Kegiatan.sampling) == sampling.year
                                ).all()
    kegiatan = {}
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
                            sampling=datetime.datetime.now() + datetime.timedelta(hours=7),
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
        except Exception as e:
            db.session.rollback()
            print(e)
            flash(f"Terjadi Error saat menyimpan data Kegiatan : {e}", 'danger')

    return redirect(url_for('admin.kegiatan_bendungan', bendungan_id=bend.id))


@bp.route('/bendungan/pemeliharaan/<bendungan_id>')
@login_required
@role_check
def pemeliharaan(bendungan_id):
    bend = Bendungan.query.get(bendungan_id)
    sampling, start, end = week_range(request.values.get('sampling'))
    petugas = Petugas.query.filter(Petugas.bendungan_id == bend.id).all()

    pemeliharaan = Pemeliharaan.query.filter(
                                        Pemeliharaan.sampling >= start,
                                        Pemeliharaan.sampling <= sampling,
                                        Pemeliharaan.bendungan_id == bendungan_id
                                    ).order_by(Pemeliharaan.sampling).all()
    data = {}
    rencana = {}
    laporan = []
    for i in range(int(sampling.strftime('%w'))):
        sampl = sampling - datetime.timedelta(days=i)
        data[sampl] = []
    for pem in pemeliharaan:
        if pem.is_rencana == '1':
            rencana[pem.jenis] = {
                'rencana': pem,
                'progress': 0
            }
        else:
            laporan.append(pem)
    for l in laporan:
        rencana[l.jenis]['progress'] += round(l.nilai/rencana[l.jenis]['rencana'].nilai, 4)
        lap_pet = l.get_petugas()
        data[l.sampling].append({
            'laporan': l,
            'petugas': lap_pet,
            'length': max(1, len(lap_pet)),
            'rencana': rencana[l.jenis]['rencana'],
            'progress': rencana[l.jenis]['progress']
        })
    # data = sorted(data, reverse=True)

    return render_template('kegiatan/pemeliharaan.html',
                            bend=bend,
                            data=data,
                            csrf=generate_csrf(),
                            sampling=sampling,
                            petugas=petugas,
                            jenis=jenis_pemeliharaan,
                            jenis_ren=[j for j, ren in rencana.items()])


@bp.route('/bendungan/pemeliharaan/<bendungan_id>/rencana', methods=['POST'])
@login_required
@role_check
def pemeliharaan_rencana(bendungan_id):
    form = RencanaPemeliharaan()

    if form.validate_on_submit():
        obj_dict = {
            'sampling': form.sampling.data,
            'is_rencana': '1',
            'jenis': form.jenis.data,
            'komponen': form.komponen.data,
            'nilai': form.target.data,
            'bendungan_id': bendungan_id
        }
        obj = Pemeliharaan(**obj_dict)
        db.session.add(obj)
        try:
            db.session.commit()
            flash('Rencana Pemeliharaan berhasil ditambahkan !', 'success')
        except IntegrityError:
            db.session.rollback()
            flash(f"Rencana Pemeliharaan sudah dibuat", 'danger')

    return redirect(url_for('admin.pemeliharaan', bendungan_id=bendungan_id))


@bp.route('/bendungan/pemeliharaan/<bendungan_id>/lapor', methods=['POST'])
@login_required
@role_check
def pemeliharaan_lapor(bendungan_id):
    form = LaporPemeliharaan()

    if form.validate_on_submit():
        obj_dict = {
            'sampling': form.sampling.data,
            'is_rencana': '0',
            'jenis': form.jenis.data,
            'nilai': form.progress.data,
            'keterangan': form.keterangan.data,
            'bendungan_id': bendungan_id
        }
        obj = Pemeliharaan(**obj_dict)
        db.session.add(obj)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash(f"Rencana Pemeliharaan sudah dibuat", 'danger')
            return redirect(url_for('admin.pemeliharaan', bendungan_id=bendungan_id))

        # set association table for pemeliharaan-petugas
        petugas = [int(id) for id in form.petugas.data]
        obj.set_petugas(petugas)
        flash('Rencana Pemeliharaan berhasil ditambahkan !', 'success')

    return redirect(url_for('admin.pemeliharaan', bendungan_id=bendungan_id))


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


@bp.route('/bendungan/kegiatan/<bendungan_id>/delete', methods=['POST'])
@login_required
@petugas_only
def kegiatan_delete(bendungan_id):
    keg_id = int(request.values.get('keg_id'))
    foto_id = int(request.values.get('foto_id'))
    filename = request.values.get('filename')
    filepath = os.path.join(app.config['SAVE_DIR'], filename)

    kegiatan = Kegiatan.query.get(keg_id)
    foto = Foto.query.get(foto_id)

    db.session.delete(kegiatan)
    db.session.delete(foto)
    db.session.commit()

    if os.path.exists(filepath):
        os.remove(filepath)

    return "ok"


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
