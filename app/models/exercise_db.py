from app import db


class ExerciseDB(db.Model):
    __tablename__ = "exercise_db"

    id = db.Column(db.Integer, primary_key=True)
    kategori = db.Column(db.String(50), nullable=True)
    nama_latihan = db.Column(db.String(150), nullable=False)
    target_otot = db.Column(db.String(150), nullable=True)
    peralatan = db.Column(db.String(100), nullable=True)
    tipe = db.Column(db.String(50), nullable=True)
    deskripsi_singkat = db.Column(db.Text, nullable=True)
    cns_cluster = db.Column(db.String(1), nullable=False, default="B")  # A/B/C

    def __repr__(self):
        return f"<ExerciseDB {self.nama_latihan} ({self.cns_cluster})>"
