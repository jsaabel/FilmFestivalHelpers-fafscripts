import requests
# import json
import base64
from fafscripts.modules import notion_new as n, utils as u
import logging


def main(guest_id: str):

    logger = logging.getLogger(__name__)
    g = n.Page(id=guest_id)
    # retrieve guest info
    name = g.get_text('name')
    logger.info(f"Trying to push {name} to Wordpress.")
    bio_rich = g.get_rich_text('bio-eng')
    bio_html = u.rich_text_to_html(bio_rich)
    pic = g.get_text('headshot-url')

    # options: 'biographies', 'seminars', 'faf-events'
    url = u.get_secret("WP_BASE_URL") + "biographies/"
    user = u.get_secret("WP_USER")
    password = u.get_secret("WP_API_KEY")
    credentials = user + ':' + password
    token = base64.b64encode(credentials.encode())
    header = {'Authorization': 'Basic ' + token.decode('utf-8')}

    post = {
        "title": name,
        "status": "draft",
        "content": bio_html,
        "featured_media": u.wp_id_from_url(pic),
        "tags": [u.get_secret("WP_TAG_ID")]
    }

    response = requests.post(url, headers=header, json=post)
    if "link" in response.json():
        g.set('wordpress', response.json()['link'])
        g.write()
        logger.info(f"Successfully pushed {name} to Wordpress.")
    else:
        logger.error(f"Error in response to Wordpress request.")

    # print(response.json())
    # logger.debug(response)
    # print(json.dumps(response.json(), indent=2))

    # https://animationfestival.no/wp-json/
