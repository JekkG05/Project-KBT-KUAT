# KUAT. — Keep Up Adaptive Training

Aplikasi web analitik latihan kekuatan berbasis Flask (MVC) + Supabase PostgreSQL.
Asisten pelatih virtual berbasis sport science: mencatat beban, menghitung volume,
tonnage, estimasi 1RM, fatigue/CNS fatigue, ACWR, dan Early Warning System (khusus premium)
dari pola RIR/RPE pribadi pengguna.

## Struktur Proyek

```
KUAT_APP/
├── app/
│   ├── models/        # SQLAlchemy models (User, ExerciseDB, WorkoutPlan, ...)
│   ├── controllers/    # Flask blueprints (auth, home, exercise, routine, train)
│   ├── services/        # Engine deterministik (gap_patch, kuat_engine, chart_generator)
│   ├── static/          # CSS & JS
│   └── templates/       # HTML (Jinja2)
├── run.py
├── requirements.txt
└── .env.example
```

## 1. Persiapan Lingkungan

```bash
python -m venv venv
```

Windows (CMD):
```bash
venv\Scripts\activate
```

Windows (PowerShell):
```powershell
.\venv\Scripts\Activate.ps1
```

macOS / Linux:
```bash
source venv/bin/activate
```

## 2. Install Dependencies

```bash
pip install -r requirements.txt
```

## 3. Konfigurasi Environment

Windows:
```bash
copy .env.example .env
```

macOS / Linux:
```bash
cp .env.example .env
```

Lalu isi `.env`:

```env
SECRET_KEY=ganti-dengan-secret-key-acak
SUPABASE_DB_URL=postgresql+psycopg2://postgres:PASSWORD_ANDA@db.PROJECT_ANDA.supabase.co:5432/postgres?sslmode=require
```

### Cara mendapatkan SUPABASE_DB_URL:

1. Buka project Anda di [supabase.com](https://supabase.com).
2. Masuk ke **Project Settings → Database**.
3. Salin **Connection string** (mode "URI", bukan "pooler" jika ingin koneksi langsung).
4. Sesuaikan formatnya menjadi `postgresql+psycopg2://...` (tambahkan `+psycopg2` setelah `postgresql`).
5. Tempelkan ke `SUPABASE_DB_URL` di file `.env`.

## 4. Jalankan Aplikasi

```bash
python run.py
```

Saat pertama kali dijalankan:
- Semua tabel otomatis dibuat lewat `db.create_all()`.
- Tabel `exercise_db` otomatis di-seed dari `app/services/clustering.csv` (68 gerakan).
- Jika `SUPABASE_DB_URL` belum diatur atau tidak valid, terminal akan menampilkan
  pesan error yang jelas — perbaiki `.env` lalu jalankan ulang.

Buka browser ke: `http://127.0.0.1:5000`

## 5. Alur Pemakaian

1. **Sign Up** (3 langkah): Akun → Data Diri → Target Angkatan & Tier.
2. **Login**.
3. Buat **Routine** baru di halaman **Exercise**, tambahkan exercise (sets/reps/kg target).
4. Buka **Routines** untuk melihat semua folder & recent workout.
5. Klik **TRAIN** untuk memulai sesi: input beban aktual, reps aktual, dan slider **RIR (0–5)**.
   RIR otomatis dikonversi menjadi RPE (`RPE = 10 - RIR`, dibatasi 5–10).
6. Setiap **DONE SET** akan:
   - Menghitung volume, estimasi 1RM (Epley), fatigue total, CNS fatigue, ACWR, dan FSM state.
   - **User Premium**: menerima peringatan (⚠️ WARNING / 🚨 DANGER) bila pola set menyimpang
     signifikan dari rata-rata historis pribadinya.
   - **User Free**: tidak menerima peringatan apapun (`warnings = []`), walau engine tetap
     menghitung statistik di balik layar.

## Catatan Sport Science

> KUAT membantu estimasi beban latihan dan memberi sinyal kehati-hatian berbasis data
> latihan pribadi. Ini bukan pengganti diagnosis medis atau pelatih profesional.

## Batasan Teknis (sesuai desain)

- Tidak ada field atau perhitungan berbasis BPM/denyut jantung di manapun.
- Tidak ada penggunaan `random()` — seluruh perhitungan deterministik dari input
  pengguna dan riwayat data (`app/services/gap_patch.py`, `app/services/kuat_engine.py`).
- Arsitektur MVC: Model (`app/models`), Controller (`app/controllers`), Service/Engine
  layer (`app/services`), View (`app/templates`).
