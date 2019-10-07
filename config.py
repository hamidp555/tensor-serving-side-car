import os

class BaseConfig:
    SERVING_TENSOR_PORT=8501
    SERVING_TENSOR_HOST='serving-tensor'
    SERVING_TENSOR_MODEL_NAME='sports_classifier'
    SERVING_TENSOR_ENDPOINT = 'http://%s:%d/v1/models/%s' % (SERVING_TENSOR_HOST, SERVING_TENSOR_PORT, SERVING_TENSOR_MODEL_NAME)
    SERVING_TENSOR_PREDICTION_ENDPOINT = '%s:predict' % (SERVING_TENSOR_ENDPOINT)
    ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])


class LiveConfig(BaseConfig):
    SERVING_TENSOR_PORT = os.environ.get('TENSOR_SERVING_PORT')
    SERVING_TENSOR_HOST = os.environ.get('TENSOR_SERVING_HOST')
    SERVING_TENSOR_MODEL_NAME = os.environ.get('TENSOR_SERVING_MODEL_NAME')
    

class TestConfig(BaseConfig):
    SERVING_TENSOR_PORT=8501
    SERVING_TENSOR_HOST='serving-tensor'
    SERVING_TENSOR_MODEL_NAME='sports_classifier'
