
import json
import requests
import os

from werkzeug.utils import secure_filename
from flask import current_app as app
from flask import request, jsonify, Blueprint, flash, redirect
import tensorflow as tf


ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

v1_rest_manager = Blueprint('v1_rest_manager', __name__, url_prefix='/v1')


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@v1_rest_manager.route('/healthcheck', methods=['GET'])
def healthcheck():
     app.logger.info('healthcheck called')
     return '', 200


@v1_rest_manager.route('/upload', methods=['POST'])
def upload_file():
    if request.method == 'POST':
        app.logger.info('upload called')
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            app.logger.info('No file part, request.url %s' % request.url)
            return redirect(request.url)
        file = request.files.get('file')
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file')
            app.logger.info('No selected file, request.url %s' % request.url)
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            app.logger.info('file saved as %s' % file_path)

            img = tf.keras.preprocessing.image.load_img(file, target_size=[224, 224])
            img_array = tf.keras.preprocessing.image.img_to_array(img)
            img_array = tf.keras.applications.mobilenet.preprocess_input(img_array[tf.newaxis,...])
  
            data = json.dumps({"signature_name": "serving_default","instances": img_array.tolist()})
            headers = {"content-type": "application/json"}
            json_response = requests.post('http://serving-tensor:8501/v1/models/sports_classifier:predict', data=data, headers=headers)

            return jsonify(json.loads(json_response.text)), 200

    return '', 400
