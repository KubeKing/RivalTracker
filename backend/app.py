# backend/app.py
from flask import Flask
from flask_cors import CORS
from src.api.routes import api
import os

def create_app():
    app = Flask(__name__)
    CORS(app)
    
    app.register_blueprint(api, url_prefix='/api')
    
    return app

if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)