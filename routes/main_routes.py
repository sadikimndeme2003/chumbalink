from flask import Blueprint, render_template, request, jsonify, current_app
from extensions.supabase_client import get_supabase
from utils.phone import whatsapp_link, tel_link

main_bp = Blueprint("main", __name__)

PAGE_SIZE = 9  # vyumba vingapi kwa kila "ukurasa"


def _parse_filters(args):
    return {
        "area": args.get("area", "").strip(),
        "room_type": args.get("room_type", "").strip(),
        "max_price": args.get("max_price", "").strip(),
        "max_distance": args.get("max_distance", "").strip(),
    }


def _fetch_rooms(filters, page):
    """
    page ni 1-based. Tunachukua PAGE_SIZE + 1 rekodi ili kujua kama
    kuna ukurasa unaofuata, bila kuhitaji query ya pili ya kuhesabu (count).
    """
    sb = get_supabase()

    query = sb.table("rooms").select("*").eq("status", "available")

    if filters["area"]:
        query = query.ilike("area", f"%{filters['area']}%")
    if filters["room_type"]:
        query = query.eq("room_type", filters["room_type"])
    if filters["max_price"]:
        try:
            query = query.lte("price", float(filters["max_price"]))
        except ValueError:
            pass
    if filters["max_distance"]:
        try:
            query = query.lte("distance_to_college", float(filters["max_distance"]))
        except ValueError:
            pass

    start = (page - 1) * PAGE_SIZE
    end = start + PAGE_SIZE  # rekodi moja ya ziada kugundua "has_more"

    rooms = (
        query.order("created_at", desc=True)
        .range(start, end)
        .execute()
        .data
        or []
    )

    has_more = len(rooms) > PAGE_SIZE
    rooms = rooms[:PAGE_SIZE]

    for room in rooms:
        media = (
            sb.table("room_media")
            .select("url")
            .eq("room_id", room["id"])
            .eq("media_type", "image")
            .limit(1)
            .execute()
            .data
        )
        room["thumbnail"] = media[0]["url"] if media else None

    return rooms, has_more


@main_bp.route("/")
def home():
    """Landing page ya uuzaji -- inaeleza ChumbaLink ni nini na inafanya kazi vipi."""
    sb = get_supabase()

    all_rooms = sb.table("rooms").select("id, owner_id").execute().data or []
    completed_requests = (
        sb.table("requests").select("id", count="exact").eq("status", "booked").execute()
    )

    stats = {
        "rooms_count": len(all_rooms),
        "owners_count": len({r["owner_id"] for r in all_rooms if r.get("owner_id")}),
        "completed_count": completed_requests.count or 0,
    }

    latest_rooms, _ = _fetch_rooms(_parse_filters({}), page=1)
    latest_rooms = latest_rooms[:6]

    return render_template("landing.html", stats=stats, latest_rooms=latest_rooms)


@main_bp.route("/vyumba")
def browse():
    """Ukurasa wa kuvinjari/kuchuja vyumba (zamani ulikuwa kwenye '/')."""
    filters = _parse_filters(request.args)
    rooms, has_more = _fetch_rooms(filters, page=1)

    return render_template(
        "browse.html",
        rooms=rooms,
        filters=filters,
        has_more=has_more,
        next_page=2,
    )


@main_bp.route("/api/rooms")
def api_rooms():
    """Inatumika na 'Load More' kwenye home page (JavaScript fetch)."""
    filters = _parse_filters(request.args)
    try:
        page = int(request.args.get("page", 2))
    except ValueError:
        page = 2

    rooms, has_more = _fetch_rooms(filters, page=page)

    return jsonify({
        "rooms": rooms,
        "has_more": has_more,
        "next_page": page + 1,
    })


@main_bp.route("/room/<room_id>")
def room_detail(room_id):
    sb = get_supabase()
    room_res = sb.table("rooms").select("*").eq("id", room_id).limit(1).execute()
    if not room_res.data:
        return render_template("404.html"), 404

    room = room_res.data[0]
    media = sb.table("room_media").select("*").eq("room_id", room_id).execute().data or []
    room["images"] = [m for m in media if m["media_type"] == "image"]
    room["videos"] = [m for m in media if m["media_type"] == "video"]

    # Vitufe vya WhatsApp/Simu vinamwelekeza ADMIN (siyo mwenye nyumba) --
    # ndiye daraja pekee kati ya mteja na mwenye nyumba kwenye muundo wetu.
    admin_number = current_app.config.get("ADMIN_WHATSAPP_NUMBER", "")
    wa_message = f"Habari, nimeona chumba cha \"{room['title']}\" huko {room['area']} kwenye ChumbaLink. Naomba maelezo zaidi."
    room["whatsapp_url"] = whatsapp_link(admin_number, wa_message) if admin_number else None
    room["tel_url"] = tel_link(admin_number) if admin_number else None

    return render_template("room_detail.html", room=room)
