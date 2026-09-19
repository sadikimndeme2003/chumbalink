import os
from dotenv import load_dotenv
from flask import Flask
from flask_wtf import CSRFProtect
from config import Config

load_dotenv()

csrf = CSRFProtect()


def create_app():
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config.from_object(Config)

    # --- Usalama wa session cookie ---
    app.config["SESSION_COOKIE_HTTPONLY"] = True   # JS haiwezi kusoma cookie ya session
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"  # kinga dhidi ya CSRF ya msingi
    app.config["SESSION_COOKIE_SECURE"] = os.environ.get("FLASK_ENV") != "development"
    # ^ Vercel ni HTTPS kila wakati, hivyo True kwa default; tunaiacha False tu
    #   ukiwa unaendesha localhost bila HTTPS (FLASK_ENV=development kwenye .env).

    csrf.init_app(app)

    from routes.auth_routes import auth_bp
    from routes.main_routes import main_bp
    from routes.room_routes import room_bp
    from routes.request_routes import request_bp
    from routes.admin_routes import admin_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(main_bp, url_prefix="/")
    app.register_blueprint(room_bp, url_prefix="/rooms")
    app.register_blueprint(request_bp, url_prefix="/requests")
    app.register_blueprint(admin_bp, url_prefix="/admin")

    @app.context_processor
    def inject_helpers():
        from utils.auth_utils import current_user
        return {"current_user": current_user()}

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
