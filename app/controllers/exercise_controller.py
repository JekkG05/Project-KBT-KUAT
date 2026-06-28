from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user

from app.config import supabase
from app.models.workout_plan import WorkoutPlan


exercise_bp = Blueprint(
    "exercise",
    __name__,
    url_prefix="/exercise"
)



def _get_owned_plan_or_404(plan_id):

    result = (
        supabase
        .table("workout_plans")
        .select("*")
        .eq("id", plan_id)
        .eq("user_id", current_user.id)
        .single()
        .execute()
    )


    if not result.data:
        abort(404)


    return result.data




def _get_owned_item_or_404(item_id):

    result = (
        supabase
        .table("workout_plan_items")
        .select("*")
        .eq("id", item_id)
        .single()
        .execute()
    )


    item = result.data


    if not item:
        abort(404)



    plan = _get_owned_plan_or_404(
        item["plan_id"]
    )


    return item




@exercise_bp.route("/", methods=["GET"])
@login_required
def index():


    plans_result = (
        supabase
        .table("workout_plans")
        .select("*")
        .eq(
            "user_id",
            current_user.id
        )
        .order(
            "created_at",
            desc=True
        )
        .execute()
    )


    plans = [WorkoutPlan(row) for row in (plans_result.data or [])]



    exercises_result = (
        supabase
        .table("exercise_db")
        .select("*")
        .order(
            "nama_latihan"
        )
        .execute()
    )


    exercises = exercises_result.data or []



    active_plan_id = request.args.get(
        "plan_id",
        type=int
    )


    active_plan = None


    if active_plan_id:

        for p in plans:

            if p.id == active_plan_id:

                active_plan = p
                break



    if active_plan is None and plans:

        active_plan = plans[0]



    if active_plan is not None:

        items_result = (
            supabase
            .table("workout_plan_items")
            .select("*")
            .eq("plan_id", active_plan.id)
            .order("id")
            .execute()
        )

        active_plan.items = items_result.data or []


    return render_template(
        "exercise.html",
        plans=plans,
        exercises=exercises,
        active_plan=active_plan
    )





@exercise_bp.route("/create-plan", methods=["POST"])
@login_required
def create_plan():


    folder_name = (
        request.form.get("folder_name")
        or ""
    ).strip()


    train_focus = (
        request.form.get("train_focus")
        or ""
    ).strip()


    notes = (
        request.form.get("notes")
        or ""
    ).strip()



    if not folder_name:

        flash(
            "Title routine tidak boleh kosong.",
            "danger"
        )

        return redirect(
            url_for("exercise.index")
        )



    result = (
        supabase
        .table("workout_plans")
        .insert(
            {
                "user_id": current_user.id,
                "folder_name": folder_name,
                "train_focus": train_focus,
                "notes": notes
            }
        )
        .execute()
    )


    plan_id = result.data[0]["id"]



    flash(
        f"Routine '{folder_name}' berhasil dibuat.",
        "success"
    )


    return redirect(
        url_for(
            "exercise.index",
            plan_id=plan_id
        )
    )





@exercise_bp.route("/add-item/<int:plan_id>", methods=["POST"])
@login_required
def add_item(plan_id):


    plan = _get_owned_plan_or_404(
        plan_id
    )


    exercise_id = request.form.get(
        "exercise_id",
        type=int
    )


    target_sets = request.form.get(
        "target_sets",
        type=int
    ) or 3


    target_reps = request.form.get(
        "target_reps",
        type=int
    ) or 10


    target_weight = request.form.get(
        "target_weight",
        type=float
    ) or 0



    exercise_result = (
        supabase
        .table("exercise_db")
        .select("*")
        .eq(
            "id",
            exercise_id
        )
        .single()
        .execute()
    )


    exercise = exercise_result.data



    if not exercise:

        flash(
            "Pilih exercise yang valid.",
            "danger"
        )

        return redirect(
            url_for(
                "exercise.index",
                plan_id=plan_id
            )
        )



    supabase.table(
        "workout_plan_items"
    ).insert(
        {

            "plan_id": plan_id,

            "exercise_id": exercise["id"],

            "nama_gerakan": exercise["nama_latihan"],

            "cluster": exercise.get(
                "cns_cluster",
                "B"
            ),

            "target_sets": target_sets,

            "target_reps": target_reps,

            "target_weight": target_weight

        }

    ).execute()



    flash(
        f"{exercise['nama_latihan']} ditambahkan.",
        "success"
    )


    return redirect(
        url_for(
            "exercise.index",
            plan_id=plan_id
        )
    )





@exercise_bp.route("/edit-item/<int:item_id>", methods=["POST"])
@login_required
def edit_item(item_id):


    item = _get_owned_item_or_404(
        item_id
    )


    target_sets = request.form.get(
        "target_sets",
        type=int
    ) or item["target_sets"]


    target_reps = request.form.get(
        "target_reps",
        type=int
    ) or item["target_reps"]


    target_weight = request.form.get(
        "target_weight",
        type=float
    )

    if target_weight is None:
        target_weight = item["target_weight"]



    supabase.table(
        "workout_plan_items"
    ).update(
        {
            "target_sets": target_sets,
            "target_reps": target_reps,
            "target_weight": target_weight
        }
    ).eq(
        "id",
        item_id
    ).execute()



    flash(
        f"{item['nama_gerakan']} diperbarui.",
        "success"
    )


    return redirect(
        url_for(
            "exercise.index",
            plan_id=item["plan_id"]
        )
    )




@exercise_bp.route("/delete-item/<int:item_id>", methods=["POST"])
@login_required
def delete_item(item_id):


    item = _get_owned_item_or_404(
        item_id
    )


    # Lepas dulu relasi di workout_logs yang menunjuk ke item ini,
    # agar tidak melanggar foreign key constraint. Baris log-nya
    # sendiri TIDAK dihapus (riwayat latihan tetap tersimpan),
    # cuma referensi ke item-nya yang dikosongkan.
    supabase.table(
        "workout_logs"
    ).update(
        {
            "plan_item_id": None
        }
    ) \
    .eq(
        "plan_item_id",
        item_id
    ).execute()


    supabase.table(
        "workout_plan_items"
    ).delete() \
    .eq(
        "id",
        item_id
    ).execute()



    flash(
        f"{item['nama_gerakan']} dihapus.",
        "success"
    )


    return redirect(
        url_for(
            "exercise.index",
            plan_id=item["plan_id"]
        )
    )





@exercise_bp.route("/delete-plan/<int:plan_id>", methods=["POST"])
@login_required
def delete_plan(plan_id):


    plan = _get_owned_plan_or_404(
        plan_id
    )


    # Hapus dulu workout_logs yang masih menunjuk ke plan ini,
    # supaya tidak melanggar foreign key constraint saat
    # workout_plan_items / workout_plans dihapus di bawah.
    supabase.table(
        "workout_logs"
    ).delete() \
    .eq(
        "plan_id",
        plan_id
    ).execute()


    # Baru hapus item-item exercise di routine ini.
    supabase.table(
        "workout_plan_items"
    ).delete() \
    .eq(
        "plan_id",
        plan_id
    ).execute()


    # Terakhir, hapus plan-nya sendiri.
    supabase.table(
        "workout_plans"
    ).delete() \
    .eq(
        "id",
        plan_id
    ).execute()


    flash(
        f"Routine '{plan['folder_name']}' dihapus.",
        "success"
    )


    return redirect(
        url_for("exercise.index")
    )
