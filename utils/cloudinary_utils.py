"""
Kihifadhi cha picha/video kupitia Cloudinary (free tier: ~25GB storage,
25GB bandwidth kwa mwezi -- inatosha kuanzia).

Kwa nini Cloudinary badala ya kuhifadhi faili moja kwa moja kwenye
Vercel: Vercel serverless functions hazina disk ya kudumu (kila
request inaweza kuja kwenye server tofauti), kwa hiyo picha/video
LAZIMA zihifadhiwe mahali pa nje (Cloudinary / Supabase Storage).
"""
import os
import cloudinary
import cloudinary.uploader

_configured = False


def _configure():
    global _configured
    if not _configured:
        cloudinary.config(
            cloud_name=os.environ.get("CLOUDINARY_CLOUD_NAME"),
            api_key=os.environ.get("CLOUDINARY_API_KEY"),
            api_secret=os.environ.get("CLOUDINARY_API_SECRET"),
            secure=True,
        )
        _configured = True


def upload_room_media(file_storage, room_id, resource_type="image"):
    """
    file_storage: werkzeug FileStorage (kutoka request.files)
    resource_type: "image" au "video"
    Returns dict: {"url": ..., "public_id": ..., "type": resource_type}
    """
    _configure()
    result = cloudinary.uploader.upload(
        file_storage,
        folder=f"vyumba/{room_id}",
        resource_type=resource_type,
        # video kubwa zinabanwa kiasi ili zisitumie bandwidth nyingi kwenye free tier
        eager=[{"quality": "auto"}] if resource_type == "image" else None,
    )
    return {
        "url": result.get("secure_url"),
        "public_id": result.get("public_id"),
        "type": resource_type,
    }


def delete_room_media(public_id, resource_type="image"):
    _configure()
    cloudinary.uploader.destroy(public_id, resource_type=resource_type)
