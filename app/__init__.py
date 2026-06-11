from flask import Flask, send_from_directory
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from flask import Flask
from flask_cors import CORS 


def create_app():
    app = Flask(__name__)
    base_dir = Path(__file__).resolve().parent.parent
    app.config["SECRET_KEY"]     = os.getenv("SECRET_KEY", "change-me-in-production")
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "jwt-secret-change-me")
    app.config["JWT_EXP_SECONDS"]= int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES", 86400))

    # CORS — graceful if flask-cors absent
    try:
        from flask_cors import CORS as _CORS
        _CORS(app, resources={r"/api/*": {"origins": "*"}})
    except ImportError:
        @app.after_request
        def _cors(r):
            r.headers["Access-Control-Allow-Origin"]  = "*"
            r.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
            r.headers["Access-Control-Allow-Methods"] = "GET,POST,PUT,DELETE,OPTIONS"
            return r

    # Init DB
    from app.db import init_db
    with app.app_context():
        init_db()

    # Blueprints
    from app.routes.auth           import auth_bp
    from app.routes.calculator     import calc_bp
    from app.routes.tracking       import track_bp
    from app.routes.dashboard      import dash_bp
    from app.routes.goals          import goals_bp
    from app.routes.recommendations import recs_bp
    from app.routes.leaderboard    import lb_bp
    from app.routes.offset         import offset_bp
    from app.routes.prediction     import pred_bp
    from app.routes.reports        import reports_bp

    app.register_blueprint(auth_bp,   url_prefix="/api/auth")
    app.register_blueprint(calc_bp,   url_prefix="/api/calculator")
    app.register_blueprint(track_bp,  url_prefix="/api/tracking")
    app.register_blueprint(dash_bp,   url_prefix="/api/dashboard")
    app.register_blueprint(goals_bp,  url_prefix="/api/goals")
    app.register_blueprint(recs_bp,   url_prefix="/api/recommendations")
    app.register_blueprint(lb_bp,     url_prefix="/api/leaderboard")
    app.register_blueprint(offset_bp, url_prefix="/api/offset")
    app.register_blueprint(pred_bp,   url_prefix="/api/prediction")
    app.register_blueprint(reports_bp,url_prefix="/api/reports")

    @app.route("/")
    def index():
        return send_from_directory(base_dir, "index.html")

    @app.route("/api/health")
    def health():
        return {"status": "ok", "service": "EcoTrace API", "version": "1.0.0"}

    @app.route("/api/health", methods=["OPTIONS"])
    def health_opts():
        return "", 204

    return app
