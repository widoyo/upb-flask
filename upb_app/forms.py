from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, DecimalField, DateField
from wtforms import BooleanField, SubmitField, SelectField, RadioField, FileField, TimeField
from wtforms.validators import DataRequired, Optional
from upb_app.models import Bendungan
import datetime

bends = [(b.id, b.nama) for b in Bendungan.query.all()]
bends.insert(0, (0, "Tidak Ada"))
roles = [
    ('1', '1'),
    ('2', '2'),
    ('3', '3'),
    ('4', '4')
]
jam = [
    ('06', '06'),
    ('12', '12'),
    ('18', '18')
]
petugas = [
    ("", "Tidak Ada"),
    ("koordinator", "Koordinator"),
    ("keamanan", "Keamanan"),
    ("pemantauan", "Pemantauan"),
    ("operasi", "Operasi"),
    ("pemeliharaan", "Pemeliharaan")
]
komponen = [
    ("Tubuh Bendungan - Puncak", "Tubuh Bendungan - Puncak"),
    ("Tubuh Bendungan - Lereng Hulu", "Tubuh Bendungan - Lereng Hulu"),
    ("Tubuh Bendungan - Lereng Hilir", "Tubuh Bendungan - Lereng Hilir"),
    ("Bangunan Pengambilan - Jembatan Hantar", "Bangunan Pengambilan - Jembatan Hantar"),
    ("Bangunan Pengambilan - Menara Intake", "Bangunan Pengambilan - Menara Intake"),
    ("Bangunan Pengambilan - Pintu Intake", "Bangunan Pengambilan - Pintu Intake"),
    ("Bangunan Pengambilan - Peralatan Hidromekanikal", "Bangunan Pengambilan - Peralatan Hidromekanikal"),
    ("Bangunan Pengambilan - Mesin Penggerak", "Bangunan Pengambilan - Mesin Penggerak"),
    ("Bangunan Pengeluaran - Tunnel / Terowongan", "Bangunan Pengambilan - Tunnel / Terowongan"),
    ("Bangunan Pengeluaran - Katup", "Bangunan Pengambilan - Katup"),
    ("Bangunan Pengeluaran - Mesin Penggerak", "Bangunan Pengambilan - Mesin Penggerak"),
    ("Bangunan Pengeluaran - Bangunan Pelindung", "Bangunan Pengambilan - Bangunan Pelindung"),
    ("Bangunan Pelimpah - Lantai Hulu", "Bangunan Pelimpah - Lantai Hulu"),
    ("Bangunan Pelimpah - Mercu Spillway", "Bangunan Pelimpah - Mercu Spillway"),
    ("Bangunan Pelimpah - Saluran Luncur", "Bangunan Pelimpah - Saluran Luncur"),
    ("Bangunan Pelimpah - Dinding / Sayap", "Bangunan Pelimpah - Dinding / Sayap"),
    ("Bangunan Pelimpah - Peredam Energi", "Bangunan Pelimpah - Peredam Energi"),
    ("Bangunan Pelimpah - Jembatan", "Bangunan Pelimpah - Jembatan"),
    ("Bukit Tumpuan - Tumpuan Kiri Kanan", "Bukit Tumpuan - Tumpuan Kiri Kanan"),
    ("Bangunan Pelengkap - Bangunan Pelengkap", "Bangunan Pelengkap - Bangunan Pelengkap"),
    ("Bangunan Pelengkap - Akses Jalan", "Bangunan Pelengkap - Akses Jalan"),
    ("Instrumentasi - Tekanan Air Pori", "Instrumentasi - Tekanan Air Pori"),
    ("Instrumentasi - Pergerakan Tanah", "Instrumentasi - Pergerakan Tanah"),
    ("Instrumentasi - Tekanan Air Tanah", "Instrumentasi - Tekanan Air Tanah"),
    ("Instrumentasi - Rembesan", "Instrumentasi - Rembesan"),
    ("Instrumentasi - Curah Hujan", "Instrumentasi - Curah Hujan")
]
kategori = [
    ('tidak rusak', 'Tidak Rusak'),
    ('ringan', 'Ringan'),
    ('sedang', 'Sedang'),
    ('berat', 'Berat')
]


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Ingat saya')
    submit = SubmitField('Login')


class AddUser(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    bendungan = SelectField("Bendungan", choices=bends, validators=[Optional()], default=bends[0][0], coerce=int)
    role = SelectField("Role", choices=roles, validators=[DataRequired()], default=roles[0][0])
    submit = SubmitField('Tambah')


class AddDaily(FlaskForm):
    sampling = DateField("Hari", default=datetime.datetime.today())
    curahhujan = DecimalField('Curah Hujan')
    inflow_deb = DecimalField('Inflow Debit')
    inflow_vol = DecimalField('Inflow Volume')
    outflow_deb = DecimalField('Outflow Debit')
    outflow_vol = DecimalField('Outflow Volume')
    spillway_deb = DecimalField('Spillway Debit')
    spillway_vol = DecimalField('Spillway Volume')
    jam = SelectField("Jam", choices=jam, validators=[DataRequired()], default=jam[0][0])
    tma = DecimalField('TMA')
    vol = DecimalField('Volume')
    submit = SubmitField('Tambah')


class AddTma(FlaskForm):
    hari = DateField("Hari", default=datetime.datetime.today())
    jam = SelectField("Jam", choices=jam, validators=[DataRequired()], default=jam[0][0])
    tma = DecimalField('TMA')
    vol = DecimalField('Volume')
    submit = SubmitField('Kirim')


class LaporBanjir(FlaskForm):
    tanggal = DateField("Tanggal", default=datetime.datetime.today())
    jam = StringField("Jam")
    tma = DecimalField('TMA')
    spillway_deb = DecimalField('Spillway Debit', validators=[Optional()])
    submit = SubmitField('Kirim')


class CHTerkini(FlaskForm):
    tanggal = DateField("Tanggal", default=datetime.datetime.today())
    jam = StringField("Jam")
    ch = DecimalField('Curah Hujan')
    submit = SubmitField('Kirim')


class AddVnotch(FlaskForm):
    sampling = DateField("Hari", default=datetime.datetime.today())
    vn1_tma = DecimalField('Vnotch 1 TMA', validators=[Optional()])
    vn1_deb = DecimalField('Vnotch 1 Debit', validators=[Optional()])
    vn2_tma = DecimalField('Vnotch 2 TMA', validators=[Optional()])
    vn2_deb = DecimalField('Vnotch 2 Debit', validators=[Optional()])
    vn3_tma = DecimalField('Vnotch 3 TMA', validators=[Optional()])
    vn3_deb = DecimalField('Vnotch 3 Debit', validators=[Optional()])
    submit = SubmitField('Kirim')


class AddPiezo(FlaskForm):
    sampling = DateField("Hari", default=datetime.datetime.today())
    p1a = DecimalField('Piezo 1A', validators=[Optional()])
    p1b = DecimalField('Piezo 1B', validators=[Optional()])
    p1c = DecimalField('Piezo 1C', validators=[Optional()])
    p2a = DecimalField('Piezo 2A', validators=[Optional()])
    p2b = DecimalField('Piezo 2B', validators=[Optional()])
    p2c = DecimalField('Piezo 2C', validators=[Optional()])
    p3a = DecimalField('Piezo 3A', validators=[Optional()])
    p3b = DecimalField('Piezo 3B', validators=[Optional()])
    p3c = DecimalField('Piezo 3C', validators=[Optional()])
    p4a = DecimalField('Piezo 4A', validators=[Optional()])
    p4b = DecimalField('Piezo 4B', validators=[Optional()])
    p4c = DecimalField('Piezo 4C', validators=[Optional()])
    p5a = DecimalField('Piezo 5A', validators=[Optional()])
    p5b = DecimalField('Piezo 5B', validators=[Optional()])
    p5c = DecimalField('Piezo 5C', validators=[Optional()])
    submit = SubmitField('Kirim')


class AddKegiatan(FlaskForm):
    sampling = DateField("Hari", default=datetime.datetime.today())
    foto = FileField("Foto")
    filename = StringField('Filename')
    petugas = SelectField("Petugas", choices=petugas, validators=[DataRequired()], default=petugas[0][0])
    keterangan = StringField('Keterangan', validators=[DataRequired()])
    submit = SubmitField('Tambah')


class AddAsset(FlaskForm):
    nama = StringField('Nama', validators=[DataRequired()])
    kategori = SelectField("Komponen", choices=komponen, validators=[DataRequired()], default=komponen[0][0])
    merk = StringField('Merk')
    model = StringField('Model')
    tanggal = DateField("Tanggal Perolehan")
    nilai = StringField('Nilai Perolehan')
    bmn = StringField('No. BMN')


class LaporKerusakan(FlaskForm):
    uraian = StringField('Uraian', validators=[DataRequired()])
    kategori = SelectField("kategori", choices=kategori, validators=[DataRequired()], default=kategori[0][0])
    foto = FileField("Foto")
    filename = StringField('Filename')
    komponen = SelectField("Komponen", choices=komponen, validators=[DataRequired()], default=komponen[0][0])
    keterangan = StringField('Keterangan', validators=[DataRequired()])
    submit = SubmitField('Lapor')
