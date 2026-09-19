from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from extensions.supabase_client import get_supabase
from utils.auth_utils import role_required
from utils.validation import validate_price, validate_distance, validate_text_len

request_bp = Blueprint("request", __name__)


@request_bp.route("/room/<room_id>", methods=["POST"])
@role_required("client")
def request_room(room_id):
    sb = get_supabase()

    room_res = sb.table("rooms").select("*").eq("id", room_id).limit(1).execute()
    if not room_res.data:
        flash("Chumba hiki hakipo tena.", "error")
        return redirect(url_for("main.browse"))

    room = room_res.data[0]
    if room["status"] != "available":
        flash("Samahani, chumba hiki kimeshaombwa na mteja mwingine.", "error")
        return redirect(url_for("main.room_detail", room_id=room_id))

    sb.table("requests").insert({
        "request_type": "room_request",
        "room_id": room_id,
        "client_id": session["user_id"],
        "owner_id": room["owner_id"],
        "status": "pending",
    }).execute()

    sb.table("rooms").update({"status": "requested"}).eq("id", room_id).execute()

    flash(
        "Ombi lako limetumwa. Msimamizi (admin) atawasiliana nawe hivi karibuni "
        "kukuunganisha na mwenye chumba.",
        "success",
    )
    return redirect(url_for("main.room_detail", room_id=room_id))


@request_bp.route("/new", methods=["GET", "POST"])
@role_required("client")
def custom_request():
    if request.method == "POST":
        sb = get_supabase()

        desired_area = request.form.get("desired_area", "").strip()
        desired_distance = request.form.get("desired_distance", "").strip()
        desired_room_type = request.form.get("desired_room_type", "").strip()
        desired_price = request.form.get("desired_price", "").strip()
        notes = request.form.get("notes", "").strip()

        if not desired_area:
            flash("Tafadhali taja eneo unalotaka.", "error")
            return render_template("request_room_form.html")

        distance_val, distance_err = validate_distance(desired_distance, required=False)
        if distance_err:
            flash(distance_err, "error")
            return render_template("request_room_form.html")

        price_val, price_err = validate_price(desired_price, required=False)
        if price_err:
            flash(price_err, "error")
            return render_template("request_room_form.html")

        notes_err = validate_text_len(notes, "Maelezo")
        if notes_err:
            flash(notes_err, "error")
            return render_template("request_room_form.html")

        sb.table("requests").insert({
            "request_type": "custom_request",
            "client_id": session["user_id"],
            "desired_area": desired_area,
            "desired_distance": distance_val,
            "desired_room_type": desired_room_type or None,
            "desired_price": price_val,
            "notes": notes,
            "status": "pending",
        }).execute()

        flash("Ombi lako limepokelewa. Tutakutafutia chumba kinachofaa.", "success")
        return redirect(url_for("request.my_requests"))

    return render_template("request_room_form.html")


@request_bp.route("/mine")
@role_required("client")
def my_requests():
    sb = get_supabase()
    reqs = (
        sb.table("requests")
        .select("*, rooms(title, area, price)")
        .eq("client_id", session["user_id"])
        .order("created_at", desc=True)
        .execute()
        .data
        or []
    )
    return render_template("my_requests.html", requests=reqs)
