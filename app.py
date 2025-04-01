from flask import Flask, jsonify, send_from_directory
from config import Config
from extensions import db, migrate, cors
import logging
import os

# Import blueprints
from routes.students import students_bp
from routes.fees import fees_bp
from routes.expenses import expenses_bp, initialize_categories
from routes.bulk_upload import bulk_upload_bp
from routes.dashboard import dashboard_bp
from routes.reports import reports_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Set up logging
    logging.basicConfig(level=app.config["LOG_LEVEL"])

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True,
                  methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])

    # Register blueprints
    app.register_blueprint(students_bp, url_prefix="/api/students")
    app.register_blueprint(fees_bp, url_prefix="/api/fees")
    app.register_blueprint(expenses_bp, url_prefix="/api/expenses")
    app.register_blueprint(bulk_upload_bp, url_prefix="/api/bulk-upload")
    app.register_blueprint(dashboard_bp, url_prefix="/api/dashboard")
    app.register_blueprint(reports_bp, url_prefix="/api/reports")

    # Initialize predefined expense categories
    with app.app_context():
        initialize_categories()

    @app.route("/")
    def index():
        return jsonify({"message": "Welcome to the School Management API"}), 200

    @app.route("/favicon.ico")
    def favicon():
        return send_from_directory(os.path.join(app.root_path, "static"),
                                   "favicon.ico", mimetype="image/vnd.microsoft.icon")

    @app.errorhandler(Exception)
    def handle_exception(e):
        app.logger.error(f"Unhandled exception: {e}")
        return jsonify({"error": "An internal error occurred. Please try again later."}), 500

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
