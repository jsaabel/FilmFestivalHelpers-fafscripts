import json
import requests
from fafscripts.modules import utils as u
import logging


headers = {
    'X-API-KEY': u.get_secret("EVENTIVE_API_KEY"),  # OBS
    'Content-Type': 'application/json',
}

logger = logging.getLogger(__name__)

# this might need an update!
# event_type_to_price = {
#     'Screening (Shorts)': (12000, 8000),
#     'Screening (Feature)': (12000, 8000),
#     'Ticketed Event': (18000, 18000),
#     'Free Event': (0, 0),
#     'Industry': (0, 0)
# }

# tag_to_tag_id = u.get_tag_dict()  # monitor this for performance issuse!


def add_films_to_request_dict(request_dict: dict, film_id_list: list):
    """takes a list of film ids and adds the films to a eventive request dictionary."""
    if 'films' not in request_dict:
        request_dict['films'] = list()
    for film_id in film_id_list:
        request_dict['films'].append(film_id)
    return request_dict


def add_tags_to_request_dict(request_dict: dict, tags_list: list):
    """takes names of tags from a list and adds their respective tag ids to a eventive request dictionary."""
    if 'tags' not in request_dict:
        request_dict['tags'] = []
    if tags_list:
        for item in tags_list:
            request_dict['tags'].append(item)
    else:
        logging.warning("No eventive tags were added.")


def country_code_to_geoblock_option(country_code: str) -> str:
    return f"country-{country_code}"


def film_id_from_url(url: str) -> str:
    return url.split('/')[-1]


def get_event_dict() -> dict:
    "Get empty/ready to be filled json dict for events"

    data = {
        "event_bucket": u.get_secret("EVENTIVE_BUCKET_ID"),
        "name": "",
        "films": [],
        "description": "",
        "short_description": "",
        "venue": "",
        "start_time": "",
        "end_time": "",
        "trailer_url": "",
        "visibility": "",
        "hide_tickets_button": True,
        "image_external": "",
        "require_mailing_address": False,
        "require_phone_number": False,
        "ticket_buckets": [
            {
                "name": "General Admission",
                "price": "",
                "unlimited": False,
                "reserved_seating_category": "",
                "quantity": "",
                "public": True,
                "exclude_capacity": False,
                "lock_admin_only": False,
                "variants": [],
                "applicable_pass_buckets": [],
                "pass_adjusted": {}
            }],
    }
    return data


def get_film_dict() -> dict:
    "Get empty/ready to be filled json dict for films"

    data = {
        "event_bucket": u.get_secret("EVENTIVE_BUCKET_ID"),
        "name": "",
        "details": {
            "year": "",
            "runtime": "",
            "language": "",
            "country": "",
            "premiere": "",
            "rating": "",
            "note": "",
        },
        "credits": {
            "director": "",
            "screenwriter": "",
            "producer": "",
            "executive_producer": "",
            "co_producer": "",
            "filmmaker": "",
            "cast": "",
            "cinematographer": "",
            "editor": "",
            "animator": "",
            "production_design": "",
            "composer": "",
            "sound_design": "",
            "music": "",
        },
        "trailer_url": "",
        "description": "",
        "cover_image_external": "",
        "still_image_external": "",
        "short_description": "",
        "visibility": "hidden",
        "unballoted": True,
    }
    return data


def get_virtual_dict() -> dict:
    "Get empty/ready to be filled json dict for virtual screenings"
    data = {
        "event_bucket": u.get_secret("EVENTIVE_BUCKET_ID"),
        "timezone": "Europe/Oslo",
        "name": "",
        "description": "",
        "short_description": "",
        "is_dated": True,
        "start_time": u.get_secret("VIRTUAL_START_TIME"),
        "end_time": u.get_secret("VIRTUAL_END_TIME"),
        "tags": [],
        "visibility": "hidden",
        "hide_tickets_button": False,
        "require_mailing_address": False,
        "require_phone_number": False,
        "rush_line_enabled": True,
        "passholder_ticket_required": "default",
        "standalone_ticket_sales_enabled": False,
        "standalone_ticket_sales_unlocked": False,
        "sales_disabled_unless_coupon": False,
        "disable_pass_quick_order": False,
        "credits_disabled": False,
        "tickets_available": True,
        "unlimited": True,
        "ticket_buckets": [
            {
                "name": "Virtual Admission",
                "price": 0,
                "unlimited": True,
                "public": True,
            }
        ],
        "films": [],
        "is_virtual": True,
        "show_in_coming_soon": True,
        "allow_preorder": True,
        "virtual_balloting_enabled": "",
        "use_default_event_bucket_preroll": True,
        "use_default_event_bucket_postroll": True,
        "virtual_show_donate_prompt": "default",
        "geographic_restrictions": [],
    }
    return data


def get_event(event_id: str):
    """Retrieves event json"""
    logger.info("Retrieving event.")
    base_url = f"https://api.eventive.org/events/{event_id}"
    request = requests.get(base_url, headers=headers)
    return request.json()


def get_film(film_id: str):
    """Retrieves film json"""
    logger.info("Retrieving film.")
    base_url = f"https://api.eventive.org/films/{film_id}"
    request = requests.get(base_url, headers=headers)
    return request.json()


def get_ticket_bucket_id(event_id: str) -> str:
    """retrieves an event and returns the first associated ticket bucket id."""
    response = get_event(event_id)
    return response['ticket_buckets'][0]['id']


def get_order(order_id):
    base_url = f"https://api.eventive.org/event_buckets/{u.get_secret('EVENTIVE_BUCKET_ID')}/orders/{order_id}"
    request = requests.get(base_url, headers=headers)
    return request.json()


def get_pass(pass_id):
    logger.info("Retrieving pass.")
    base_url = f"https://api.eventive.org/passes/{pass_id}"
    request = requests.get(base_url, headers=headers)
    return request.json()


def get_passes(pass_bucket_id):
    """Retrieves passes in pass bucket."""
    logger.info("Retrieving pass bucket.")
    base_url = f"https://api.eventive.org/pass_buckets/{pass_bucket_id}/passes"
    request = requests.get(base_url, headers=headers)
    return request.json()


def get_pass_buckets():
    logger.info("Retrieving pass buckets.")
    base_url = f"https://api.eventive.org/event_buckets/{u.get_secret('EVENTIVE_BUCKET_ID')}/pass_buckets"
    request = requests.get(base_url, headers=headers)
    return request.json()


def issue_all_access_pass(email: str, message: str = ""):
    base_url = "https://api.eventive.org/box_office/new_order"
    data = {
        "emails": [
            email
        ],
        "subitems": [
            {
                "pass_bucket": u.get_secret("AAA_PASS_BUCKET_ID"),
                "quantity": 1
            }
        ],
        "coupon": u.get_secret("COUPON_CODE"),
        "additional_message": message,
        "event_bucket": u.get_secret("EVENTIVE_BUCKET_ID"),
        "api_key": u.get_secret("EVENTIVE_API_KEY")
    }

    data = json.dumps(data)
    request = requests.post(base_url, data=data, headers=headers)
    return request.json()
# def issue_ticket(email: str, event_id: str, quantity: int = 1, message: str = ""):
#     """issues free ticket(s) to the chosen event."""
#     base_url = 'https://api.eventive.org/box_office/new_order'
#     ticket_bucket_id = get_ticket_bucket_id(event_id)
#
#     d = {
#         "emails": [
#             email
#         ],
#         "subitems": [
#             {
#                 "ticket_bucket": ticket_bucket_id,
#                 "quantity": quantity
#             }
#         ],
#         "additional_message": message,
#         "event_bucket": event_bucket_id,
#         "api_key": secrets.eventive_api_key
#     }
#     data = json.dumps(d)
#     request = requests.post(base_url, data=data, headers=headers)
#     print(request.json())


def update_event(data: dict, event_id: str) -> str:
    """Updates eventive event with data in dictionary, returns eventive id."""
    base_url = f"https://api.eventive.org/events/{event_id}"
    data = json.dumps(data)
    request = requests.post(base_url, headers=headers, data=data)
    response = request.json()
    try:
        eventive_id = response['id']
    except:
        logger.error("Failed to update event.")
    else:
        logger.info(f"Updated event on eventive (id: {eventive_id}).")
        return eventive_id


def update_film(data: dict, film_id: str) -> str:
    """Updates eventive film with data in dictionary, returns eventive id."""
    base_url = f"https://api.eventive.org/films/{film_id}"
    data = json.dumps(data)
    request = requests.post(base_url, headers=headers, data=data)
    response = request.json()
    try:
        eventive_id = response['id']
    except:
        logger.error("Failed to update film.")
    else:
        logger.info(f"Updated film on eventive (id: {eventive_id}).")
        return eventive_id


def update_pass_name(pass_id, name):
    """Updates the name of the pass with the supplied id"""
    base_url = f"https://api.eventive.org/passes/{pass_id}"
    data = {
        "name": name,
    }

    request = requests.post(base_url, headers=headers, data=json.dumps(data))
    return request.json()


def url_to_film_id(url: str) -> str:
    """returns film id for a provided film url"""
    return url.split('/')[-1]


def url_to_tag_id(url: str) -> str:
    """returns tag id for a provided tag url"""
    return url.split('/')[-1]


def write_event(data: dict, event_id=None):
    """Writes data in dictionary to eventive event, returns eventive id."""
    base_url = f"https://api.eventive.org/events/{event_id}" if event_id else "https://api.eventive.org/events"
    data = json.dumps(data)
    request = requests.post(base_url, headers=headers, data=data)
    response = request.json()
    try:
        eventive_id = response['id']
    except:
        logger.error("Failed to write event.")
        return None
    else:
        logger.info(f"Wrote event to eventive. (id: {eventive_id}).")
        return eventive_id


def write_film(data: dict, film_id=None):
    """Writes data in dictionary to eventive event, returns eventive id."""
    base_url = f"https://api.eventive.org/films/{film_id}" if film_id else "https://api.eventive.org/films"
    data = json.dumps(data)
    request = requests.post(base_url, headers=headers, data=data)
    response = request.json()
    try:
        eventive_id = response['id']
    except:
        logger.error("Failed to write film.")
        return None
    else:
        logger.info(f"Wrote film to eventive. (id: {eventive_id}).")
        return eventive_id
