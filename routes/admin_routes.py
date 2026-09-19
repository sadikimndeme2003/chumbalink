from flask import Blueprint, render_template, request, redirect, url_for, flash
from extensions.supabase_client import get_supabase
from utils.auth_utils import role_required

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/")
@role_required("admin")
def dashboard():
    sb = get_supabase()
    pending = (
        sb.table("requests").select("*", count="exact").eq("status", "pending").execute()
    )
    rooms_available = (
        sb.table("rooms").select("*", count="exact").eq("status", "available").execute()
    )
    rooms_booked = (
        sb.table("rooms").select("*", count="exact").eq("status", "booked").execute()
    )
    rooms_archived = (
        sb.table("rooms").select("*", count="exact").eq("status", "archived").execute()
    )
    return render_template(
        "admin/dashboard.html",
        pending_count=pending.count or 0,
        available_count=rooms_available.count or 0,
        booked_count=rooms_booked.count or 0,
        archived_count=rooms_archived.count or 0,
    )


@admin_bp.route("/rooms")
@role_required("admin")
def rooms_list():
    """
    Vyumba vyote (available/requested/pending_payment/booked/archived).
    'archived' ndiyo vyumba vilivyoshakamilika/kuchukuliwa -- vimetolewa
    kwenye orodha ya umma lakini bado vinaonekana hapa kwa historia.
    """
    sb = get_supabase()

    status_filter = request.args.get("status", "").strip()
    query = sb.table("rooms").select("*")
    if status_filter:
        query = query.eq("status", status_filter)

    rooms = query.order("created_at", desc=True).execute().data or []

    for room in rooms:
        room["owner_info"] = None
        if room.get("owner_id"):
            try:
                user_res = sb.auth.admin.get_user_by_id(room["owner_id"])
                meta = user_res.user.user_metadata or {}
                room["owner_info"] = {
                    "full_name": meta.get("full_name", user_res.user.email),
                    "phone": meta.get("phone", ""),
                }
            except Exception:
                pass

    return render_template("admin/rooms.html", rooms=rooms, status_filter=status_filter)


@admin_bp.route("/requests")
@role_required("admin")
def requests_list():
    sb = get_supabase()
    reqs = (
        sb.table("requests")
        .select("*, rooms(title, area, price, contact_phone)")
        .order("created_at", desc=True)
        .execute()
        .data
        or []
    )

    # Hakuna jedwali letu la "users" -- taarifa za mteja (jina/simu) zinatoka
    # moja kwa moja kwenye Supabase Auth (auth.users) kwa kila ombi.
    for r in reqs:
        r["client_info"] = None
        if r.get("client_id"):
            try:
                user_res = sb.auth.admin.get_user_by_id(r["client_id"])
                meta = user_res.user.user_metadata or {}
                r["client_info"] = {
                    "full_name": meta.get("full_name", user_res.user.email),
                    "phone": meta.get("phone", ""),
                }
            except Exception:
                pass

    return render_template("admin/requests.html", requests=reqs)


@admin_bp.route("/requests/<request_id>/status", methods=["POST"])
@role_required("admin")
def update_status(request_id):
    """
    Admin ndiye anayebadilisha hali ya ombi mkono kwa mkono, baada ya
    kuzungumza na mteja na mwenye nyumba nje ya mfumo (simu/WhatsApp):

    pending -> connected (admin ameunganisha mteja na mwenye nyumba)
             -> payment_in_progress (mteja anaelekea kulipa kwa mwenye nyumba,
                akiwa ameshuhudiwa na admin)
             -> booked (malipo yamekamilika, chumba kimechukuliwa)
             -> cancelled (mteja au mwenye nyumba wamejitoa)

    Chumba kinapofikia 'booked', kinaondolewa kwenye orodha ya umma
    (status ya room inakuwa 'archived').
    """
    sb = get_supabase()
    new_status = request.form.get("status")
    admin_notes = request.form.get("admin_notes", "").strip()

    valid_statuses = ["pending", "connected", "payment_in_progress", "booked", "cancelled"]
    if new_status not in valid_statuses:
        flash("Hali isiyotambulika.", "error")
        return redirect(url_for("admin.requests_list"))

    req_res = sb.table("requests").select("*").eq("id", request_id).limit(1).execute()
    if not req_res.data:
        flash("Ombi halikupatikana.", "error")
        return redirect(url_for("admin.requests_list"))

    req = req_res.data[0]

    update_data = {"status": new_status}
    if admin_notes:
        update_data["admin_notes"] = admin_notes
    sb.table("requests").update(update_data).eq("id", request_id).execute()

    if req.get("room_id"):
        if new_status == "booked":
            # Chumba kimechukuliwa -> kinaondoka kabisa kwenye orodha ya umma
            sb.table("rooms").update({"status": "archived"}).eq("id", req["room_id"]).execute()
        elif new_status == "cancelled":
            # Ombi limekufa -> chumba kinarudi sokoni
            sb.table("rooms").update({"status": "available"}).eq("id", req["room_id"]).execute()

    flash("Hali ya ombi imesasishwa.", "success")
    return redirect(url_for("admin.requests_list"))
