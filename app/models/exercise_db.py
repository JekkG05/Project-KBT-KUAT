class ExerciseDB:

    def __init__(self, data):

        self.id = data.get("id")

        self.kategori = data.get(
            "kategori"
        )

        self.nama_latihan = data.get(
            "nama_latihan"
        )

        self.target_otot = data.get(
            "target_otot"
        )

        self.peralatan = data.get(
            "peralatan"
        )

        self.tipe = data.get(
            "tipe"
        )

        self.deskripsi_singkat = data.get(
            "deskripsi_singkat"
        )

        self.cns_cluster = data.get(
            "cns_cluster",
            "B"
        )


    def __repr__(self):

        return (
            f"<ExerciseDB "
            f"{self.nama_latihan} "
            f"({self.cns_cluster})>"
        )
