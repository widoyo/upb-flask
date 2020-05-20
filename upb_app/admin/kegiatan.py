from flask import Blueprint, request, render_template, redirect, url_for, jsonify, flash, Response
from flask_login import login_required, current_user
from flask_wtf.csrf import generate_csrf
from sqlalchemy import extract, and_
from sqlalchemy.exc import IntegrityError
from upb_app.helper import month_range, week_range
from upb_app.models import Kegiatan, Foto, Bendungan, Embung, Petugas, Pemeliharaan, jenis_pemeliharaan
from upb_app.models import KegiatanEmbung
from upb_app.forms import AddKegiatan, RencanaPemeliharaan, LaporPemeliharaan, RencanaEmbung, PencapaianEmbung
from upb_app import app, db, admin_only, petugas_only, role_check, role_check_embung
import datetime
import calendar
import base64
import csv
import os
import io

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


@bp.route('/bendungan/kegiatan')
@login_required
@admin_only
def kegiatan():
    if current_user.role == "2":
        return redirect(url_for('admin.kegiatan_bendungan', bendungan_id=current_user.bendungan_id))
    if current_user.role == "3":
        return redirect(url_for('admin.kegiatan_embung', embung_id=current_user.embung_id))
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


@bp.route('/bendungan/<bendungan_id>/pemeliharaan')
@login_required
@role_check
def pemeliharaan(bendungan_id):
    bend = Bendungan.query.get(bendungan_id)
    sampling, start, end = week_range(request.values.get('sampling'))
    petugas = Petugas.query.filter(Petugas.bendungan_id == bend.id).all()
    is_laporan = False

    pemeliharaan = Pemeliharaan.query.filter(
                                        Pemeliharaan.sampling >= start,
                                        Pemeliharaan.sampling <= end,
                                        Pemeliharaan.bendungan_id == bendungan_id
                                    ).order_by(Pemeliharaan.sampling, Pemeliharaan.id).all()
    data = {}
    rencana = {}
    laporan = []
    for i in range(int(end.strftime('%w'))):
        sampl = end - datetime.timedelta(days=i)
        data[sampl] = []
    for pem in pemeliharaan:
        if pem.is_rencana == '1':
            rencana[pem.jenis] = {
                'rencana': pem,
                'progress': 0
            }
        else:
            laporan.append(pem)
            is_laporan = True
    for l in laporan:
        rencana[l.jenis]['progress'] += round(l.nilai/rencana[l.jenis]['rencana'].nilai, 4)
        lap_pet = l.get_petugas()
        data[l.sampling].append({
            'laporan': l,
            'petugas': lap_pet,
            'length': max(1, len(lap_pet)),
            'rencana': rencana[l.jenis]['rencana'],
            'progress': round(rencana[l.jenis]['progress'] * 100, 2)
        })
    # data = sorted(data, reverse=True)

    return render_template('kegiatan/pemeliharaan.html',
                            bend=bend,
                            data=data,
                            rencana=rencana,
                            csrf=generate_csrf(),
                            sampling=sampling,
                            next=start + datetime.timedelta(days=7),
                            prev=start - datetime.timedelta(days=7),
                            petugas=petugas,
                            is_laporan=is_laporan,
                            jenis=jenis_pemeliharaan,
                            jenis_ren=[j for j, ren in rencana.items()])


@bp.route('/bendungan/<bendungan_id>/pemeliharaan/rencana', methods=['POST'])
@login_required
@role_check
def pemeliharaan_rencana(bendungan_id):
    form = RencanaPemeliharaan()

    if form.validate_on_submit():
        row = Pemeliharaan.query.filter(
                                    Pemeliharaan.sampling == form.sampling.data,
                                    Pemeliharaan.is_rencana == '1',
                                    Pemeliharaan.bendungan_id == bendungan_id,
                                    Pemeliharaan.jenis == form.jenis.data
                                ).first()
        obj_dict = {
            'sampling': form.sampling.data,
            'is_rencana': '1',
            'jenis': form.jenis.data,
            'komponen': form.komponen.data,
            'nilai': form.target.data,
            'bendungan_id': bendungan_id
        }
        if row:
            for key, value in obj_dict.items():
                setattr(row, key, value)
        else:
            obj = Pemeliharaan(**obj_dict)
            db.session.add(obj)

        try:
            db.session.commit()
            flash('Rencana Pemeliharaan berhasil ditambahkan !', 'success')
        except Exception:
            db.session.rollback()
            flash(f"Terjadi Error", 'danger')

    return redirect(url_for('admin.pemeliharaan', bendungan_id=bendungan_id, rencana='on'))


@bp.route('/bendungan/<bendungan_id>/pemeliharaan/lapor', methods=['POST'])
@login_required
@role_check
def pemeliharaan_lapor(bendungan_id):
    row = Pemeliharaan.query.filter(
                                Pemeliharaan.sampling == request.form.get('sampling'),
                                Pemeliharaan.is_rencana == '0',
                                Pemeliharaan.bendungan_id == bendungan_id,
                                Pemeliharaan.jenis == request.form.get('jenis')
                            ).first()
    obj = None
    obj_dict = {
        'sampling': request.form.get('sampling'),
        'is_rencana': '0',
        'jenis': request.form.get('jenis'),
        'nilai': float(request.form.get('progress')),
        'keterangan': request.form.get('keterangan'),
        'bendungan_id': bendungan_id
    }
    petugas = [int(id) for id in request.form.get('petugas').split(',')]
    if row:
        for key, value in obj_dict.items():
            setattr(row, key, value)
        row.set_petugas(petugas)
    else:
        obj = Pemeliharaan(**obj_dict)
        db.session.add(obj)

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        flash(f"Terjadi Error", 'danger')
        return "error"

    # set association table for pemeliharaan-petugas
    if obj:
        obj.set_petugas(petugas)
    flash('Rencana Pemeliharaan berhasil ditambahkan !', 'success')

    # add foto
    new_id = obj.id if obj else row.id
    latest = Foto.query.order_by(Foto.id.desc()).first()
    raw = request.form.get('foto')
    imageStr = raw.split(',')[1]
    filename = f"pemeliharaan_{latest.id}_{request.form.get('filename')}"
    img_file = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    save_file = os.path.join(app.config['SAVE_DIR'], img_file)

    # convert base64 into image file and then save it
    imgdata = base64.b64decode(imageStr)
    with open(save_file, 'wb') as f:
        f.write(imgdata)

    foto = Foto(
        url=img_file,
        obj_type="pemeliharaan",
        obj_id=new_id
    )
    foto.keterangan = request.form.get('keterangan_foto')
    db.session.add(foto)
    db.session.commit()

    return "success"


@bp.route('/bendungan/<bendungan_id>/pemeliharaan/<pem_id>/petugas', methods=['POST'])
@login_required
@role_check
def pemeliharaan_petugas(bendungan_id, pem_id):
    pem = Pemeliharaan.query.get(pem_id)

    petugas = [int(p) for p in request.form.getlist(f"petugas_add")]
    pem.set_petugas(petugas)

    return redirect(url_for('admin.pemeliharaan', bendungan_id=bendungan_id))


@bp.route('/bendungan/<bendungan_id>/pemeliharaan/<pem_id>/foto', methods=['POST'])
@login_required
@role_check
def pemeliharaan_foto(bendungan_id, pem_id):

    latest = Foto.query.order_by(Foto.id.desc()).first()
    raw = request.form.get('foto')
    imageStr = raw.split(',')[1]
    filename = f"pemeliharaan_{latest.id}_{request.form.get('filename')}"
    img_file = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    save_file = os.path.join(app.config['SAVE_DIR'], img_file)

    print(imageStr)
    print(filename)
    print(request.form.get(f"keterangan"))

    try:
        # convert base64 into image file and then save it
        imgdata = base64.b64decode(imageStr)
        with open(save_file, 'wb') as f:
            f.write(imgdata)

        foto = Foto(
            url=img_file,
            obj_type="pemeliharaan",
            obj_id=pem_id
        )
        foto.keterangan = request.form.get(f"keterangan")
        db.session.add(foto)
        db.session.commit()

        return "success"
    except Exception:
        return "error"


@bp.route('/bendungan/pemeliharaan/update', methods=['POST'])  # @login_required
def pemeliharaan_update():
    pk = request.values.get('pk')
    attr = request.values.get('name')
    val = request.values.get('value')
    row = Pemeliharaan.query.get(pk)
    setattr(row, attr, val)
    db.session.commit()

    result = {
        "name": attr,
        "pk": pk,
        "value": val
    }
    return jsonify(result)


@bp.route('/bendungan/<bendungan_id>/pemeliharaan/delete', methods=['POST'])
@login_required
@role_check
def pemeliharaan_delete(bendungan_id):
    pem_id = int(request.values.get('pem_id'))

    pemeliharaan = Pemeliharaan.query.get(pem_id)
    pem_list = [pemeliharaan]

    if pemeliharaan.is_rencana == '1':
        sampling, start, end = week_range(pemeliharaan.sampling.strftime("%Y-%m-%d"))
        laporan = Pemeliharaan.query.filter(
                            Pemeliharaan.sampling >= start,
                            Pemeliharaan.sampling <= end,
                            Pemeliharaan.jenis == pemeliharaan.jenis,
                            Pemeliharaan.is_rencana == '0',
                            Pemeliharaan.bendungan_id == bendungan_id
                        ).all()
        pem_list += laporan
    print(pem_list)

    for pem in pem_list:
        fotos = pem.fotos

        for f in fotos:
            filepath = os.path.join(app.config['SAVE_DIR'], f.url)

            db.session.delete(f)
            if os.path.exists(filepath):
                os.remove(filepath)
        for ass in pem.pemeliharaan_petugas:
            db.session.delete(ass)
        db.session.delete(pem)

    db.session.commit()

    return "ok"


@bp.route('/bendungan/<bendungan_id>/pemeliharaan/delete/foto', methods=['POST'])
@login_required
@role_check
def pemeliharaan_delete_foto(bendungan_id):
    foto_id = int(request.values.get('foto_id'))
    print(f"ID Foto : {foto_id}")

    foto = Foto.query.get(foto_id)
    filepath = os.path.join(app.config['SAVE_DIR'], foto.url)

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


@bp.route('/embung/kegiatan')
@login_required
@admin_only
def kegiatan_index_embung():
    embung = Embung.query.filter(Embung.is_verified == '1').order_by(Embung.id).all()

    embung_a = []
    embung_b = []
    for e in embung:
        if e.jenis == 'a':
            embung_a.append(e)
        elif e.jenis == 'b':
            embung_b.append(e)
    return render_template('kegiatan/embung/index.html',
                            embung_a=embung_a,
                            embung_b=embung_b)


@bp.route('/embung/<embung_id>/kegiatan')
@login_required
@role_check_embung
def kegiatan_embung(embung_id):
    embung = Embung.query.get(embung_id)

    sampling, end, day = month_range(request.values.get('sampling'))
    all_kegiatan = KegiatanEmbung.query.filter(
                                    KegiatanEmbung.embung_id == embung_id,
                                    extract('month', KegiatanEmbung.sampling) == sampling.month,
                                    extract('year', KegiatanEmbung.sampling) == sampling.year
                                ).all()
    kegiatan = {}
    for i in range(day, 0, -1):
        sampl = datetime.datetime.strptime(f"{sampling.year}-{sampling.month}-{i}", "%Y-%m-%d")
        kegiatan[sampl] = []

    for keg in all_kegiatan:
        kegiatan[keg.sampling].append(keg)

    return render_template('kegiatan/embung/embung.html',
                            csrf=generate_csrf(),
                            emb_id=embung.id,
                            name=embung.nama,
                            bagian=embung.bagian,
                            kegiatan=kegiatan,
                            sampling=datetime.datetime.now() + datetime.timedelta(hours=7),
                            sampling_dt=sampling)


@bp.route('/embung/<embung_id>/kegiatan/add', methods=['POST'])
@login_required
@role_check_embung
def kegiatan_embung_add(embung_id):
    form = RencanaEmbung()

    if form.validate_on_submit():
        bagian_id = int(form.bagian.data or 0)
        bagian_id = None if bagian_id == 0 else bagian_id
        obj_dict = {
            'sampling': form.sampling.data,
            'lokasi': form.lokasi.data,
            'rencana': f"{form.kegiatan.data} seluas {form.luas.data}m2",
            'embung_id': embung_id
        }
        if form.bagian.data:
            obj_dict['bagian_id'] = int(form.bagian.data)
        print(obj_dict)

        row = KegiatanEmbung.query.filter(
                                        KegiatanEmbung.sampling == form.sampling.data,
                                        KegiatanEmbung.embung_id == embung_id,
                                        KegiatanEmbung.bagian_id == bagian_id
                                    ).first()
        if row:
            for key, value in obj_dict.items():
                setattr(row, key, value)
        else:
            nrow = KegiatanEmbung(**obj_dict)
            db.session.add(nrow)
        db.session.commit()

    return redirect(url_for('admin.kegiatan_embung', embung_id=embung_id))


@bp.route('/embung/<embung_id>/kegiatan/update', methods=['POST'])
@login_required
@role_check_embung
def kegiatan_embung_update(embung_id):
    form = PencapaianEmbung()

    if form.validate_on_submit():
        print("Validated")
        bagian_id = int(form.bagian.data or 0)
        bagian_id = None if bagian_id == 0 else bagian_id
        print(bagian_id)
        row = KegiatanEmbung.query.filter(
                                        KegiatanEmbung.sampling == form.sampling.data,
                                        KegiatanEmbung.embung_id == embung_id,
                                        KegiatanEmbung.bagian_id == bagian_id
                                    ).first()
        if not row:
            return "not ok"

        obj_dict = {
            'mulai': form.mulai.data,
            'selesai': form.selesai.data,
            'pencapaian': form.pencapaian.data,
            'kendala': form.kendala.data,
        }
        if form.bagian.data:
            obj_dict['bagian_id'] = int(form.bagian.data)
        print(obj_dict)

        for key, value in obj_dict.items():
            setattr(row, key, value)
        fotos = [
            {
                'filename': form.filename_0.data,
                'file': form.foto_0.data,
                'keterangan': "0%"
            },
            {
                'filename': form.filename_50.data,
                'file': form.foto_50.data,
                'keterangan': "50%"
            },
            {
                'filename': form.filename_100.data,
                'file': form.foto_100.data,
                'keterangan': "100%"
            }
        ]

        last_foto = Foto.query.order_by(Foto.id.desc()).first()
        new_id = 1 if not last_foto else (last_foto.id + 1)
        for foto in fotos:
            raw = foto['file']
            imageStr = raw.split(',')[1]
            filename = f"kegiatan_embung_{new_id}_{foto['filename']}"
            new_id += 1

            img_file = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            save_file = os.path.join(app.config['SAVE_DIR'], img_file)

            # convert base64 into image file and then save it
            imgdata = base64.b64decode(imageStr)
            with open(save_file, 'wb') as f:
                f.write(imgdata)

            foto = Foto(
                keterangan=foto['keterangan'],
                url=img_file,
                obj_type="kegiatan_embung",
                obj_id=row.id
            )
            db.session.add(foto)
        db.session.commit()

    return "ok"


@bp.route('/embung/<embung_id>/kegiatan/delete', methods=['POST'])
@login_required
@role_check_embung
def kegiatan_embung_delete(embung_id):
    keg_id = int(request.values.get('keg_id'))

    kegiatan = KegiatanEmbung.query.get(keg_id)

    fotos = kegiatan.fotos

    for f in fotos:
        filepath = os.path.join(app.config['SAVE_DIR'], f.url)

        db.session.delete(f)
        if os.path.exists(filepath):
            os.remove(filepath)
    db.session.delete(kegiatan)
    db.session.commit()

    return "ok"


@bp.route('/embung/<embung_id>/kegiatan/csv', methods=['GET'])
@login_required
@role_check_embung
def kegiatan_embung_csv(embung_id):
    embung = Embung.query.get(embung_id)

    sampling, end, day = month_range(request.values.get('sampling'))
    all_kegiatan = KegiatanEmbung.query.filter(
                                    KegiatanEmbung.embung_id == embung_id,
                                    extract('month', KegiatanEmbung.sampling) == sampling.month,
                                    extract('year', KegiatanEmbung.sampling) == sampling.year
                                ).all()
    kegiatan = {}
    for i in range(day, 0, -1):
        sampl = datetime.datetime.strptime(f"{sampling.year}-{sampling.month}-{i}", "%Y-%m-%d")
        kegiatan[sampl] = None

    for keg in all_kegiatan:
        kegiatan[keg.sampling] = keg

    pre_csv = []
    pre_csv.append(['URAIAN KEGIATAN PETUGAS OP EMBUNG'])
    pre_csv.append(['NAMA EMBUNG', embung.nama])
    pre_csv.append(['LOKASI EMBUNG', f"{embung.desa} Kec. {embung.kec} Kab. {embung.kab}"])
    pre_csv.append(['Bulan', sampling.strftime("%B")])
    pre_csv.append([
        'tanggal', 'lokasi kegiatan', 'rencana kegiatan', 'pencapaian', 'jam mulai',
        'jam selesai', 'kendala', '0%', '50%', '100%'
    ])
    for date, keg in kegiatan.items():
        if keg:
            pre_csv.append([
                date.strftime("%d %B %Y"), keg.lokasi,
                keg.rencana, keg.pencapaian, keg.mulai, keg.selesai, keg.kendala,
                f"{request.url_root}{keg.fotos[0].url}",
                f"{request.url_root}{keg.fotos[1].url}",
                f"{request.url_root}{keg.fotos[2].url}"
            ])
        else:
            pre_csv.append([date.strftime("%d %B %Y"), None, None, None, None, None, None, None, None, None])
    output = io.StringIO()
    writer = csv.writer(output, delimiter='\t')
    for l in pre_csv:
        writer.writerow(l)
    output.seek(0)

    return Response(output,
                    mimetype="text/csv",
                    headers={
                        "Content-Disposition": f"attachment;filename={embung.nama}-{sampling.strftime('%B %Y')}.csv"
                    })

    return "ok"
