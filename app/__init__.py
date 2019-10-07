from flask import Flask
from flask.logging import default_handler
from flask_cors import CORS
from app.controllers import v1_rest_manager
import logging


UPLOAD_FOLDER = '/home/uploads'

def create_app(config):
    app = Flask(__name__)
    CORS(app)

    with app.app_context():
        app.config.from_object(config)
        
        app.secret_key = 'some secret key'
        app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
        app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

        gunicorn_logger = logging.getLogger('gunicorn.error')
        app.logger.handlers = gunicorn_logger.handlers
        app.logger.setLevel(gunicorn_logger.level)

        app.register_blueprint(v1_rest_manager)
        app.logger.info('serving tensor sidecar app initialized successfully')
        
    return app


