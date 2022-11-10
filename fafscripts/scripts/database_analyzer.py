from fafscripts.modules import notion_new as n
from fafscripts.scripts import dba_catalogue, dba_event, dba_film, dba_guest
import logging


logger = logging.getLogger(__name__)


def main(db: str):

    r = get_results_dict()

    if db.lower() == "films":
        r.update(analyze_films_db(r))
    elif db.lower() == "guests":
        r.update(analyze_guests_db(r))
    elif db.lower() == "events":
        r.update(analyze_events_db(r))
    elif db.lower() == "catalogue":
        r.update(analyze_catalogue_db(r))
    return r


if __name__ == "__main__":
    main()


def analyze_films_db(r):

    logger.info("Analyzing film database...")
    data_dict = dict()
    n.add_filter_to_request_dict(data_dict, "🎥 Film programmes", "relation",
                                 "is_not_empty", True)
    notion_data = n.get_db('films', data_dict=data_dict)

    r = get_results_dict()
    for page in notion_data['results']:
        film = n.Page(json_obj=page)
        temp_dict = dba_film.analyze_film(film)
        for error in temp_dict['errors']:
            r['errors'].append(error)
        for warning in temp_dict['warnings']:
            r['warnings'].append(warning)
        for message in temp_dict['messages']:
            r['messages'].append(message)

    return r


def analyze_guests_db(r):

    logger.info("Analyzing guest database...")
    data_dict = dict()
    notion_data = n.get_db('guests', data_dict=data_dict)
    data_dict_events = dict()
    # retrieved event db has to be sorted chronologically
    n.add_sorts_to_request_dict(data_dict_events, 'Time', 'ascending')
    events_data = n.get_db('events', data_dict=data_dict_events)

    r = get_results_dict()
    for page in notion_data['results']:
        guest = n.Page(json_obj=page)
        temp_dict = dba_guest.analyze_guest(
            guest=guest, events_data=events_data)
        for error in temp_dict['errors']:
            r['errors'].append(error)
        for warning in temp_dict['warnings']:
            r['warnings'].append(warning)
        for message in temp_dict['messages']:
            r['messages'].append(message)

    return r


def analyze_events_db(r):

    logger.info("Analyzing event database...")
    data_dict_events = dict()
    # retrieved event db has to be sorted chronologically
    n.add_sorts_to_request_dict(data_dict_events, 'Time', 'ascending')
    events_data = n.get_db('events', data_dict=data_dict_events)

    r = get_results_dict()
    for page in events_data['results']:
        event = n.Page(json_obj=page)
        temp_dict = dba_event.analyze_event(event)
        for error in temp_dict['errors']:
            r['errors'].append(error)
        for warning in temp_dict['warnings']:
            r['warnings'].append(warning)
        for message in temp_dict['messages']:
            r['messages'].append(message)

    return r


def analyze_catalogue_db(r):

    logger.info("Analyzing catalog database...")
    catalog_data = n.get_db('catalogue')

    r = get_results_dict()
    for cat_page in catalog_data['results']:
        page = n.Page(json_obj=cat_page)
        temp_dict = dba_catalogue.analyze_catalogue_page(page)
        for error in temp_dict['errors']:
            r['errors'].append(error)
        for warning in temp_dict['warnings']:
            r['warnings'].append(warning)
        for message in temp_dict['messages']:
            r['messages'].append(message)

    return r


def get_max_text_length() -> int:
    return 1200


# also in utils
def get_results_dict():

    r = {
        'messages': [],
        'warnings': [],
        'errors': [],
    }

    return r


# also in utils
def add_to_results(results: dict, title, category, message, url):

    code_to_category = {
        "e": "errors",
        "w": "warnings",
        "m": "messages",
    }

    feedback_dict = {
        "message": f"{title}: {message}",
        "url": url,
    }
    results[code_to_category[category]].append(feedback_dict)
