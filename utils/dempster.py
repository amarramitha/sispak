# =========================================================
#  DEMPSTER-SHAFER (FINAL FIXED VERSION)
#  - Mendukung kategori gabungan (O03,O07)
#  - Normalisasi benar
#  - Intersection himpunan benar
#  - Cocok dengan route hasil() kamu
# =========================================================


# ---------------------------------------------------------
# Helper: string kategori → set
# ---------------------------------------------------------
def to_set(label):
    """
    Convert label seperti 'O03' atau 'O03,O07' menjadi set.
    Θ dianggap universal set.
    """
    if label == "Θ":
        return set(["Θ"])
    return set(label.split(","))  # contoh: 'O03,O07' -> {'O03','O07'}


# ---------------------------------------------------------
# Helper: set → string kategori
# ---------------------------------------------------------
def from_set(s):
    """Convert set ke string label."""
    if s == set(["Θ"]):
        return "Θ"
    return ",".join(sorted(s))


# ---------------------------------------------------------
# Buat mass function dari RuleDetail
# ---------------------------------------------------------
def normalize_mass(details):
    if not details:
        return {}

    # kumpulkan semua kategori jadi satu himpunan
    kategori_set = set()
    for d in details:
        if d.kategori_kode:
            kategori_set.add(d.kategori_kode)

    if not kategori_set:
        return {}

    # ambil satu nilai kepercayaan saja (diasumsikan sama untuk semua baris)
    nilai = float(details[0].nilai_kepercayaan)

    mass = {}

    # gabungkan kategori jadi 1 label, misal: "O01,O02,O03"
    label = ",".join(sorted(kategori_set))
    mass[label] = nilai

    # sisa untuk Θ
    if nilai < 1:
        mass["Θ"] = 1 - nilai

    return mass


# ---------------------------------------------------------
# Combine dua mass function (HIMPUNAN YANG BENAR)
# ---------------------------------------------------------
def combine(m1, m2):
    """
    Implementasi Dempster-Shafer yang benar.
    BISA menghasilkan kategori gabungan seperti "O03,O07".
    """

    combined = {}
    K = 0  # konflik

    for A, v1 in m1.items():
        Aset = to_set(A)

        for B, v2 in m2.items():
            Bset = to_set(B)

            # Θ bersifat universal set
            if "Θ" in Aset and "Θ" in Bset:
                Cset = set(["Θ"])
            elif "Θ" in Aset:
                Cset = Bset
            elif "Θ" in Bset:
                Cset = Aset
            else:
                Cset = Aset.intersection(Bset)

            # Intersection kosong = KONFLIK
            if not Cset:
                K += v1 * v2
                continue

            C = from_set(Cset)
            combined[C] = combined.get(C, 0) + (v1 * v2)

    # Normalisasi
    if K < 1:
        for key in combined:
            combined[key] = combined[key] / (1 - K)

    return combined


# ---------------------------------------------------------
# Gabungkan mass function banyak gejala
# ---------------------------------------------------------
def hitung_dempster(list_mass):
    """
    Kombinasi berurutan:
        m = m1 ⊕ m2 ⊕ m3 ...
    """

    if not list_mass:
        return {}

    result = list_mass[0]

    for m in list_mass[1:]:
        result = combine(result, m)

    # Hapus Θ pada hasil final (boleh saja)
    if "Θ" in result:
        del result["Θ"]

    return result
