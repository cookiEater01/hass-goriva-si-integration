from urllib import request
import json


def get_data(url):

    response = request.urlopen(url)
    response_JSON = json.loads(response.read().decode("UTF-8"))

    return response_JSON
