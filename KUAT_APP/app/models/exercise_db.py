from app import db


class ExerciseDB(db.Model):
    __tablename__ = "exercise_db"

    id = db.Column(db.Integer, primary_key=True)
    nama_latihan = db.Column(db.String(160), nullable=False, index=True)
    target_otot = db.Column(db.String(120), nullable=False)
    peralatan = db.Column(db.String(80), nullable=False)
    tipe = db.Column(db.String(80), nullable=False)
    cns_cluster = db.Column(db.String(1), nullable=False, index=True)

    # Kolom tambahan dari CSV agar kartu exercise lebih informatif.
    kategori = db.Column(db.String(80), nullable=True)
    deskripsi = db.Column(db.Text, nullable=True)
