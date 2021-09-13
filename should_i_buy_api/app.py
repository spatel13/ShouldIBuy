"""Application entry point."""
from flask import Flask
from databases.database import mongo


def create_app(config_file="settings.py"):
    """Create Flask application."""
    app = Flask(__name__)
    app.config.from_pyfile(config_file)
    print(app.config.get("MONGO_URI"))
    print(app.config.get("DEBUG"))
    mongo.init_app(app)

    with app.app_context():
        # Import parts of our application
        from apis.api import api_bp

        # Register Blueprints
        app.register_blueprint(api_bp)

        return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0")
