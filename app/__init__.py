from flask import Flask
from .utils.db_manager import DBManager
from flask_caching import Cache

def create_app():
    app = Flask(__name__, template_folder='templates', static_folder='static')
    app.config['SECRET_KEY'] = 'your-secret-key-here'
    app.config['DATABASE'] = 'AttachmentTestimonyHub/testimonies.db'
    app.config['CACHE_TYPE'] = 'SimpleCache'  # For page speed

    # Initialize database
    db = DBManager()
    app.db = db

    # Initialize cache
    cache = Cache(app)

    # Register routes
    from .routes import init_routes
    init_routes(app, cache)

    return app