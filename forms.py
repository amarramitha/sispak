from flask_wtf import FlaskForm
from wtforms import FloatField, StringField, PasswordField, SubmitField, TextAreaField, SelectField, SelectMultipleField, FloatField
from wtforms.validators import InputRequired, DataRequired
from flask_wtf.file import FileField, FileAllowed

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired()])
    password = PasswordField('Password', validators=[InputRequired()])
    submit = SubmitField('Login')

class GejalaForm(FlaskForm):
    kode = StringField('Kode Gejala', validators=[InputRequired()])
    nama_gejala = StringField('Nama Gejala', validators=[InputRequired()])
    submit = SubmitField('Simpan')

class ObatForm(FlaskForm):
    kode = StringField('Kode Obat', validators=[InputRequired()])
    nama_obat = StringField('Nama Obat', validators=[InputRequired()])
    golongan = StringField('Golongan')
    deskripsi = TextAreaField('Deskripsi')
    indikasi = TextAreaField('Indikasi')
    komposisi = TextAreaField('Komposisi')
    dosis = TextAreaField('Dosis')
    kontraindikasi = TextAreaField('Kontraindikasi')
    efek_samping = TextAreaField('Efek Samping')
    harga = StringField('Harga')  
    manufaktur = StringField('Manufaktur')
    warning = TextAreaField('Warning / Peringatan')
    kategori_kode = SelectField('Kategori Obat', choices=[])
    gambar = FileField("Gambar Obat", validators=[FileAllowed(['jpg','png','jpeg'])])
    submit = SubmitField('Simpan')


class KategoriForm(FlaskForm):
    kode = StringField('Kode Kategori', validators=[InputRequired()])
    nama_kategori = StringField('Nama Kategori', validators=[InputRequired()])
    submit = SubmitField('Simpan')


class RuleForm(FlaskForm):
    gejala_kode = SelectField("Gejala", choices=[], coerce=str)
    kategori_list = SelectMultipleField("Kategori Obat", choices=[], coerce=str)
    nilai_kepercayaan = FloatField("Nilai Kepercayaan", validators=[DataRequired()])
    submit = SubmitField("Simpan")





