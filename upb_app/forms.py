from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, DecimalField, DateField
from wtforms import BooleanField, SubmitField, SelectField, RadioField, FileField
from wtforms.validators import DataRequired
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
    bendungan = SelectField("Bendungan", choices=bends, validators=[DataRequired()], default=bends[0][0], coerce=int)
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


class AddVnotch(FlaskForm):
    sampling = DateField("Hari", default=datetime.datetime.today())
    vn1_tma = DecimalField('Vnotch 1 TMA', default=0)
    vn1_deb = DecimalField('Vnotch 1 Debit', default=0)
    vn2_tma = DecimalField('Vnotch 2 TMA', default=0)
    vn2_deb = DecimalField('Vnotch 2 Debit', default=0)
    vn3_tma = DecimalField('Vnotch 3 TMA', default=0)
    vn3_deb = DecimalField('Vnotch 3 Debit', default=0)
    submit = SubmitField('Kirim')


class AddPiezo(FlaskForm):
    sampling = DateField("Hari", default=datetime.datetime.today())
    p1a = DecimalField('Piezo 1A', default=0)
    p1b = DecimalField('Piezo 1B', default=0)
    p1c = DecimalField('Piezo 1C', default=0)
    p2a = DecimalField('Piezo 2A', default=0)
    p2b = DecimalField('Piezo 2B', default=0)
    p2c = DecimalField('Piezo 2C', default=0)
    p3a = DecimalField('Piezo 3A', default=0)
    p3b = DecimalField('Piezo 3B', default=0)
    p3c = DecimalField('Piezo 3C', default=0)
    p4a = DecimalField('Piezo 4A', default=0)
    p4b = DecimalField('Piezo 4B', default=0)
    p4c = DecimalField('Piezo 4C', default=0)
    p5a = DecimalField('Piezo 5A', default=0)
    p5b = DecimalField('Piezo 5B', default=0)
    p5c = DecimalField('Piezo 5C', default=0)
    submit = SubmitField('Kirim')


class AddKegiatan(FlaskForm):
    sampling = DateField("Hari", default=datetime.datetime.today())
    foto = FileField("Foto")
    petugas = SelectField("Petugas", choices=petugas, validators=[DataRequired()], default=petugas[0][0])
    uraian = StringField('Keterangan', validators=[DataRequired()])
    submit = SubmitField('Tambah')


class LaporKerusakan(FlaskForm):
    uraian = StringField('Uraian', validators=[DataRequired()]),
    kategori = SelectField("kategori", choices=kategori, validators=[DataRequired()], default=kategori[0][0]),
    foto = FileField("Foto"),
    komponen = SelectField("Komponen", choices=komponen, validators=[DataRequired()], default=komponen[0][0])
    keterangan = StringField('Keterangan', validators=[DataRequired()])
    submit = SubmitField('Lapor')
