from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# ================= ADMIN ==================
class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(200))  # hashed


# ================= GEJALA ==================
class Gejala(db.Model):
    kode = db.Column(db.String(10), primary_key=True)
    nama_gejala = db.Column(db.String(200))


# ================= KATEGORI OBAT ==================
class KategoriObat(db.Model):
    kode = db.Column(db.String(10), primary_key=True)
    nama_kategori = db.Column(db.String(200))

    # hubungan: 1 kategori → banyak obat
    obat_list = db.relationship("Obat", backref="kategori", lazy=True)


# ================= OBAT ==================
class Obat(db.Model):
    kode = db.Column(db.String(10), primary_key=True)

    nama_obat = db.Column(db.String(200))
    deskripsi = db.Column(db.Text)
    golongan = db.Column(db.String(50))
    indikasi = db.Column(db.Text)
    komposisi = db.Column(db.Text)
    dosis = db.Column(db.Text)
    kontraindikasi = db.Column(db.Text)
    efek_samping = db.Column(db.Text)
    harga = db.Column(db.String(100))
    manufaktur = db.Column(db.String(200))
    warning = db.Column(db.Text)

    # 🖼️ Tambahkan kolom gambar
    gambar = db.Column(db.String(200))

    # foreign key → kategori
    kategori_kode = db.Column(
        db.String(10), 
        db.ForeignKey('kategori_obat.kode')
    )


class Rule(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    gejala_kode = db.Column(db.String(10), db.ForeignKey('gejala.kode'), nullable=False)
    kategori_list = db.Column(db.String(255), nullable=False)

    nilai_kepercayaan = db.Column(db.Float, nullable=False)


