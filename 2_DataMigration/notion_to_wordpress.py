# test this...
import requests
import json
import base64
from modules import secrets

# post_id = '24225'

url = "https://animationfestival.no/wp-json/wp/v2/pages/"
user = "faf"
password = secrets.wordpress_api_key
credentials = user + ':' + password
token = base64.b64encode(credentials.encode())
header = {'Authorization': 'Basic ' + token.decode('utf-8')}
# response = requests.get(url + post_id , headers=header)

post = {
    'title': 'Hello World',
    'status': 'draft',
    'content': 'This is my first post created using rest API',
    'date': '2020-01-05T10:00:00',

}

response = requests.post(url, headers=header, json=post)
print(response.json())

# https://animationfestival.no/wp-json/