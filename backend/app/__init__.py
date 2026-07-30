from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS

from .config import Config
from .extensions import db
from .routes import api
from .seed import seed_database


def create_app(test_config=None):
    load_dotenv()
    app = Flask(__name__)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)

    CORS(app, resources={r"/api/*": {"origins": "http://localhost:5174"}})
    db.init_app(app)
    app.register_blueprint(api)

    with app.app_context():
        db.create_all()
        seed_database()

    return app
