
import json
import requests
import numpy
import pybreaker
import tensorflow as tf
import asyncio
import aiohttp

from retrying import retry
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


def process_file(file):
    img = tf.keras.preprocessing.image.load_img(file, target_size=[224, 224])
    img_array = tf.keras.preprocessing.image.img_to_array(img)
    img_array = tf.keras.applications.mobilenet.preprocess_input(img_array[tf.newaxis,...])
    data = json.dumps({"signature_name": "serving_default","instances": img_array.tolist()})
    return data
    

def process_response(respone):
    predictions = numpy.array(json.loads(respone)["predictions"])
    predictions = predictions.flatten()
    result = json.dumps({"hockey": predictions[0], "soccer": predictions[1]})   
    return result


"""
async operations
"""

async def get_classification_result_async(session, url, file):
    data = process_file(file)
    headers = {"content-type": "application/json"}
    async with session.post(url, data=data, headers=headers) as response:
        rseponse_text = await response.text()
        return process_response(rseponse_text) 


async def get_all_classification_results_async(files):
    async with aiohttp.ClientSession() as session:
        tasks = []
        for file in files:
            if allowed_file(file.filename):
                task = asyncio.create_task(
                    get_classification_result_async(session, app.config['SERVING_TENSOR_PREDICTION_ENDPOINT'], file))
                tasks.append(task)
        await asyncio.gather(*tasks, return_exceptions=True)
        return tasks


@v1_rest_manager.route('/uploads', methods=['POST'])
def upload_files():
    if request.method == 'POST':
        if not request.files:
            flash('No file part')
            app.logger.info('No file part, request.url %s' % request.url)
            return redirect(request.url)
        files = list(request.files.values())
        tasks = asyncio.run(get_all_classification_results_async(files))
        results = [task.result() for task in tasks]
        return jsonify(results), 200
    return '', 400

"""
sync operations
"""

def retry_if_io_error(exception):
    """Return True if Timeout exception"""
    return isinstance(exception, requests.exceptions.Timeout)


@tensor_breaker
@retry(retry_on_exception=retry_if_io_error, wait_fixed=1000)
def get_classification_result(file):
    app.logger.info("called get_classification_result")
    data = process_file(file)
    headers = {"content-type": "application/json"}
    respone = requests.post(app.config['SERVING_TENSOR_PREDICTION_ENDPOINT'], data=data, headers=headers)
    result = process_response(respone.text)       
    app.logger.info("response for tensorflow %s" % result)
    return result


@v1_rest_manager.route('/upload', methods=['POST'])
def upload_file():
    if request.method == 'POST':
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

