import json
import requests
import urllib.request
from modules import secrets, utils as u

# database ids
db_ids = {
    'films': '5f44638545ed42e7ac97fdd5a7a2dcaf',
    'commissioned': '5f44638545ed42e7ac97fdd5a7a2dcaf',
    'catalogue_overview': '51f738ae5d1946d7aaf1e20fa0fe3d10',
    'guests': 'd6467f1918dd4a848b78023b618a646c',
    'events': 'b0b2e7b6ee4c41fe9b1901413bde54f0',
    'venues': '35655dc994f149698058fcc878f81e93',
    'virtual': 'e8b4ce4220634c4ca3e3028f769157b6',
    'watchlist': 'bf8b7021d94544aca211d96a02c6bba4',
    'receipts': 'e05c004ce7004a679d12f11c30b6aa71',
    'supporters': '41b7de4ac69e45d9b4eaf95814bcbe43',
    'test': '53a2ddbe3ca448e58c53283ef15f02d0',
    'tags': '4236304059cc48d98ea0a28a9d5c5fe9',
}

# programme tags
programme_tags = ['Best of International Short Film 1', 'Best of International Short Film 2', 'NBC: Student Film',
                  'NBC: Short Film 1', 'NBC: Short Film 2', 'NBC: Commissioned Film', 'Abstraction at hoi polloi',
                  "NBC: Children's Film", 'Midnight Madness at TÆPS', 'Kindergarten Films', 'Animated Science',
                  'Significant: The Animation Workshop']

# header for html requests
header = {
    "Authorization": secrets.notion_api_key,
    "Notion-Version": "2021-08-16",
    "Content-Type": "application/json",
}


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


def add_property_to_request_dict(request_dict: dict, content, property_name, property_type='text'):
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


def download_file(file_url: str, target_folder: str, target_filename: str = ""):
    """download a file from provided/previously retrieved url."""
    # add file extension recognition?
    if not target_filename:
        parts = file_url.split('?')
        clean_url = parts[0]
        file_name_index = clean_url.rfind('/')
        target_filename = clean_url[file_name_index + 1:]
    print(f'\tdownloading file: {target_filename}...')
    urllib.request.urlretrieve(url=file_url, filename=f'{target_folder}/{target_filename}')


def error_check_response(response_object):
    """checks html response for errors, prints status report"""
    if 'error' not in response_object.json()['object']:
        print('\tRequest successfully executed.')
        return True
    else:
        print('\t! Error in response to request:')
        print(f"\t{response_object.json()}")
        return False


def generate_info_lines(ids: list) -> list:
    """generates infolines for use in catalogue from a list of ids (typically from relation-property)"""
    info_lines = list()
    try:
        for id in ids:
            notion_data = get_page(id)
            venue_id = get_property_from_page('Venue', 'relation', source=notion_data)
            venue_page = get_page(venue_id[0])
            venue = get_property_from_page('Name', 'title', source=venue_page)
            day = get_property_from_page('Time', 'date', source=notion_data)[0][8:10]
            time = get_property_from_page('Time', 'date', source=notion_data)[0][11:16]
            age_limit = get_property_from_page('Age Limit', 'number', source=notion_data)
            info_line = f"{day} OCT / {time} / {venue.upper()}"
            if age_limit:
                info_line += f' / AGE LIMIT: {age_limit}'
            info_lines.append(info_line)
    except (IndexError, TypeError):
        return []
    return sorted(info_lines)


def get_children(block_id):
    """retrieve a page's / block's children as json"""
    base_url = f'https://api.notion.com/v1/blocks/{block_id}/children'
    request = requests.get(base_url, headers=header)
    return request.json()


def get_children_ids(parent_id):
    """Returns a list of all children (block) ids for a specified parent page/block."""
    base_url = f"https://api.notion.com/v1/blocks/{parent_id}/children"
    r = requests.get(base_url, headers=header)
    response = r.json()
    children = list()
    for object in response['results']:
        children.append((object['id'], object['type']))
    children_counter = 0
    print('Block children retrieved:')
    for id, type in children:
        print(f'\t{id} ({type}) at index {children_counter}')
        children_counter += 1
    return children


def get_item_count(notion_db):
    """returns the number of items in a notion db/json-object."""
    item_count = 0
    for result in notion_db["results"]:
        item_count += 1
    return item_count


def get_db(db_name="films", data_dict: dict = None):
    """retrieves the desired notion-db as json object. optional: filtering and/or sorting by providing dict
     NB: keep db_ids dict updated!"""
    base_url = "https://api.notion.com/v1/databases/"
    db_id = db_ids[db_name]
    data = dict()
    if data_dict:
        data.update(data_dict)
    data = json.dumps(data)
    response = requests.post(base_url + db_id + "/query", headers=header, data=data)
    test = error_check_response(response)
    if test:
        notion_data = response.json()
        item_count = get_item_count(notion_data)
        print(f"Database ('{db_name}') loaded. {item_count} items retrieved.")
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
    for search_count in range (0, item_count_relation_db):
        if relation_db['results'][search_count]['id'] == relation_id:
            relation_name = relation_db['results'][search_count]['properties']['Name']['title'][0]['text']['content']
            return relation_name
    else:
        return relation_id


def get_page(page_id):
    """retrieve a notion page"""
    base_url = "https://api.notion.com/v1/pages/"
    request = requests.get(base_url + page_id, headers=header)
    return request.json()


def get_page_from_db(page_id: str, source="notion_data"):
    """returns the page data (properties etc) of a single page from a PREVIOUSLY RETRIEVED database."""
    for index in range(0, len(source['results'])):
        if page_id in source['results'][index]['id']:
            index_match = index
            break
    return source['results'][index_match]


# noinspection PyTypeChecker
def get_property(index, property_name=None, property_type="text", source="notion_data"):
    """returns plain text or list object for a given property from notion db API json"""
    try:
        if property_type == "text":
            if len(source['results'][index]['properties'][property_name]['rich_text']) > 1:
                res = str()
                for number in range(len(source['results'][index]['properties'][property_name]['rich_text'])):
                    res += source['results'][index]['properties'][property_name]['rich_text'][number]['text']['content']
            else:
                res = source['results'][index]['properties'][property_name]['rich_text'][0]['plain_text']
        elif property_type == "title":
            res = source['results'][index]['properties'][property_name][property_type][0]['plain_text']
        elif property_type == "number" or property_type == "checkbox" or property_type == "url":
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
    except (IndexError, KeyError, NameError):
        res = None
    # remove unnecessary spaces (Anders..)
    if isinstance(res, str):
        if res[-1] == " ":
            res = res[:-1]
    return res


# noinspection PyTypeChecker
def get_property_from_page(property_name=None, property_type="text", source="notion_data"):
    """returns plain text or list object for a given property from notion page API json"""
    try:
        if property_type == "text":
            res = source['properties'][property_name]['rich_text'][0]['plain_text']
        elif property_type == "title":
            res = source['properties'][property_name][property_type][0]['plain_text']
        elif property_type == "number" or property_type == "checkbox" or property_type == "url":
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
        elif property_type == 'files':
            res = list()
            dictionaries = source['properties'][property_name][property_type]
            for dictionary in dictionaries:
                res.append(dictionary['file']['url'])
    except (IndexError, KeyError, NameError):
        res = None
    return res


def get_text_from_child(index, source):
    """use to extract plain text from list of text-like child blocks in json"""
    property_type = str(source['results'][index]['type'])
    plain_text = source['results'][index][property_type]['text'][0]['plain_text']
    return plain_text


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
                        "text": [{"type": "text",
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
                        "text": [{"type": "text",
                                  "text": {"content": content}}]
                    }
                }]}
    data = json.dumps(data_raw)
    r = requests.patch(base_url, headers=header, data=data)
    print(r.json())
    print(f"\t...wrote {block_type}: '{content}' to notion.")


def write_to_db(data_dict: dict, db_id: str):
    """sends a json-formatted dictionary as a request (add to database) to notion api"""
    create_url = "https://api.notion.com/v1/pages/"
    data = json.dumps(data_dict)
    res = requests.post(create_url, headers=header, data=data)
    error_check_response(res)


def write_property_to_page(page_id, property_name, content, property_type='text'):
    """Write a value to a property field in a notion page"""
    base_url = "https://api.notion.com/v1/pages/"
    if property_type == 'text':
        data_raw = {
            'properties':
                {property_name: {'rich_text': [{'text': {'content': content}}]}}
        }
    elif property_type == 'url':
        data_raw = {
            "properties":
                {property_name: {"url": content}}}

    data = json.dumps(data_raw)
    r = requests.patch(base_url + page_id, headers=header, data=data)
    error_check_response(r)
    print(f"\t...wrote {property_name} to notion.")
