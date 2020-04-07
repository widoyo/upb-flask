from flask import Blueprint, request, render_template, redirect, url_for, jsonify, flash
from flask_login import login_required, current_user
from upb_app.admin.kegiatan import save_image
from upb_app.models import Kerusakan, Bendungan, Asset, Foto
from upb_app.forms import LaporKerusakan
from upb_app import db, admin_only, petugas_only, get_bendungan
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


@bp.route('/kinerja/bendungan')
@login_required
@get_bendungan
def kinerja_bendungan(bend):
    bendungan_id = bend.id
    arr = bend.nama.split('_')
    name = f"{arr[0].title()}.{arr[1].title()}"
    kerusakan = Kerusakan.query.filter(
                                    Kerusakan.bendungan_id == bendungan_id
                                ).order_by(
                                    Kerusakan.tgl_lapor.desc()
                                ).all()
    ids = []
    komponens = []
    for ker in kerusakan:
        ids.append(ker.id)
        if ker.komponen not in komponens:
            komponens.append(ker.komponen)

    foto = {}
    fotos = Foto.query.filter(Foto.obj_type == 'kinerja').all()
    for f in fotos:
        if f.obj_id in ids:
            foto[f.obj_id] = f

    return render_template('kinerja/bendungan.html',
                            name=name,
                            bend_id=bend.id,
                            kerusakan=kerusakan,
                            komponens=komponens,
                            foto=foto)


@bp.route('/kinerja/bendungan/asset', methods=['GET'])
@login_required
@petugas_only
def asset():
    bend = Bendungan.query.get(current_user.bendungan_id)
    arr = bend.nama.split('_')
    name = f"{arr[0].title()}.{arr[1].title()}"

    assets = Asset.query.filter(Asset.bendungan_id == bend.id).all()
    kerusakan = Kerusakan.query.filter(Kerusakan.bendungan_id == bend.id).all()

    ass = []
    rusak = []
    for ker in kerusakan:
        if ker.asset_id not in rusak:
            rusak.append(ker.asset_id)
    for asset in assets:
        ass.append({
            'asset': asset,
            'status': asset.id in rusak
        })

    return render_template('kinerja/asset.html',
                            name=name,
                            bend_id=bend.id,
                            assets=ass,
                            kategori=komponen)


@bp.route('/kinerja/bendungan/asset', methods=['POST'])
@login_required
@petugas_only
def asset_add():
    bendungan_id = current_user.bendungan_id
    form = AddAsset(
        merk="null",
        model="null",
        tanggal="null",
        nilai="null",
        bmn="null"
    )
    if form.validate_on_submit():
        try:
            new_asset = Asset(
                nama=request.nama.data,
                kategori=request.kategori.data,
                bendungan_id=bendungan_id
            )
            if request.merk.data != "null":
                new_asset.merk = request.merk.data
            if request.model.data != "null":
                new_asset.model = request.model.data
            if request.perolehan.data != "null":
                new_asset.perolehan = request.perolehan.data
            if request.nilai_perolehan.data != "null":
                new_asset.nilai_perolehan = request.nilai_perolehan.data
            if request.bmn.data != "null":
                new_asset.bmn = request.bmn.data

            db.session.add(new_asset)
            db.session.commit()

            flash(f"Asset berhasil ditambahkan", 'success')
            return redirect(url_for('admin.asset'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error {e}", 'danger')

    return redirect(url_for('admin.asset'))


@bp.route('/kinerja/bendungan/lapor', methods=['POST'])
@login_required
@petugas_only
def kinerja_lapor():
    bendungan_id = current_user.bendungan_id
    form = LaporKerusakan()
    if form.validate_on_submit():
        last_foto = Foto.query.order_by(Foto.id.desc()).first()
        new_id = 1 if not last_foto else (last_foto.id + 1)
        try:
            raw = request.foto.data
            imageStr = base64.b64encode(raw).decode('ascii')
            filename = f"kegiatan_{new_id}_{request.foto.data.filename}"
            foto = save_image(imageStr, filename)
            foto.keterangan = form.values.get("keterangan")
            foto.obj_type = "kerusakan"

            kerusakan = Kerusakan(
                tgl_lapor=datetime.datetime.now(),
                uraian=form.values.get("uraian"),
                kategori=form.values.get("kategori"),
                komponen=form.values.get("komponen"),
                bendungan_id=bendungan_id
            )
            db.session.add(kerusakan)
            db.session.add(foto)
            db.session.commit()

            foto.obj_id = kerusakan.id
            kerusakan.foto_id = foto.id
            db.session.commit()

            flash('Lapor Kerusakan berhasil !', 'success')
            return redirect(url_for('admin.kinerja_bendungan'))
        except IntegrityError:
            db.session.rollback()
            flash('Data sudah ada, mohon update untuk mengubah', 'danger')

    return redirect(url_for('admin.kinerja_bendungan'))


@bp.route('/kinerja/bendungan/foto', methods=['POST'])
@login_required
@petugas_only
def kinerja_foto():
    last_foto = Foto.query.order_by(Foto.id.desc()).first()
    new_id = 1 if not last_foto else (last_foto.id + 1)
    try:
        ker_id = request.args.get('kerusakan_id')
        raw = request.foto.data
        imageStr = base64.b64encode(raw).decode('ascii')
        filename = f"kerusakan_{new_id}_{request.foto.data.filename}"

        foto = save_image(imageStr, filename)
        foto.keterangan = request.args.get('keterangan')
        foto.obj_type = "kinerja"
        foto.obj_id = ker_id
        db.session.add(foto)
        db.session.commit()

        flash("Foto berhasil disimpan", 'success')
        return redirect(url_for('admin.kinerja_bendungan'))
    except Exception as e:
        db.session.rollback()
        flash(f"Error : {e}", 'danger')
        return redirect(url_for('admin.kinerja_bendungan'))


@bp.route('/kinerja/<bendungan_id>/tanggapan', methods=['POST'])
@login_required
@admin_only
def kinerja_tanggapan(bendungan_id):
    tang = request.args.get('tanggapan')
    ker_id = request.args.get('ker_id')
    kat = request.args.get('kategori', 'tidak rusak')

    ker = Kerusakan.query.get(int(ker_id))

    ker.tanggapan_upb = tang
    ker.kategori = kat
    ker.tgl_tanggapan = datetime.datetime.now()
    ker.upb_id = current_user.id

    db.session.commit()

    flash('Tanggapan disimpan', 'success')
    return redirect(url_for('admin.kinerja_bendungan'))


@bp.route('/kinerja/update', methods=['POST'])  # @login_required
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
