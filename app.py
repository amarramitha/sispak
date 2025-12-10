from flask import Flask, render_template, redirect, url_for, session, request, flash
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, Admin, Gejala, Obat, Rule, KategoriObat
from forms import LoginForm, GejalaForm, ObatForm, RuleForm, KategoriForm
from functools import wraps
from flask_migrate import Migrate   
from utils.dempster import hitung_dempster, normalize_mass
from werkzeug.utils import secure_filename
import os
from sqlalchemy import func, cast, Integer

UPLOAD_FOLDER = "static/obat"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.config.from_pyfile("config.py")

db.init_app(app)
migrate = Migrate(app, db)


# ------------------------------------------
# LOGIN REQUIRED
# ------------------------------------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


@app.route("/")
def landing():
    return render_template("landing/index.html")


# ------------------------------------------
# LOGIN ADMIN
# ------------------------------------------
@app.route("/admin/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        admin = Admin.query.filter_by(username=form.username.data).first()
        if admin and check_password_hash(admin.password, form.password.data):
            session['admin'] = admin.username
            return redirect(url_for('dashboard'))
        else:
            flash("Username atau password salah!", "danger")
    return render_template("admin/login.html", form=form)


@app.route("/logout")
def logout():
    session.pop("admin", None)
    return redirect(url_for("landing"))


@app.route("/dashboard")
@login_required
def dashboard():
    gejala_count = Gejala.query.count()
    obat_count = Obat.query.count()
    rule_count = Rule.query.count()
    return render_template("admin/dashboard.html",
                           gejala_count=gejala_count,
                           obat_count=obat_count,
                           rule_count=rule_count)


# ------------------------------------------
# CRUD GEJALA  (PK = kode)
# ------------------------------------------
@app.route("/gejala")
@login_required
def gejala_index():
    data = Gejala.query.all()
    return render_template("admin/gejala/index.html", data=data)


@app.route("/gejala/create", methods=["GET", "POST"])
@login_required
def gejala_create():
    form = GejalaForm()
    if form.validate_on_submit():
        g = Gejala(kode=form.kode.data, nama_gejala=form.nama_gejala.data)
        db.session.add(g)
        db.session.commit()
        return redirect(url_for('gejala_index'))
    return render_template("admin/gejala/create.html", form=form)


@app.route("/gejala/edit/<string:kode>", methods=["GET", "POST"])
@login_required
def gejala_edit(kode):
    g = Gejala.query.get_or_404(kode)
    form = GejalaForm(obj=g)

    # PK tidak boleh diedit
    form.kode.render_kw = {"readonly": True}

    if form.validate_on_submit():
        g.nama_gejala = form.nama_gejala.data
        db.session.commit()
        return redirect(url_for('gejala_index'))

    return render_template("admin/gejala/edit.html", form=form)


@app.route("/gejala/delete/<string:kode>")
@login_required
def gejala_delete(kode):
    g = Gejala.query.get_or_404(kode)
    db.session.delete(g)
    db.session.commit()
    return redirect(url_for('gejala_index'))


# ------------------------------------------
# CRUD KATEGORI (PK = kode)
# ------------------------------------------
@app.route('/admin/kategori')
def kategori_index():
    data = KategoriObat.query.all()
    return render_template('admin/kategori/index.html', data=data)


@app.route('/admin/kategori/create', methods=['GET', 'POST'])
def kategori_create():
    form = KategoriForm()
    if form.validate_on_submit():
        kategori = KategoriObat(kode=form.kode.data,
                                nama_kategori=form.nama_kategori.data)
        db.session.add(kategori)
        db.session.commit()
        flash("Kategori berhasil ditambahkan!", "success")
        return redirect(url_for('kategori_index'))
    return render_template('admin/kategori/create.html', form=form)


@app.route('/admin/kategori/edit/<string:kode>', methods=['GET', 'POST'])
def kategori_edit(kode):
    kategori = KategoriObat.query.get_or_404(kode)
    form = KategoriForm(obj=kategori)
    
    form.kode.render_kw = {"readonly": True}

    if form.validate_on_submit():
        kategori.nama_kategori = form.nama_kategori.data
        db.session.commit()
        flash("Kategori berhasil diperbarui!", "success")
        return redirect(url_for('kategori_index'))
    
    return render_template('admin/kategori/edit.html', form=form)


@app.route('/admin/kategori/delete/<string:kode>')
def kategori_delete(kode):
    kategori = KategoriObat.query.get_or_404(kode)
    db.session.delete(kategori)
    db.session.commit()
    flash("Kategori berhasil dihapus!", "success")
    return redirect(url_for('kategori_index'))


# ------------------------------------------
# CRUD OBAT (PK = kode)
# ------------------------------------------
@app.route("/obat")
@login_required
def obat_index():
    data = Obat.query.all()
    return render_template("admin/obat/index.html", data=data)


@app.route("/obat/create", methods=["GET", "POST"])
@login_required
def obat_create():
    form = ObatForm()

    # ambil kategori
    kategori = KategoriObat.query.all()
    form.kategori_kode.choices = [(k.kode, k.nama_kategori) for k in kategori]

    if form.validate_on_submit():

        # ---- HANDLE GAMBAR ----
        filename = None
        if form.gambar.data:
            file = form.gambar.data
            filename = secure_filename(file.filename)
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)

        # ---- SIMPAN DATA OBAT ----
        obat = Obat(
            kategori_kode=form.kategori_kode.data,
            kode=form.kode.data,
            nama_obat=form.nama_obat.data,
            golongan=form.golongan.data,
            deskripsi=form.deskripsi.data,
            indikasi=form.indikasi.data,
            komposisi=form.komposisi.data,
            dosis=form.dosis.data,
            kontraindikasi=form.kontraindikasi.data,
            efek_samping=form.efek_samping.data,
            warning=form.warning.data,
            harga=form.harga.data,
            manufaktur=form.manufaktur.data,
            gambar=filename
        )

        db.session.add(obat)
        db.session.commit()

        return redirect(url_for('obat_index'))

    return render_template('admin/obat/create.html', form=form)

@app.route("/obat/edit/<string:kode>", methods=["GET", "POST"])
@login_required
def obat_edit(kode):
    o = Obat.query.get_or_404(kode)
    form = ObatForm(obj=o)

    # Set pilihan kategori
    kategori = KategoriObat.query.all()
    form.kategori_kode.choices = [(k.kode, k.nama_kategori) for k in kategori]

    # Kode tidak boleh diedit
    form.kode.render_kw = {"readonly": True}

    if form.validate_on_submit():

        # ===========================
        #  HANDLE UPLOAD GAMBAR BARU
        # ===========================
        file = form.gambar.data

        # Pastikan file valid (bukan string kosong)
        if file and hasattr(file, "filename") and file.filename != "":
            filename = secure_filename(file.filename)
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)

            # Hapus gambar lama jika ada
            if o.gambar:
                old_path = os.path.join(UPLOAD_FOLDER, o.gambar)
                if os.path.exists(old_path):
                    os.remove(old_path)

            # Update nama file di database
            o.gambar = filename

        # ===========================
        #  UPDATE FIELD LAIN
        # ===========================
        o.nama_obat = form.nama_obat.data
        o.golongan = form.golongan.data
        o.deskripsi = form.deskripsi.data
        o.indikasi = form.indikasi.data
        o.komposisi = form.komposisi.data
        o.dosis = form.dosis.data
        o.kontraindikasi = form.kontraindikasi.data
        o.efek_samping = form.efek_samping.data
        o.warning = form.warning.data
        o.harga = form.harga.data
        o.manufaktur = form.manufaktur.data
        o.kategori_kode = form.kategori_kode.data

        db.session.commit()
        return redirect(url_for('obat_index'))

    return render_template("admin/obat/edit.html", form=form, obat=o)


@app.route("/obat/delete/<string:kode>")
@login_required
def obat_delete(kode):
    o = Obat.query.get_or_404(kode)
    db.session.delete(o)
    db.session.commit()
    return redirect(url_for('obat_index'))


# ------------------------------------------
# CRUD RULE  (ID tetap)
# ------------------------------------------
@app.route("/rule")
@login_required
def rule_index():
    data = Rule.query.order_by(
        cast(func.substr(Rule.gejala_kode, 2), Integer)
    ).all()

    return render_template("admin/rule/index.html", data=data)


@app.route("/rule/create", methods=["GET", "POST"])
@login_required
def rule_create():
    form = RuleForm()

    # Isi pilihan gejala & kategori
    form.gejala_kode.choices = [(g.kode, g.nama_gejala) for g in Gejala.query.all()]
    form.kategori_list.choices = [(k.kode, k.nama_kategori) for k in KategoriObat.query.all()]

    if form.validate_on_submit():

        # Ambil kategori terpilih: list
        selected = form.kategori_list.data   # contoh: ["O01", "O05", "O28"]

        # Simpan ke database dalam format CSV
        kategori_csv = ",".join(selected)

        new_rule = Rule(
            gejala_kode=form.gejala_kode.data,
            kategori_list=kategori_csv,
            nilai_kepercayaan=form.nilai_kepercayaan.data
        )

        db.session.add(new_rule)
        db.session.commit()

        return redirect(url_for("rule_index"))

    return render_template("admin/rule/create.html", form=form)

@app.route('/rule/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def rule_edit(id):
    r = Rule.query.get_or_404(id)
    form = RuleForm()

    # isi pilihan dropdown
    form.gejala_kode.choices = [(g.kode, g.nama_gejala) for g in Gejala.query.all()]
    form.kategori_list.choices = [(k.kode, k.nama_kategori) for k in KategoriObat.query.all()]

    # ---- GET (initial load form) ----
    if request.method == "GET":
        form.gejala_kode.data = r.gejala_kode

        # jika kategori_list ada isinya → split
        if r.kategori_list:
            form.kategori_list.data = r.kategori_list.split(",")
        else:
            form.kategori_list.data = []

        form.nilai_kepercayaan.data = r.nilai_kepercayaan

    # ---- POST (submit form) ----
    if form.validate_on_submit():

        r.gejala_kode = form.gejala_kode.data

        # Ambil semua kategori yang dicentang
        selected = form.kategori_list.data or []
        r.kategori_list = ",".join(selected)

        r.nilai_kepercayaan = form.nilai_kepercayaan.data

        db.session.commit()
        return redirect(url_for("rule_index"))

    return render_template("admin/rule/edit.html", form=form)

@app.route("/rule/delete/<int:id>")
@login_required
def rule_delete(id):
    r = Rule.query.get_or_404(id)
    db.session.delete(r)
    db.session.commit()
    return redirect(url_for('rule_index'))

# ------------------------------------------
# KONSULTASI (USER)
# ------------------------------------------

@app.route("/konsultasi")
def konsultasi():
    gejala = Gejala.query.all()     # ambil dari database
    return render_template("user/konsultasi.html", gejala=gejala)


# @app.route("/user/hasil", methods=["POST"])
# def hasil():
#     gejala_terpilih = request.form.getlist("gejala")

#     print("\n\n======================================")
#     print("===== HASIL PERHITUNGAN DIMULAI =====")
#     print("Gejala dipilih:", gejala_terpilih)
#     print("======================================\n")

#     # Ambil nama gejala
#     gejala_nama = []
#     for g in gejala_terpilih:
#         obj = Gejala.query.filter_by(kode=g).first()
#         if obj:
#             gejala_nama.append(obj.nama_gejala)

#     # =======================================
#     # CASE 0 → USER TIDAK MEMILIH GEJALA
#     # =======================================
#     if not gejala_terpilih:
#         print("❌ USER TIDAK MEMILIH GEJALA")
#         return render_template("user/hasil.html", gejala_terpilih=gejala_nama, obat_rekomendasi=[])

#     # ===================================
#     # CASE 1 → USER PILIH HANYA 1 GEJALA
#     # ===================================
#     if len(gejala_terpilih) == 1:
#         kode = gejala_terpilih[0]
#         print("\n=== CASE 1 (1 GEJALA) ===")
#         print("GEJALA:", kode)

#         rule = Rule.query.filter_by(gejala_kode=kode).first()

#         if not rule:
#             print("⚠️ TIDAK ADA RULE UNTUK GEJALA INI")
#             return render_template("user/hasil.html", gejala_terpilih=gejala_nama, obat_rekomendasi=[])

#         kategori_set = rule.kategori_list.split(",")
#         print("KATEGORI:", kategori_set)

#         obat_rekomendasi = []
#         for kategori in kategori_set:
#             obat = Obat.query.filter_by(kategori_kode=kategori).all()
#             print(f"OBAT DARI {kategori}:", [o.nama_obat for o in obat])
#             obat_rekomendasi.extend(obat)

#         print("\n=== OBAT FINAL CASE 1 ===")
#         print([o.nama_obat for o in obat_rekomendasi])

#         return render_template("user/hasil.html", gejala_terpilih=gejala_nama, obat_rekomendasi=obat_rekomendasi)

#     # ===================================
#     # CASE 2 → MULTI GEJALA (DEMPSTER)
#     # ===================================
#     print("\n=== CASE 2 (MULTI GEJALA) ===")

#     all_mass = []

#     for kode in gejala_terpilih:
#         rule = Rule.query.filter_by(gejala_kode=kode).first()

#         print("\n------------------------------")
#         print("GEJALA:", kode)

#         if not rule:
#             print("⚠️ TIDAK ADA RULE UNTUK GEJALA INI")
#             continue

#         print("RULE:", rule.kategori_list, rule.nilai_kepercayaan)

#         # Mass function
#         mass = {}

#         kategori_label = rule.kategori_list  # contoh: 'O01,O05,O28'
#         nilai = rule.nilai_kepercayaan

#         mass[kategori_label] = nilai

#         if nilai < 1:
#             mass["Θ"] = 1 - nilai

#         print("MASS FUNCTION:", mass)
#         all_mass.append(mass)

#     if not all_mass:
#         print("❌ TIDAK ADA MASS FUNCTION TERBENTUK (SEMUA RULE KOSONG)")
#         return render_template("user/hasil.html", gejala_terpilih=gejala_nama, obat_rekomendasi=[])

#     print("\n\n=== MULAI KOMBINASI DEMPSTER ===")
#     hasil_akhir = hitung_dempster(all_mass)

#     print("\nHASIL AKHIR DEMPSTER (RAW):")
#     print(hasil_akhir)

#     # Bersihkan Θ
#     if "Θ" in hasil_akhir:
#         del hasil_akhir["Θ"]

#     print("\nHASIL TANPA Θ:")
#     print(hasil_akhir)

#     if not hasil_akhir:
#         print("❌ HASIL KOSONG SETELAH HAPUS Θ")
#         return render_template("user/hasil.html", gejala_terpilih=gejala_nama, obat_rekomendasi=[])

#     # Ranking
#     ranking = sorted(hasil_akhir.items(), key=lambda x: x[1], reverse=True)

#     print("\n=== RANKING KATEGORI ===")
#     for kategori, nilai in ranking:
#         print(f"{kategori}: {nilai:.4f}")

#     kategori_top = ranking[0][0]
#     print("\nKATEGORI TERPILIH:", kategori_top)

#     kategori_list = kategori_top.split(",")

#     # Ambil obat
#     obat_rekomendasi = []
#     print("\n=== AMBIL OBAT DARI KATEGORI ===")

#     for kategori in kategori_list:
#         obat = Obat.query.filter_by(kategori_kode=kategori).all()
#         print(f"{kategori}:", [o.nama_obat for o in obat])
#         obat_rekomendasi.extend(obat)

#     print("\n=== OBAT REKOMENDASI AKHIR ===")
#     print([o.nama_obat for o in obat_rekomendasi])

#     print("\n===== SELESAI =====\n\n")

#     return render_template("user/hasil.html", gejala_terpilih=gejala_nama, obat_rekomendasi=obat_rekomendasi)

@app.route("/user/hasil", methods=["POST"])
def hasil():
    gejala_terpilih = request.form.getlist("gejala")

    print("\n\n======================================")
    print("===== HASIL PERHITUNGAN DIMULAI =====")
    print("Gejala dipilih:", gejala_terpilih)
    print("======================================\n")

    # Ambil nama gejala
    gejala_nama = []
    for g in gejala_terpilih:
        obj = Gejala.query.filter_by(kode=g).first()
        if obj:
            gejala_nama.append(obj.nama_gejala)

    # =======================================
    # CASE 0 → USER TIDAK MEMILIH GEJALA
    # =======================================
    if not gejala_terpilih:
        print("❌ USER TIDAK MEMILIH GEJALA")
        return render_template(
            "user/hasil.html",
            gejala_terpilih=gejala_nama,
            obat_rekomendasi=[],
            pesan="Tidak ada gejala yang dipilih."
        )

    # ===================================
    # CASE 1 → HANYA 1 GEJALA
    # ===================================
    if len(gejala_terpilih) == 1:
        kode = gejala_terpilih[0]
        print("\n=== CASE 1 (1 GEJALA) ===")
        print("GEJALA:", kode)

        rule = Rule.query.filter_by(gejala_kode=kode).first()

        if not rule:
            print("⚠️ TIDAK ADA RULE UNTUK GEJALA INI")
            return render_template(
                "user/hasil.html",
                gejala_terpilih=gejala_nama,
                obat_rekomendasi=[],
                pesan="Tidak ada rekomendasi obat untuk gejala ini."
            )

        kategori_set = rule.kategori_list.split(",")
        print("KATEGORI:", kategori_set)

        obat_rekomendasi = []
        for kategori in kategori_set:
            obat = Obat.query.filter_by(kategori_kode=kategori).all()
            print(f"OBAT DARI {kategori}:", [o.nama_obat for o in obat])
            obat_rekomendasi.extend(obat)

        print("\n=== OBAT FINAL CASE 1 ===")
        print([o.nama_obat for o in obat_rekomendasi])

        return render_template(
            "user/hasil.html",
            gejala_terpilih=gejala_nama,
            obat_rekomendasi=obat_rekomendasi
        )

    # ===================================
    # CASE 2 → MULTI GEJALA (DEMPSTER)
    # ===================================
    print("\n=== CASE 2 (MULTI GEJALA) ===")

    all_mass = []

    for kode in gejala_terpilih:
        rule = Rule.query.filter_by(gejala_kode=kode).first()

        print("\n------------------------------")
        print("GEJALA:", kode)

        if not rule:
            print("⚠️ TIDAK ADA RULE UNTUK GEJALA INI")
            continue

        print("RULE:", rule.kategori_list, rule.nilai_kepercayaan)

        mass = {}
        kategori_label = rule.kategori_list
        nilai = rule.nilai_kepercayaan

        mass[kategori_label] = nilai

        if nilai < 1:
            mass["Θ"] = 1 - nilai

        print("MASS FUNCTION:", mass)
        all_mass.append(mass)

    if not all_mass:
        print("❌ TIDAK ADA MASS FUNCTION TERBENTUK")
        return render_template(
            "user/hasil.html",
            gejala_terpilih=gejala_nama,
            obat_rekomendasi=[],
            pesan="Tidak ada kecocokan aturan untuk kombinasi gejala tersebut."
        )

    print("\n\n=== MULAI KOMBINASI DEMPSTER ===")
    hasil_akhir = hitung_dempster(all_mass)

    print("\nHASIL AKHIR DEMPSTER (RAW):")
    print(hasil_akhir)

    if "Θ" in hasil_akhir:
        del hasil_akhir["Θ"]

    print("\nHASIL TANPA Θ:")
    print(hasil_akhir)

    if not hasil_akhir:
        print("❌ HASIL KOSONG SETELAH HAPUS Θ")
        return render_template(
            "user/hasil.html",
            gejala_terpilih=gejala_nama,
            obat_rekomendasi=[],
            pesan="Tidak ada keyakinan yang cukup untuk memberi rekomendasi obat."
        )

    # ============================================
    # 🔥 ITEM-LEVEL SCORING → PILIH 1 KATEGORI
    # ============================================
    print("\n=== ITEM-LEVEL SCORING (MEMILIH 1 KATEGORI TERKUAT) ===")

    item_score = {}

    for label, bobot in hasil_akhir.items():
        kategori_list = label.split(",")
        for kategori in kategori_list:
            item_score[kategori] = item_score.get(kategori, 0) + bobot

    print("ITEM SCORE:")
    for k, v in item_score.items():
        print(f"{k}: {v:.4f}")

    total_score = sum(item_score.values())
    max_kategori, max_score = max(item_score.items(), key=lambda x: x[1])

    print(f"\nTOTAL SCORE : {total_score:.4f}")
    print(f"MAX SCORE   : {max_kategori} = {max_score:.4f}")

    # ================================
    # ⚠️ DETEKSI GEJALA ABSTRAK / RANDOM
    # ================================
    if total_score == 0 or max_score < 0.5:
        print("\n❌ EVIDENCE LEMAH → GEJALA TERLALU ABSTRAK")
        return render_template(
            "user/hasil.html",
            gejala_terpilih=gejala_nama,
            obat_rekomendasi=[],
            pesan="Tidak ada rekomendasi obat. Gejala terlalu umum atau tidak saling berkaitan."
        )

    # LOLOS → pilih kategori_final
    kategori_final = max_kategori
    print("\nKATEGORI TERPILIH FINAL (TUNGGAL):", kategori_final)

    # ============================================
    # AMBIL OBAT DARI 1 KATEGORI FINAL
    # ============================================
    print("\n=== AMBIL OBAT DARI KATEGORI FINAL ===")

    obat_rekomendasi = Obat.query.filter_by(kategori_kode=kategori_final).all()

    print("OBAT:", [o.nama_obat for o in obat_rekomendasi])

    print("\n===== SELESAI =====\n\n")

    return render_template(
        "user/hasil.html",
        gejala_terpilih=gejala_nama,
        obat_rekomendasi=obat_rekomendasi
    )

# ------------------------------------------
# FUNGSI PROSES DEMPSTER-SHAFER
# ------------------------------------------
# def proses_dempster_shafer(selected_gejala):
#     """
#     selected_gejala = list berisi kode gejala ['G01','G03', ...]
#     Return: list rekomendasi obat (diurutkan berdasarkan nilai keyakinan)
#     """

#     # 1. Ambil rule berdasarkan gejala yang dipilih
#     rules = Rule.query.filter(Rule.gejala_kode.in_(selected_gejala)).all()

#     if not rules:
#         return []

#     # 2. Buat mass function awal dari setiap rule
#     mass_list = []
#     for r in rules:
#         for d in r.details:
#             mass_list.append({
#                 "kategori": d.kategori_kode,
#                 "belief": d.nilai_kepercayaan
#             })

#     # 3. Jika user mau nanti bisa saya isi rumus DS lengkap.
#     # Untuk sekarang dummy dulu:
#     hasil = {m["kategori"]: m["belief"] for m in mass_list}

#     # Sort terbesar
#     sorted_hasil = sorted(hasil.items(), key=lambda x: x[1], reverse=True)

#     # 4. Ambil obat berdasarkan kategori tertinggi
#     rekomendasi_obat = []
#     for kategori, nilai in sorted_hasil:
#         obat = Obat.query.filter_by(kategori_kode=kategori).all()
#         for o in obat:
#             rekomendasi_obat.append({
#                 "obat": o,
#                 "kategori": kategori,
#                 "nilai": nilai
#             })

#     return rekomendasi_obat





# ------------------------------------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
