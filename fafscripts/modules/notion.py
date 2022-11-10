import json
import requests
import urllib.request
from fafscripts.models import DatabaseID, Venue
from fafscripts.modules.utils import get_secret
import fafscripts.modules.utils as u
import logging

# header for html requests


def get_header():
    header = {
        "Authorization": get_secret("NOTION_API_KEY"),
        "Notion-Version": "2022-02-22",
        "Content-Type": "application/json",
    }
    return header


def add_block_to_request_dict(request_dict: dict, block_type: str, content: str):
    """adds a block to request dict (e. g. when creating pages in db)"""
    if block_type == 'link':
        temp_dict = {
            "object": "block",
            "type": 'paragraph',
            'paragraph': {
                    "text": [{"type": "text",
                              "text": {"content": content,
                                       "link": {'type': 'url',
                                                'url': content}}}]
            }}
    else:
        temp_dict = {
            "object": "block",
            "type": block_type,
            block_type: {
                "rich_text": [{"type": "text",
                                       "text": {"content": content}}]
            }
        }
    if not 'children' in request_dict:
        request_dict['children'] = []

    request_dict['children'].append(temp_dict)


def add_cover_to_page(page_id: str, url: str):
    """makes the chosen image (provided by url) the page's cover image."""
    base_url = "https://api.notion.com/v1/pages/"
    data_raw = dict()
    temp_dict = {"type": "external",
                 "external": {
                     "url": url}}
    data_raw['cover'] = temp_dict
    data = json.dumps(data_raw)
    r = requests.patch(base_url + page_id, headers=get_header(), data=data)
    error_check_response(r)
    logging.info(f"...updated cover img.")


def add_icon_to_page(page_id: str, emoji: str):
    """makes the chosen emoji the page's icon."""
    base_url = "https://api.notion.com/v1/pages/"
    data_raw = dict()
    temp_dict = {"type": "emoji", "emoji": emoji}

    data_raw['icon'] = temp_dict
    data = json.dumps(data_raw)
    r = requests.patch(base_url + page_id, headers=get_header(), data=data)
    error_check_response(r)
    logging.info(f"...updated page icon.")


def add_cover_to_request_dict(request_dict: dict, url: str):
    """adds the chosen image (provided by url) to request dict as cover img."""
    temp_dict = {"type": "external",
                 "external": {
                     "url": url}}
    request_dict['cover'] = temp_dict


def add_icon_to_request_dict(request_dict: dict, emoji: str):
    """adds the chosen emoji to request dict as page icon."""
    temp_dict = {"type": "emoji", "emoji": emoji}

    request_dict['icon'] = temp_dict


def add_filter_to_request_dict(request_dict: dict, property_name: str, property_type: str, filter_condition: str,
                               filter_content: str):
    """adds a filter (in the form of a dictionary in the 'data' property) to a notion database request"""
    """https://developers.notion.com/reference/post-database-query#post-database-query-filter"""
    filter_dict = {'property': property_name,
                   property_type: {filter_condition: filter_content},
                   }
    request_dict['filter'] = filter_dict


def add_sorts_to_request_dict(request_dict: dict, property_name: str, sorts_direction: str = 'ascending'):
    """adds a single sort (in the form of a dictionary in the 'data' property) to a notion database request"""
    sorts_dict = [{'property': property_name,
                   'direction': sorts_direction,
                   }]
    request_dict['sorts'] = sorts_dict


def add_parent_id_to_request_dict(request_dict: dict, parent_id):
    request_dict['parent'] = {
        "database_id": parent_id
    }


def add_property_to_request_dict(request_dict: dict, content, property_name, property_type='rich_text'):
    """adds a property (with name, type and content) to a dictionary. Used to simplify the process
    of sending 'json-ized' dictionaries to API"""
    # create dictionary structure if not present from before
    if 'properties' not in request_dict:
        request_dict['properties'] = {}
    # adding property names and values to temporary dictionary
    temp_dict = {
        property_name: {
            "rich_text": [{
                "text": {
                    "content": content
                }
            }]
        }
    }
    if property_type == 'title':
        temp_dict = {
            property_name: {
                "title": [{
                    "text": {
                        "content": content
                    }
                }]
            }
        }
    elif property_type == 'select':
        temp_dict = {
            property_name: {
                "type": "select",
                "select": {
                    "name": content
                }
            }
        }
    elif property_type == 'number':
        temp_dict = {
            property_name: {
                "type": "number",
                "number": content
            }
        }
    elif property_type == 'multi_select':
        temp_dict = {
            property_name: {
                "type": property_type,
                "multi_select": []
            }
        }
        for item in content:
            item_dict = {'name': item}
            temp_dict[property_name][property_type].append(item_dict)
    elif property_type == 'email':
        temp_dict = {
            property_name: {
                "type": "email",
                "email": content
            }
        }
    elif property_type == 'url':
        temp_dict = {
            property_name: {
                "type": "url",
                "url": content
            }
        }
    # updating original dictionary with temporary dictionary
    request_dict['properties'].update(temp_dict)


def create_db(properties: dict, title: str = "New DB", parent: str = "default"):
    """Creates an empty database with the provided properties (name and type)"""
    logging.info("exec create_db.")
    base_url = "https://api.notion.com/v1/databases/"
    # include "title" at root level?
    page_id = "04645a3397bc4d6ebebaa3442f58707a"
    if not parent == "default":
        page_id = parent

    data_raw = {
        "parent": {
            "type": "page_id",
            "page_id": page_id
        },
        "title": [{
            "type": "text",
            "text": {
                    "content": title
            }
        }
        ],
        "properties": {
        }
    }

    for property_name, property_type in properties.items():
        sub_dict = {property_name: {property_type: {}}}
        data_raw['properties'].update(sub_dict)

    data = json.dumps(data_raw)
    r = requests.post(base_url, headers=get_header(), data=data)
    return r.json()["id"]  # add conditional check etc


def download_file(file_url: str, target_folder: str, target_filename: str = ""):
    """download a file from provided/previously retrieved url."""
    # add file extension recognition?
    if not target_filename:
        parts = file_url.split('?')
        clean_url = parts[0]
        file_name_index = clean_url.rfind('/')
        target_filename = clean_url[file_name_index + 1:]
    logging.info(f'downloading file: {target_filename}...')
    urllib.request.urlretrieve(
        url=file_url, filename=f'{target_folder}/{target_filename}')


def error_check_response(response_object):
    """checks html response for errors, prints status report"""
    if 'error' not in response_object.json()['object']:
        logging.info('Request successfully executed.')
        return True
    else:
        logging.error('! Error in response to request.')
        logging.message(response_object.json()['message'])
        return False


def generate_info_lines(ids: list) -> list:
    """generates infolines for use in catalogue from a list of ids (typically from relation-property)"""
    logging.info("Generating info lines.")
    info_lines = list()
    try:
        for id in ids:
            notion_data = get_page(id)
            venue_id = get_property_from_page(
                'Venue', 'relation', source=notion_data)
            venue_page = get_page(venue_id[0])
            venue = get_property_from_page('Name', 'title', source=venue_page)
            day = get_property_from_page(
                'Time', 'date', source=notion_data)[0][8:10]
            time = get_property_from_page(
                'Time', 'date', source=notion_data)[0][11:16]
            age_limit = get_property_from_page(
                'Age Limit', 'number', source=notion_data)
            info_line = f"{day} OCT / {time} / {venue.upper()}"
            if age_limit:
                info_line += f' / AGE LIMIT: {age_limit}'
            info_lines.append(info_line)
    except (IndexError, TypeError):
        logging.error("Error encountered while generating info lines.")
        return []
    return sorted(info_lines)


def generate_film_view_dict(notion_page) -> dict:
    title = get_property_from_page(
        "English Title", 'title', source=notion_page)
    notion_id = get_property_from_page(property_type="id", source=notion_page)
    notion_url = get_property_from_page(
        property_type="page_url", source=notion_page)
    title_ov = get_property_from_page(
        "Original Title", 'rich_text', source=notion_page)
    year = get_property_from_page("Year", 'select', source=notion_page)
    director = get_property_from_page(
        "Director", 'rich_text', source=notion_page)
    synopsis = get_property_from_page(
        "Synopsis", 'rich_text', source=notion_page, mode="rich")
    if synopsis:
        synopsis = u.rich_text_to_html(synopsis)
    bio = get_property_from_page(
        "Bio", 'rich_text', source=notion_page, mode="rich")
    if bio:
        bio = u.rich_text_to_html(bio)
    country = get_property_from_page(
        "Country", 'multi_select', source=notion_page)
    if country:
        country = u.list_to_comma_separated(country)
    runtime = get_property_from_page(
        "Runtime", 'rich_text', source=notion_page)  # OBS
    technique = get_property_from_page(
        "Technique", 'multi_select', source=notion_page)
    if technique:
        technique = u.list_to_comma_separated(technique)
    production = get_property_from_page(
        "Production", 'rich_text', source=notion_page)
    animation = get_property_from_page(
        "Animation", 'rich_text', source=notion_page)
    # "seq" = str(index + 2).zfill(2)  # OBS
    still_img = get_property_from_page("Pic", 'url', source=notion_page)
    # OBS 'new' functionality for feature films
    programme = get_property_from_page(
        "Programme", 'multi_select', source=notion_page)
    if programme:
        programme = u.list_to_comma_separated(programme)
    dcp_status = get_property_from_page(
        "DCP Status", 'select', source=notion_page)
    eventive = get_property_from_page("Eventive", 'select', source=notion_page)
    file_status = get_property_from_page(
        "File Status", 'select', source=notion_page)
    digital_approval = get_property_from_page(
        "Digital Approval", 'checkbox', source=notion_page)
    trailer_url = get_property_from_page(
        "Trailer URL", 'url', source=notion_page)
    filmfreeway_link = get_property_from_page(
        "FilmFreeway Link", 'url', source=notion_page)
    eventive_link = get_property_from_page(
        "eventive_link", 'url', source=notion_page)
    eventive_id = get_property_from_page(
        "eventive_id", 'rich_text', source=notion_page)

    film_dict = {
        "title": title,
        "notion_id": notion_id,
        "notion_url": notion_url,
        "title_ov": title_ov,
        "year": year,
        "director": director,
        "synopsis": synopsis,
        "bio": bio,
        "country": country,
        "technique": technique,
        "production": production,
        "animation": animation,
        "still_img": still_img,
        "programme": programme,
        "runtime": runtime,
        "dcp_status": dcp_status,
        "eventive": eventive,
        "file_status": file_status,
        "digital_approval": digital_approval,
        "trailer_url": trailer_url,
        "filmfreeway_link": filmfreeway_link,
        "eventive_link": eventive_link,
        "eventive_id": eventive_id,
    }

    return film_dict


def generate_event_view_dict(notion_page) -> dict:
    name = get_property_from_page("Name", 'title', source=notion_page)
    notion_id = get_property_from_page(property_type="id", source=notion_page)
    notion_url = get_property_from_page(
        property_type="page_url", source=notion_page)
    attendees_ids = get_property_from_page(
        "Attendees", property_type="relation", source=notion_page)
    functionaries_ids = get_property_from_page(
        "Functionaries", property_type="relation", source=notion_page)
    notion_time = get_property_from_page("Time", 'date', source=notion_page)
    notion_venue = get_property_from_page(
        "Venue", 'relation', source=notion_page)
    venue = None
    if notion_venue:
        venue = Venue.query.filter_by(notion_id=notion_venue[0]).first().name
    if not venue:
        venue = "unspecified venue"
    try:
        time = u.get_date_string(notion_time[0], output='time')
    except TypeError:
        time = "unspecified time"
    try:
        day = u.get_date_string(notion_time[0], output='day')
    except TypeError:
        day = "Unspecified day"

    event_dict = {
        "name": name,
        "notion_id": notion_id,
        "notion_url": notion_url,
        "attendees_ids": attendees_ids,
        "functionaries_ids": functionaries_ids,
        "time": time,
        "day": day,
        "venue": venue,
    }

    return event_dict


def generate_guest_view_dict(notion_page) -> dict:
    name = get_property_from_page("Name", 'title', source=notion_page)
    status = get_property_from_page("Status", 'select', source=notion_page)
    notion_id = get_property_from_page(property_type="id", source=notion_page)
    notion_url = get_property_from_page(
        property_type="page_url", source=notion_page)
    bio = get_property_from_page(
        "Bio", 'rich_text', source=notion_page, mode="rich")
    if bio:
        bio = u.rich_text_to_html(bio)
    # "seq" = str(index + 2).zfill(2)  # OBS
    # OBS 'new' functionality for feature films
    category = get_property_from_page(
        "Guest Category", 'select', source=notion_page)
    events_attendee = get_property_from_page(
        "Events (Attendees)", "relation", source=notion_page)
    events_functionary = get_property_from_page(
        "Events (Functionary)", "relation", source=notion_page)
    email = get_property_from_page("E-Mail", "email", source=notion_page)

    guest_dict = {
        "name": name,
        "notion_id": notion_id,
        "notion_url": notion_url,
        "bio": bio,
        "category": category,
        "events_attendee": events_attendee,
        "events_functionary": events_functionary,
        "status": status,
        "email": email,

    }

    return guest_dict


def generate_guests():
    guests = list()
    notion_data = get_db('guests')
    item_count_notion = get_item_count(notion_data)
    for i in range(item_count_notion):
        name = get_property(i, "Name", "title", source=notion_data)
        if name and name not in guests:
            guests.append(name)
    return sorted(guests)


def generate_programmes_and_seq():
    programmes = list()
    seq_choices = list()
    notion_data = get_db('films')
    for property in notion_data['results'][0]['properties']:
        if "Seq" in property and property not in seq_choices:
            seq_choices.append(property)
    item_count_notion = get_item_count(notion_data)
    for index in range(item_count_notion):
        retrieved_programmes = get_property(index, 'Programme', 'multi_select',
                                            source=notion_data)
        for programme in retrieved_programmes:
            if programme not in programmes:
                programmes.append(programme)

    return sorted(programmes), sorted(seq_choices)


def get_children(block_id):
    """retrieve a page's / block's children as json"""
    base_url = f'https://api.notion.com/v1/blocks/{block_id}/children'
    request = requests.get(base_url, headers=get_header())
    return request.json()


def get_children_ids(parent_id):
    """Returns a list of all children (block) ids for a specified parent page/block."""
    base_url = f"https://api.notion.com/v1/blocks/{parent_id}/children"
    r = requests.get(base_url, headers=get_header())
    response = r.json()
    children = list()
    for object in response['results']:
        children.append((object['id'], object['type']))
    if len(children) > 0:
        logging.info('Block children retrieved.')
    return children


def get_item_count(notion_db):
    """returns the number of items in a notion db/json-object."""
    item_count = 0
    for result in notion_db["results"]:
        item_count += 1
    return item_count


def get_db(db_name=None, data_dict=None, db_id=None):  # safe to remove "=films?"
    """retrieves the desired notion-db as json object. optional: filtering and/or sorting by providing dict
     NB: keep db_ids dict updated!"""
    base_url = "https://api.notion.com/v1/databases/"
    if not db_id:
        # db_id = db_ids[db_name]
        logging.debug(f"Querying DatabaseID model for {db_name}.")
        db_id = DatabaseID.query.filter_by(name=db_name).first().notion_id
    data = dict()
    if data_dict:
        data.update(data_dict)
    data_json = json.dumps(data)
    response = requests.post(base_url + db_id + "/query",
                             headers=get_header(), data=data_json)
    test = error_check_response(response)
    if not test:
        logging.error("Error in response.")
        return

    notion_data = response.json()
    previous_request = notion_data

    # Pagination
    has_more = notion_data['has_more']
    if has_more:
        logging.info("Retrieving paginated database.")
    while has_more:
        next_cursor = previous_request['next_cursor']
        data['start_cursor'] = next_cursor
        data_json = json.dumps(data)
        next_request = requests.post(
            base_url + db_id + "/query", headers=get_header(), data=data_json)
        next_request_json = next_request.json()
        for result in next_request_json['results']:
            notion_data['results'].append(result)
        has_more = next_request_json['has_more']
        previous_request = next_request_json

    item_count = get_item_count(notion_data)
    if item_count == 0:
        logging.warning("Empty database retrieved. Check filters?")
    logging.info(
        f"Database ('{db_name}') loaded. {item_count} items retrieved.")
    return notion_data


def get_eventive_ids_shorts(source):
    """generates a list of eventive film ids from a (previously filtered, sorted and retrieved) notion database"""
    item_count_notion = get_item_count(source)
    eventive_ids = list()
    for index in range(0, item_count_notion):
        eventive_ids.append(get_property(index, 'eventive_id', source=source))
    return eventive_ids


def get_name_from_relation(relation_id: str, relation_db: dict) -> str:
    """given a notion id, this function returns the related name (title property)
    from the related db (in the form of a previously retrieved json object)"""
    item_count_relation_db = get_item_count(relation_db)
    for search_count in range(0, item_count_relation_db):
        if relation_db['results'][search_count]['id'] == relation_id:
            relation_name = relation_db['results'][search_count]['properties']['Name']['title'][0]['text']['content']
            return relation_name
    else:
        return relation_id


def get_page(page_id):
    """retrieve a notion page"""
    logging.info(f"Retrieving page (id {page_id}).")
    base_url = "https://api.notion.com/v1/pages/"
    request = requests.get(base_url + page_id, headers=get_header())
    return request.json()


def get_page_from_db(page_id: str, source="notion_data"):
    """returns the page data (properties etc) of a single page from a PREVIOUSLY RETRIEVED database."""
    for index in range(len(source['results'])):
        if page_id in source['results'][index]['id']:
            index_match = index
            break
    return source['results'][index_match]


def get_property(index, property_name=None, property_type="rich_text", source="notion_data", mode="plain"):
    """returns plain text or list object for a given property from notion db API json"""
    res = None
    try:
        if property_type == "rich_text" and mode == "plain":
            if len(source['results'][index]['properties'][property_name][property_type]) > 1:
                res = str()
                for number in range(len(source['results'][index]['properties'][property_name][property_type])):
                    res += source['results'][index]['properties'][property_name][property_type][number]['text']['content']
            else:
                res = source['results'][index]['properties'][property_name][property_type][0]['plain_text']
        elif property_type == "rich_text" and mode == "rich":
            res = source['results'][index]['properties'][property_name][property_type]
        elif property_type == "title":
            res = source['results'][index]['properties'][property_name][property_type][0]['plain_text']
        elif (property_type == "number" or property_type == "checkbox"
                or property_type == "url" or property_type == 'email'):
            res = source['results'][index]['properties'][property_name][property_type]
        elif property_type == "multi_select":
            res = list()
            for item in source['results'][index]['properties'][property_name][property_type]:
                res.append(item['name'])
        elif property_type == 'select':
            res = source['results'][index]['properties'][property_name][property_type]['name']
        elif property_type == 'date':
            res1 = source['results'][index]['properties'][property_name]['date']['start']
            res2 = source['results'][index]['properties'][property_name]['date']['end']
            res = res1, res2
        elif property_type == 'relation':
            res = list()
            dictionaries = source['results'][index]['properties'][property_name][property_type]
            for dictionary in dictionaries:
                res.append(dictionary['id'])
        elif property_type == 'id':
            res = source['results'][index]['id']
        elif property_type == 'page_url':
            res = source['results'][index]['url']
        elif property_type == 'people':
            res = list()
            dictionaries = source['results'][index]['properties'][property_name][property_type]
            for dictionary in dictionaries:
                res.append(dictionary['name'])
        elif property_type == 'files':
            res = list()
            dictionaries = source['results'][index]['properties'][property_name][property_type]
            for dictionary in dictionaries:
                res.append(dictionary['file']['url'])
    except (IndexError, KeyError, NameError, TypeError):
        # res = None
        pass
    # remove unnecessary spaces (Anders..)
    if isinstance(res, str) and len(res) > 1:
        if res[-1] == " ":
            res = res[:-1]
    return res


def get_property_from_page(property_name=None, property_type="rich_text", source="notion_data",
                           mode="plain"):
    """returns plain text or list object for a given property from notion page API json"""
    res = None
    try:
        if property_type == "rich_text" and mode == "plain":
            if len(source['properties'][property_name][property_type]) > 1:
                res = str()
                for number in range(len(source['properties'][property_name][property_type])):
                    res += source['properties'][property_name][property_type][number]['text']['content']
            else:
                res = source['properties'][property_name][property_type][0]['plain_text']
        elif property_type == "rich_text" and mode == "rich":
            res = source['properties'][property_name][property_type]
        # if property_type == "rich_text": # leaving following 4 lines in JIC
        #     res = source['properties'][property_name]['rich_text'][0]['plain_text']
        elif property_type == "title":
            res = source['properties'][property_name][property_type][0]['plain_text']
        elif (property_type == "number" or property_type == "checkbox"
                or property_type == "url" or property_type == "email"):
            res = source['properties'][property_name][property_type]
        elif property_type == "multi_select":
            res = list()
            for item in source['properties'][property_name][property_type]:
                res.append(item['name'])
        elif property_type == 'select':
            res = source['properties'][property_name][property_type]['name']
        elif property_type == 'date':
            res1 = source['properties'][property_name]['date']['start']
            res2 = source['properties'][property_name]['date']['end']
            res = res1, res2
        elif property_type == 'relation':
            res = list()
            dictionaries = source['properties'][property_name][property_type]
            for dictionary in dictionaries:
                res.append(dictionary['id'])
        elif property_type == 'id':
            res = source['id']
        elif property_type == 'page_url':
            res = source['url']
        elif property_type == 'files':
            res = list()
            dictionaries = source['properties'][property_name][property_type]
            for dictionary in dictionaries:
                res.append(dictionary['file']['url'])
    except (IndexError, KeyError, NameError, TypeError):
        pass
    return res


def get_text_from_child(index, source, mode='plain'):
    """use to extract plain text from list of text-like child blocks in json"""
    property_type = str(source['results'][index]['type'])
    if mode == "plain":
        plain_text = ""
        for segment in source['results'][index][property_type]['rich_text']:
            plain_text += segment['plain_text']
        # plain_text = source['results'][index][property_type]['rich_text'][0]['plain_text']
        return plain_text
    else:
        return source['results'][index][property_type]['rich_text']


def get_unique_values_in_db_property(db: str, property_name, property_type):
    uniques = list()
    notion_data = get_db(db)
    item_count_notion = get_item_count(notion_data)
    for i in range(item_count_notion):
        data = get_property(
            i, property_name, property_type, source=notion_data)
        if data and data not in uniques:
            uniques.append(data)
    logging.info(
        f"Retrieved {len(uniques)} unique values for {property_name} from {db}.")
    return sorted(uniques)


def write_block(parent_id, content, block_type='paragraph'):
    """ appends block with chosen type and content to existing block/page.
    Type should be `"paragraph"`, `"heading_1"`, `"heading_2"`, `"heading_3"`,
    "bulleted_list_item"`, `"numbered_list_item"`, `"to_do"`, or `"toggle"`.
"""
    base_url = f"https://api.notion.com/v1/blocks/{parent_id}/children"
    if block_type == 'link':
        data_raw = {
            "children": [
                {
                    "object": "block",
                    "type": 'paragraph',
                    'paragraph': {
                        "rich_text": [{"type": "text",
                                       "text": {"content": content,
                                                "link": {'type': 'url',
                                                         'url': content}}}]
                    }
                }]}
    else:
        data_raw = {
            "children": [
                {
                    "object": "block",
                    "type": block_type,
                    block_type: {
                        "rich_text": [{"type": "text",
                                       "text": {"content": content}}]
                    }
                }]}
    data = json.dumps(data_raw)
    r = requests.patch(base_url, headers=get_header(), data=data)
    # print(r.json())
    # integrate check here?
    logging.info(f"...wrote {block_type}: '{content}' to notion.")
    return r.json()['results'][-1]['id']  # test


def write_to_db(data_dict: dict, db_id: str):
    """sends a json-formatted dictionary as a request (add to database) to notion api"""
    create_url = "https://api.notion.com/v1/pages/"
    add_parent_id_to_request_dict(data_dict, db_id)  # test
    data = json.dumps(data_dict)
    res = requests.post(create_url, headers=get_header(), data=data)
    error_check_response(res)


def write_property_to_page(page_id, property_name, content, property_type='rich_text'):
    """Write a value to a property field in a notion page"""
    base_url = "https://api.notion.com/v1/pages/"
    if property_type == 'rich_text':
        data_raw = {
            'properties':
                {property_name: {'rich_text': [
                    {'text': {'content': content}}]}}
        }
    elif property_type == 'url':
        data_raw = {
            "properties":
                {property_name: {"url": content}}}

    data = json.dumps(data_raw)
    r = requests.patch(base_url + page_id, headers=get_header(), data=data)
    error_check_response(r)
    logging.info(f"...wrote {property_name} to notion.")
