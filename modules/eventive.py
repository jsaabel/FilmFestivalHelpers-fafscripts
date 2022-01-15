# 22.07.2021
import json
import requests
from modules import secrets, utils as u


event_bucket_id = '5fa953f600ef650071c4d68c'
# FAF 2021 event_bucket_id: 5fa953f600ef650071c4d68c
# FAF 2021 test event bucket: 60e7579087291c0083e504eb

headers = {
    'X-API-KEY': secrets.eventive_api_key,
    'Content-Type': 'application/json',
}

# this might need an update!
event_type_to_price = {
    'Screening (Shorts)': (12000, 8000),
    'Screening (Feature)': (12000, 8000),
    'Ticketed Event': (18000, 18000),
    'Free Event': (0, 0),
    'Industry': (0, 0)
}

tag_to_tag_id = u.get_tag_dict()  # monitor this for performance issuse!


def add_films_to_request_dict(request_dict: dict, film_id_list: list):
    """takes a list of film ids and adds the films to a eventive request dictionary."""
    if 'films' not in request_dict:
        request_dict['films'] = list()
    for film_id in film_id_list:
        request_dict['films'].append(film_id)


def add_tags_to_request_dict(request_dict: dict, tags_list: list):
    """takes names of tags from a list and adds their respective tag ids to a eventive request dictionary."""
    if 'tags' not in request_dict:
        request_dict['tags'] = []
    for item in tags_list:
        request_dict['tags'].append(tag_to_tag_id[item])


def get_event(event_id: str):
    """Retrieves film json"""
    base_url = f"https://api.eventive.org/events/{event_id}"
    request = requests.get(base_url, headers=headers)
    return request.json()


def get_film(film_id: str):
    """Retrieves film json"""
    base_url = f"https://api.eventive.org/films/{film_id}"
    request = requests.get(base_url, headers=headers)
    return request.json()


def get_ticket_bucket_id(event_id: str) -> str:
    """retrieves an event and returns the first associated ticket bucket id."""
    response = get_event(event_id)
    return response['ticket_buckets'][0]['id']


def issue_ticket(email: str, event_id: str, quantity: int = 1, message: str = ""):
    """issues free ticket(s) to the chosen event."""
    base_url = 'https://api.eventive.org/box_office/new_order'
    ticket_bucket_id = get_ticket_bucket_id(event_id)

    d = {
        "emails": [
            email
        ],
        "subitems": [
            {
                "ticket_bucket": ticket_bucket_id,
                "quantity": quantity
            }
        ],
        "additional_message": message,
        "event_bucket": event_bucket_id,
        "api_key": secrets.eventive_api_key
    }
    data = json.dumps(d)
    request = requests.post(base_url, data=data, headers=headers)
    print(request.json())


def update_event(data: dict, event_id: str):
    """Updates eventive event with data in dictionary, returns eventive id."""
    base_url = f"https://api.eventive.org/events/{event_id}"
    data = json.dumps(data)
    request = requests.post(base_url, headers=headers, data=data)
    response = request.json()
    try:
        eventive_id = response['id']
    except:
        u.print_error_message('e.update_event', response)
    else:
        print(f"\t...updated event in eventive (id: {eventive_id})")
        return eventive_id


def update_film(data: dict, film_id: str):
    """Updates eventive film with data in dictionary, returns eventive id."""
    base_url = f"https://api.eventive.org/films/{film_id}"
    data = json.dumps(data)
    request = requests.post(base_url, headers=headers, data=data)
    response = request.json()
    try:
        eventive_id = response['id']
    except:
        u.print_error_message('e.update_film', response)
    else:
        print(f"\t...updated film in eventive (id: {eventive_id})")
        return eventive_id


def write_event(data: dict):
    """Writes data in dictionary to eventive event, returns eventive id."""
    base_url = "https://api.eventive.org/events"
    data = json.dumps(data)
    request = requests.post(base_url, headers=headers, data=data)
    response = request.json()
    try:
        eventive_id = response['id']
    except:
        u.print_error_message('e.write_event', response)
    else:
        print(f"\t...wrote event to eventive (id: {eventive_id})")
        return eventive_id


def write_film(data: dict):
    """Writes data in dictionary to eventive event, returns eventive id."""
    base_url = "https://api.eventive.org/films"
    data = json.dumps(data)
    request = requests.post(base_url, headers=headers, data=data)
    response = request.json()
    try:
        eventive_id = response['id']
    except:
        u.print_error_message('e.write_film', response)
    else:
        print(f"\t...wrote film to eventive (id: {eventive_id})")
        return eventive_id
