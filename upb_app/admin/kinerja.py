from flask import Blueprint, request, render_template, redirect, url_for, jsonify, flash
from flask_login import login_required, current_user
from flask_wtf.csrf import generate_csrf
from upb_app.admin.kegiatan import save_image
from upb_app.models import Kerusakan, Bendungan, Asset, Foto
from upb_app.forms import LaporKerusakan, AddAsset
from upb_app import db, admin_only, petugas_only, role_check
from sqlalchemy.exc import IntegrityError
import datetime
import base64

from upb_app.admin import bp
# bp = Blueprint('kinerja', __name__)

komponen = [
    "Tubuh Bendungan - Puncak",
    "Tubuh Bendungan - Lereng Hulu",
    "Tubuh Bendungan - Lereng Hilir",
    "Bangunan Pengambilan - Jembatan Hantar",
    "Bangunan Pengambilan - Menara Intake",
    "Bangunan Pengambilan - Pintu Intake",
    "Bangunan Pengambilan - Peralatan Hidromekanikal",
    "Bangunan Pengambilan - Mesin Penggerak",
    "Bangunan Pengeluaran - Tunnel / Terowongan",
    "Bangunan Pengeluaran - Katup",
    "Bangunan Pengeluaran - Mesin Penggerak",
    "Bangunan Pengeluaran - Bangunan Pelindung",
    "Bangunan Pelimpah - Lantai Hulu",
    "Bangunan Pelimpah - Mercu Spillway",
    "Bangunan Pelimpah - Saluran Luncur",
    "Bangunan Pelimpah - Dinding / Sayap",
    "Bangunan Pelimpah - Peredam Energi",
    "Bangunan Pelimpah - Jembatan",
    "Bukit Tumpuan - Tumpuan Kiri Kanan",
    "Bangunan Pelengkap - Bangunan Pelengkap",
    "Bangunan Pelengkap - Akses Jalan",
    "Instrumentasi - Tekanan Air Pori",
    "Instrumentasi - Pergerakan Tanah",
    "Instrumentasi - Tekanan Air Tanah",
    "Instrumentasi - Rembesan",
    "Instrumentasi - Curah Hujan"
]


@bp.route('/kinerja')
@login_required
@admin_only
def kinerja():
    kat = ['berat', 'sedang', 'ringan']
    bends = Bendungan.query.all()
    kerusakan = Kerusakan.query.order_by(Kerusakan.tgl_lapor.desc()).all()

    kinerja = {}
    for ker in kerusakan:
        if ker.kategori not in kat:
            continue

        if ker.bendungan_id not in kinerja:
            kinerja[ker.bendungan_id] = {
                'kerusakan': [],
                'kategori': {}
            }
        kinerja[ker.bendungan_id]['kerusakan'].append(ker)

        if ker.kategori not in kinerja[ker.bendungan_id]['kategori']:
            kinerja[ker.bendungan_id]['kategori'][ker.kategori] = 0
        kinerja[ker.bendungan_id]['kategori'][ker.kategori] += 1
    for bend in bends:
        if bend.id in kinerja:
            arr = bend.nama.split('_')
            name = f"{arr[0].title()}.{arr[1].title()}"
            kinerja[bend.id]['bendungan'] = {
                'nama': name,
                'id': bend.id
            }
    print(kerusakan)

    return render_template('kinerja/index.html',
                            kinerja=kinerja)


@bp.route('/bendungan/kinerja/<bendungan_id>')
@login_required
@role_check
def kinerja_bendungan(bendungan_id):
    bend = Bendungan.query.get(bendungan_id)

    kerusakan = Kerusakan.query.filter(
                                    Kerusakan.bendungan_id == bendungan_id
                                ).order_by(
                                    Kerusakan.tgl_tanggapan.desc(),
                                    Kerusakan.tgl_lapor.desc()
                                ).all()
    ids = []
    komponens = []
    for ker in kerusakan:
        ids.append(ker.id)
        if ker.komponen not in komponens:
            komponens.append(ker.komponen)

    foto = {}
    fotos = Foto.query.filter(Foto.obj_type == 'kerusakan').all()
    for f in fotos:
        fid = f.obj_id
        if fid in ids:
            if fid not in foto:
                foto[fid] = []
            foto[fid].append({
                'url': f.url[7:],
                'keterangan': f.keterangan
            })

    return render_template('kinerja/bendungan.html',
                            name=bend.name,
                            bend_id=bend.id,
                            kerusakan=kerusakan,
                            komponens=komponens,
                            foto=foto)


@bp.route('/bendungan/kinerja/<bendungan_id>/asset', methods=['GET'])
@login_required
@petugas_only
def asset(bendungan_id):
    bend = Bendungan.query.get(bendungan_id)

    assets = Asset.query.filter(Asset.bendungan_id == bend.id).all()
    kerusakan = Kerusakan.query.filter(Kerusakan.bendungan_id == bend.id).all()

    ass = []
    rusak = []
    for ker in kerusakan:
        if ker.asset_id not in rusak:
            rusak.append(ker.asset_id)
    for asset in assets:
        ass.append({
            'id': asset.id,
            'asset': asset,
            'status': asset.id in rusak
        })

    return render_template('kinerja/asset.html',
                            name=bend.name,
                            bend_id=bend.id,
                            assets=ass,
                            csrf=generate_csrf(),
                            kategori=komponen)


@bp.route('/bendungan/kinerja/<bendungan_id>/asset/add', methods=['POST'])
@login_required
@petugas_only
def asset_add(bendungan_id):
    form = AddAsset()
    try:
        new_asset = Asset(
            nama=form.nama.data,
            kategori=form.kategori.data,
            bendungan_id=bendungan_id
        )
        if form.merk.data:
            new_asset.merk = form.merk.data
        if form.model.data:
            new_asset.model = form.model.data
        if form.tanggal.data:
            new_asset.perolehan = form.tanggal.data
        if form.nilai.data:
            new_asset.nilai_perolehan = form.nilai.data
        if form.bmn.data:
            new_asset.bmn = form.bmn.data

        db.session.add(new_asset)
        db.session.commit()

        flash(f"Asset berhasil ditambahkan", 'success')
        return redirect(url_for('admin.asset', bendungan_id=bendungan_id))
    except Exception as e:
        db.session.rollback()
        flash(f"Error {e}", 'danger')

    return redirect(url_for('admin.asset', bendungan_id=bendungan_id))


@bp.route('/bendungan/kinerja/<bendungan_id>/asset/<asset_id>/lapor', methods=['GET', 'POST'])
@login_required
@petugas_only
def kinerja_lapor(bendungan_id, asset_id):
    asset = Asset.query.get(asset_id)

    form = LaporKerusakan()
    if form.validate_on_submit():
        last_foto = Foto.query.order_by(Foto.id.desc()).first()
        new_id = 1 if not last_foto else (last_foto.id + 1)
        try:
            raw = form.foto.data
            imageStr = raw.split(',')[1]
            filename = f"kerusakan_{new_id}_{form.filename.data}"
            foto = save_image(imageStr, filename)
            foto.keterangan = form.keterangan.data
            foto.obj_type = "kerusakan"

            kerusakan = Kerusakan(
                tgl_lapor=datetime.datetime.now(),
                uraian=form.uraian.data,
                kategori=form.kategori.data,
                komponen=asset.kategori,
                bendungan_id=bendungan_id,
                asset_id=asset.id
            )
            db.session.add(kerusakan)
            db.session.add(foto)
            db.session.commit()

            foto.obj_id = kerusakan.id
            kerusakan.foto_id = foto.id
            db.session.commit()

            flash('Lapor Kerusakan berhasil !', 'success')
            return redirect(url_for('admin.kinerja_bendungan', bendungan_id=bendungan_id))
        except Exception as e:
            db.session.rollback()
            print(e)
            flash(f"Terjadi Error saat menyimpan data Kegiatan", 'danger')

    return render_template('kinerja/lapor.html',
                            bend_id=bendungan_id,
                            asset=asset,
                            csrf=generate_csrf())


@bp.route('/bendungan/kinerja/<bendungan_id>/foto', methods=['POST'])
@login_required
@petugas_only
def kinerja_foto(bendungan_id):
    last_foto = Foto.query.order_by(Foto.id.desc()).first()
    new_id = 1 if not last_foto else (last_foto.id + 1)
    try:
        ker_id = request.form.get('kerusakan_id')
        raw = request.form.get('foto')
        imageStr = raw.split(',')[1]
        filename = f"kerusakan_{new_id}_{request.form.get('filename')}"

        foto = save_image(imageStr, filename)
        foto.keterangan = request.form.get('keterangan')
        foto.obj_type = "kerusakan"
        foto.obj_id = ker_id

        db.session.add(foto)
        db.session.commit()

        flash("Foto berhasil disimpan", 'success')
        return redirect(url_for('admin.kinerja_bendungan', bendungan_id=bendungan_id))
    except Exception as e:
        db.session.rollback()
        print(e)
        flash(f"Error : {e}", 'danger')
        return redirect(url_for('admin.kinerja_bendungan', bendungan_id=bendungan_id))


@bp.route('/bendungan/kinerja/<ker_id>/tanggapan', methods=['POST'])
@login_required
@admin_only
def kinerja_tanggapan(ker_id):
    tang = request.form.get('tanggapan')
    kat = request.form.get('kategori', 'tidak rusak')

    ker = Kerusakan.query.get(int(ker_id))

    try:
        ker.tanggapan = tang
        ker.kategori = kat
        ker.tgl_tanggapan = datetime.datetime.now()
        ker.upb_id = current_user.id

        db.session.commit()
        flash('Tanggapan disimpan', 'success')
    except Exception as e:
        db.session.rollback()
        print(e)
        flash('Tanggapan gagal disimpan', 'danger')

    return redirect(url_for('admin.kinerja_bendungan', bendungan_id=ker.bendungan_id))


@bp.route('/bendungan/kinerja/update', methods=['POST'])  # @login_required
def kinerja_update():
    pk = request.values.get('pk')
    attr = request.values.get('name')
    val = request.values.get('value')
    row = Kerusakan.query.get(pk)
    setattr(row, attr, val)
    db.session.commit()

    result = {
        "name": attr,
        "pk": pk,
        "value": val
    }
    return jsonify(result)
