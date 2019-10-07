
import json
import requests
import numpy
import pybreaker
import tensorflow as tf

from werkzeug.utils import secure_filename
from flask import current_app as app
from flask import request, jsonify, Blueprint, flash, redirect

# used in the serving-tensor integration point
tensor_breaker = pybreaker.CircuitBreaker(fail_max=3, reset_timeout=30)
v1_rest_manager = Blueprint('v1_rest_manager', __name__, url_prefix='/v1')


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


@v1_rest_manager.route('/healthcheck', methods=['GET'])
def healthcheck():
     app.logger.info('healthcheck called')
     return '', 200


@tensor_breaker
def get_classification_result(file):
    img = tf.keras.preprocessing.image.load_img(file, target_size=[224, 224])
    img_array = tf.keras.preprocessing.image.img_to_array(img)
    img_array = tf.keras.applications.mobilenet.preprocess_input(img_array[tf.newaxis,...])

    data = json.dumps({"signature_name": "serving_default","instances": img_array.tolist()})
    headers = {"content-type": "application/json"}
    respone = requests.post(app.config['SERVING_TENSOR_PREDICTION_ENDPOINT'], data=data, headers=headers)

    predictions = numpy.array(json.loads(respone.text)["predictions"])
    predictions = predictions.flatten()
    result = json.dumps({"hocky": predictions[0], "soccer": predictions[1]})         
    app.logger.info("response for tensorflow %s" % result)
    return result


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
            app.logger.info('file %s recieved' % filename)
            result = get_classification_result(file)
            return jsonify(result), 200

    return '', 400
