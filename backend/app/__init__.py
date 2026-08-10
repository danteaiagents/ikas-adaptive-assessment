from flask import Flask, jsonify
from app.config import Config
from app.extensions import db, jwt, cors, neo4j_ext
from werkzeug.exceptions import HTTPException

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    cors.init_app(app, supports_credentials=True, resources={r"/api/*": {"origins": app.config['CORS_ORIGINS']}})
    neo4j_ext.init_app(app)

    # Create tables in development
    with app.app_context():
        from app.models import db_models  # noqa: F401 — import models so db.create_all() sees them
        db.create_all()

    # Register Blueprints
    from app.api.v1 import bp as api_v1_bp
    app.register_blueprint(api_v1_bp, url_prefix='/api/v1')

    # Error Handling
    @app.errorhandler(Exception)
    def handle_exception(e):
        if isinstance(e, HTTPException):
            return jsonify({
                "success": False,
                "data": None,
                "error": {"code": e.code, "message": e.description},
                "meta": {}
            }), e.code
        return jsonify({
            "success": False,
            "data": None,
            "error": {"code": 500, "message": str(e)},
            "meta": {}
        }), 500

    @app.teardown_appcontext
    def teardown_db(exception):
        pass

    return app
