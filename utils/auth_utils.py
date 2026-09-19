from functools import wraps
from flask import session, redirect, url_for, flash, request


def current_user():
    """Inarudisha dict rahisi ya mtumiaji aliye-login kutoka session, au None.

    Chanzo cha ukweli ni Supabase Auth (auth.users) -- session hii ya Flask
    ni nakala nyepesi tu ya kile Supabase kilichorudisha wakati wa login,
    ili tusihitaji kupiga Supabase kwa kila request.
    """
    if "user_id" not in session:
        return None
    return {
        "id": session.get("user_id"),
        "full_name": session.get("full_name"),
        "email": session.get("email"),
        "role": session.get("role"),
    }


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Tafadhali ingia kwenye akaunti yako kwanza.", "error")
            return redirect(url_for("auth.login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


def role_required(*roles):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if "user_id" not in session:
                flash("Tafadhali ingia kwenye akaunti yako kwanza.", "error")
                return redirect(url_for("auth.login", next=request.path))
            if session.get("role") not in roles:
                flash("Huna ruhusa ya kufikia ukurasa huu.", "error")
                return redirect(url_for("main.browse"))
            return view(*args, **kwargs)
        return wrapped
    return decorator
