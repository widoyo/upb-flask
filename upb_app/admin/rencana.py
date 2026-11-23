from flask import Blueprint, request, render_template, redirect, flash
from flask import Response, url_for, jsonify
from flask_login import login_required
from sqlalchemy import and_
from upb_app.helper import to_date
from upb_app.models import Bendungan, Rencana, wil_sungai, WET_MONTHS, DRY_MONTHS
from upb_app import db, admin_only
import datetime
import calendar
import csv
import io

from upb_app.admin import bp
# bp = Blueprint('rtow', __name__)


@bp.route('/bendungan/rtow')
@login_required
@admin_only
def rtow():
    sampling = request.values.get('sampling')
    sampling = datetime.datetime.strptime(sampling, "%Y-%m-%d") if sampling else datetime.datetime.now()

    year = (sampling.year) if sampling.month < 11 else sampling.year + 1
    start = datetime.datetime.strptime(f"{year - 1}-11-01", "%Y-%m-%d")
    end = datetime.datetime.strptime(f"{year}-10-31", "%Y-%m-%d")

    bends = Bendungan.query.all()
    '''
    TABUNGAN ALGORITMA, YANG ADA TERLALU RUWET
    bds_1 = [b for b in bends if b.wil_sungai == '1']
    bds_2 = [b for b in bends if b.wil_sungai == '2']
    bds_3 = [b for b in bends if b.wil_sungai == '3']
    rencana = Rencana.query.filter(
                            and_(
                                Rencana.sampling >= start,
                                Rencana.sampling <= end),
                            ).order_by(Rencana.sampling).all()
    for b in bds_1:
        b.rencana_row1 = [r for r in rencana if r.bendungan_id == b.id and r.sampling.month in WET_MONTHS]
        b.rencana_row2 = [r for r in rencana if r.bendungan_id == b.id and r.sampling.month in DRY_MONTHS]
    for b in bds_2:
        b.rencana_row1 = [r for r in rencana if r.bendungan_id == b.id and r.sampling.month in WET_MONTHS]
        b.rencana_row2 = [r for r in rencana if r.bendungan_id == b.id and r.sampling.month in DRY_MONTHS]
    for b in bds_3:
        b.rencana_row1 = [r for r in rencana if r.bendungan_id == b.id and r.sampling.month in WET_MONTHS]
        b.rencana_row2 = [r for r in rencana if r.bendungan_id == b.id and r.sampling.month in DRY_MONTHS]
        
    print('len(rencana):', len(rencana))
    '''
    rencana = Rencana.query.filter(
                            and_(
                                Rencana.sampling >= start,
                                Rencana.sampling <= end),
                            ).order_by(Rencana.sampling).all()
    rencana_s = {}
    for bend in bends:
        rencana_s[bend.id] = []
    for ren in rencana:
        rencana_s[ren.bendungan_id].append(ren)

    rtow = {
        '1': {
            'date_list': [],
            'data': {}
        },
        '2': {
            'date_list': [],
            'data': {}
        },
        '3': {
            'date_list': [],
            'data': {}
        }
    }
    for bend in bends:
        temp = {}
        for ren in rencana_s[bend.id]:
            index = ren.sampling.strftime('%d %b %y')
            last_day = calendar.monthrange(ren.sampling.year, ren.sampling.month)[1]

            if sampling.year >= 2020 and bend.wil_sungai in ['2', '3']:
                if ren.sampling.day in [10, 20, last_day]:
                    temp[index] = ren
                    if index not in rtow[bend.wil_sungai]['date_list']:
                        rtow[bend.wil_sungai]['date_list'].append(index)
            elif sampling.year >= 2019 and ren.sampling.day in [15, last_day]:
                temp[index] = ren
                if index not in rtow[bend.wil_sungai]['date_list']:
                    rtow[bend.wil_sungai]['date_list'].append(index)
            elif sampling.year <= 2018 and ren.sampling.day in [1, 16]:
                temp[index] = ren
                if index not in rtow[bend.wil_sungai]['date_list']:
                    rtow[bend.wil_sungai]['date_list'].append(index)

        rtow[bend.wil_sungai]['data'][bend.id] = {
            "bend": bend,
            "data": temp
        }
    #print('len(rtow):', rtow['2']['data'][108]['data'])
    return render_template('rencana/index.html',
                            sampling=sampling,
                            rtow=rtow,
                            wil_sungai=wil_sungai,
                            year=year)


@bp.route('/bendungan/<bendungan_id>/rtow/export', methods=['GET'])
@login_required
@admin_only
def rtow_exports(bendungan_id):
    sampling_param = request.args.get('sampling')

    sampling = (
        datetime.datetime.strptime(sampling_param, "%Y-%m-%d")
        if sampling_param
        else datetime.datetime.now()
    )
    
    year = sampling.year if sampling.month < 11 else sampling.year + 1

    start = datetime.datetime(year - 1, 11, 1)
    end = datetime.datetime(year, 10, 31)
    
    bend = Bendungan.query.get(bendungan_id)
    rencana = Rencana.query.filter(
                            and_(
                                Rencana.sampling >= start,
                                Rencana.sampling <= end),
                            Rencana.bendungan_id == bendungan_id
                            ).order_by(Rencana.sampling).all()
    

    data = []
    three_periods = bend.wil_sungai in ['2', '3']

    print('Bendungan:', bend.nama)
    print('Wilayah Sungai:', repr(bend.wil_sungai))
    print('Three periods:', three_periods)

    for ren in rencana:
        last_day = calendar.monthrange(
            ren.sampling.year,
            ren.sampling.month
        )[1]

        if three_periods and ren.sampling.year >= 2020:
            valid_days = [10, 20, last_day]
        else:
            valid_days = [15, last_day]

        if ren.sampling.day in valid_days:
            data.append(ren)
        
    pre_csv = [[bend.nama]]
    pre_csv.append(['waktu', 'po_tma', 'po_vol', 'po_outflow_q', 'po_inflow_q', 'po_bona', 'po_bonb', 'vol_bona', 'vol_bonb'])
    for d in data:
        pre_csv.append([
            d.sampling.strftime("%Y-%m-%d"),
            d.po_tma or None,
            d.po_vol or None,
            d.po_outflow_deb or None,
            d.po_inflow_deb or None,
            d.po_bona or None,
            d.po_bonb or None,
            d.vol_bona or None,
            d.vol_bonb or None
        ])
    output = io.StringIO()
    writer = csv.writer(output, delimiter='\t')
    for l in pre_csv:
        writer.writerow(l)
    output.seek(0)

    return Response(output,
                    mimetype="text/csv",
                    headers={
                        "Content-Disposition": f"attachment;filename={bend.nama}.csv"
                    })


@bp.route('/bendungan/<bendungan_id>/rtow/import', methods=['GET', 'POST'])
@login_required
@admin_only
def rtow_imports(bendungan_id):
    bend = Bendungan.query.get_or_404(bendungan_id)

    if request.method == "POST":
        file = request.files.get('upload')
        if not file or file.filename == '':
            flash("Tidak ada file yang dipilih.", 'danger')
            return redirect(request.url)

        try:
            # 1. Baca dan decode file
            file_content = file.stream.read().decode("utf-8")
            lines = file_content.splitlines()
            
            # 2. Cari baris header (yang mengandung kata "waktu")
            # Ini mengabaikan baris pertama seperti "bd_delingan"
            header_idx = -1
            for i, line in enumerate(lines):
                if "waktu" in line.lower().split('\t') or "waktu" in line.lower().split(','):
                    header_idx = i
                    break
            
            if header_idx == -1:
                flash("Format file tidak valid. Kolom 'waktu' tidak ditemukan.", 'danger')
                return redirect(request.url)

            # 3. Buat stream CSV hanya dari baris header ke bawah
            valid_csv_data = "\n".join(lines[header_idx:])
            csv_stream = io.StringIO(valid_csv_data)
            reader = csv.DictReader(csv_stream, delimiter='\t')
            try:
                dialect = csv.Sniffer().sniff(valid_csv_data[:4096], delimiters='\t,')
                reader = csv.DictReader(csv_stream, dialect=dialect)
            except csv.Error:
                pass
            
            # 4. Bersihkan nama kolom
            reader.fieldnames = [name.strip() for name in reader.fieldnames]
            records_to_insert = []
            sampling_dates_to_check = []

            # Helper: Konversi string kosong menjadi None (NULL di database)
            def to_float(val):
                val = str(val).strip() if val else ""
                return float(val) if val else None

            # 4. Proses setiap baris data
            for row in reader:
                try:
                    # Parsing tanggal menjadi objek datetime (waktu default 00:00:00)
                    sampling_dt = datetime.datetime.strptime(row['waktu'].strip(), "%Y-%m-%d")
                    sampling_dates_to_check.append(sampling_dt)
                    
                    # Mapping kolom CSV ke Model Rencana
                    new_record = Rencana(
                        bendungan_id=bendungan_id,
                        sampling=sampling_dt,
                        po_tma=to_float(row.get('po_tma')),
                        po_vol=to_float(row.get('po_vol')),
                        # Mapping nama kolom CSV (po_inflow_q) ke model (po_inflow_deb)
                        po_inflow_deb=to_float(row.get('po_inflow_q')),
                        po_outflow_deb=to_float(row.get('po_outflow_q')),
                        po_bona=to_float(row.get('po_bona')),
                        po_bonb=to_float(row.get('po_bonb')),
                        vol_bona=to_float(row.get('vol_bona')),
                        vol_bonb=to_float(row.get('vol_bonb'))
                        # po_inflow_vol dan po_outflow_vol diabaikan karena tidak ada di CSV
                    )
                    records_to_insert.append(new_record)
                
                except ValueError as e:
                    # Lewati baris yang format tanggal/angkanya rusak, tapi catat peringatan
                    flash(f"Peringatan: Baris dengan waktu '{row.get('waktu')}' dilewati (format tidak valid).", 'warning')
                    continue

            if not records_to_insert:
                flash("Tidak ada data valid yang ditemukan untuk diimport.", 'danger')
                return redirect(request.url)

            # 5. Eksekusi ke Database dengan Transaksi
            try:
                # Hapus data lama yang memiliki bendungan_id dan tanggal (sampling) yang sama
                # Ini mencegah UniqueConstraint error saat re-import
                Rencana.query.filter(
                    Rencana.bendungan_id == bendungan_id,
                    Rencana.sampling.in_(sampling_dates_to_check)
                ).delete(synchronize_session=False)
                
                # Masukkan data baru
                db.session.add_all(records_to_insert)
                db.session.commit()
                
                flash(f"Berhasil mengimport {len(records_to_insert)} data RTOW.", 'success')
            
            except Exception as e:
                db.session.rollback()
                flash(f"Gagal menyimpan ke database: {str(e)}", 'danger')
                # print(e) # Aktifkan untuk debugging di console server jika perlu

        except Exception as e:
            flash(f"Terjadi kesalahan saat memproses file: {str(e)}", 'danger')

        # Redirect ke halaman operasi/RTOW setelah selesai
        return redirect(url_for('bendungan.operasi', lokasi_id=bendungan_id))

    return render_template('rencana/import.html', bend=bend)

@bp.route('/bendungan/rtow/update', methods=['POST'])  # @login_required  # @admin_only
def rtow_update():
    pk = request.values.get('pk')
    attr = request.values.get('name')
    val = request.values.get('value')
    row = Rencana.query.get(pk)
    setattr(row, attr, val)
    db.session.commit()

    result = {
        "name": attr,
        "pk": pk,
        "value": val
    }
    return jsonify(result)


def rtow_upload(data, bend_id):
    columns = [col.replace('q', 'deb') for col in data[1]]
    for row in data[2:]:
        sampling = to_date(row[0])
        rencana = Rencana.query.filter(
                                    Rencana.sampling == sampling,
                                    Rencana.bendungan_id == bend_id
                                ).first()
        if not rencana:
            rencana = Rencana(sampling=sampling, bendungan_id=bend_id)
            db.session.add(rencana)

        for i, col in enumerate(columns[1:]):
            if row[i+1]:
                setattr(rencana, col, float(row[i+1].replace(',', '.')))

    try:
        db.session.commit()
        flash('RTOW berhasil ditambahkan !', 'success')
    except Exception as e:
        db.session.rollback()
        print(e)
        flash(f"RTOW gagal ditambahkan", 'danger')
