import requests
# import json
import base64
from fafscripts.modules import notion_new as n, utils as u, eventive
from fafscripts.models import EventCategory
import logging


def main(event_id: str):

    logger = logging.getLogger(__name__)

    e = n.Page(id=event_id)
    name = e.get_text('name')
    logger.info(f"Trying to push {name} to Wordpress.")

    text_rich = e.get_rich_text('text-catalogue')
    text_html = u.rich_text_to_html(text_rich)
    pic = e.get_text('pic')

    eventive_url = e.get_text('eventive')
    eventive_id = eventive.url_to_tag_id(eventive_url) if eventive_url else ""
    eventive_btn_code = ""
    if eventive_id:
        eventive_btn_code = f"<br><a class='btn-faf' target='_blank' href='https://{u.get_secret('FESTIVAL_ACRONYM').lower()}.eventive.org/schedule/{eventive_id}'>Order tickets</a>"

    if eventive_btn_code:
        text_html += eventive_btn_code

    event_category_id = e.get_list('category')
    if event_category_id:
        post_type = EventCategory.query.filter_by(
            notion_id=event_category_id[0]).first().wordpress_post_type
        logger.info(f'Found post type {post_type}')

    url = u.get_secret("WP_BASE_URL") + post_type + "/"
    user = u.get_secret("WP_USER")
    password = u.get_secret("WP_API_KEY")
    credentials = user + ':' + password
    token = base64.b64encode(credentials.encode())
    header = {'Authorization': 'Basic ' + token.decode('utf-8')}

    post = {
        "title": name,
        "status": "draft",
        "content": text_html,
        "featured_media": u.wp_id_from_url(pic),
        "tags": [u.get_secret("WP_TAG_ID")]
    }

    response = requests.post(url, headers=header, json=post)
    if "link" in response.json():
        e.set('wordpress', response.json()['link'])
        e.write()
        logger.info(f"Successfully pushed {name} to Wordpress.")
    else:
        logger.error(f"Error in response to Wordpress request. Check config?")
        logger.info(response.json())
