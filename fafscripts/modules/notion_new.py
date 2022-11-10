import json
import requests
from fafscripts.modules import utils as u
from fafscripts.models import DatabaseID
# import urllib.request
from slugify import slugify
import logging

logger = logging.getLogger(__name__)


class Page():

    base_url = "https://api.notion.com/v1/pages/"
    prop_group_one = ["rich_text", "title"]
    prop_group_two = ["number", "url", "checkbox", "email", "phone_number"]

    def __init__(self, json_obj=None, id=None) -> None:
        # to-do: provide init method for 'empty' page?
        # (create empty json structure?)
        self.json = json_obj if json_obj else get_page(id)
        self.id = self.json['id']
        self.url = self.json['url']
        self.cover = None if not self.json['cover'] else self.json['cover']['external']['url']
        # self.icon = None if not self.json['icon'] else self.json['icon']['emoji']
        self.icon = self.json['icon']
        if self.icon and "external" in self.icon:
            self.icon = self.icon['external']['url']
        elif self.icon and "emoji" in self.icon:
            self.icon = self.icon['emoji']
        self.children = {"children": []}
        self.new_children = {"children": []}
        self._props = dict()
        self._modified_props = []

        for prop in self.json['properties']:
            d = {
                slugify(prop): {
                    "name": prop,
                    "type": self.json['properties'][prop]['type'],
                    "id": self.json['properties'][prop]['id'],
                }
            }
            self._props.update(d)

    def _get_prop_stub(self, slug):

        prop_name = self._props[slug]['name']
        prop_type = self._props[slug]['type']
        prop_stub = self.json['properties'][prop_name][prop_type]
        return prop_stub

    def _check_prop_exists(self, slug):

        if slug not in self._props:
            raise ValueError(f"{slug} is not a valid property.")

    def _prop_has_content(self, slug):

        prop_stub = self._get_prop_stub(slug)
        prop_type = self._props[slug]['type']
        # rich_text and (which??) others
        if not prop_stub:
            return False
        if prop_type == "rich_text" and not prop_stub[0]['text']['content']:
            return False
        return True

    def add_block(self, content, block_type='paragraph'):
        """ appends block with chosen type and content to existing block/page.
        Type should be `"paragraph"`, `"heading_1"`, `"heading_2"`, `"heading_3"`,
        "bulleted_list_item"`, `"numbered_list_item"`, `"to_do"`, or `"toggle"`.
        """
        if block_type == 'link':
            child_dict = {
                "object": "block",
                "type": 'paragraph',
                        'paragraph': {
                            "rich_text": [{"type": "text",
                                           "text": {"content": content,
                                                    "link": {'type': 'url',
                                                             'url': content}}}]
                        }
            }
        else:
            child_dict = {
                "object": "block",
                "type": block_type,
                block_type: {
                    "rich_text": [{"type": "text",
                                           "text": {"content": content}}]
                }
            }
        self.new_children['children'].append(child_dict)

    def retrieve_children(self) -> None:

        base_url = f'https://api.notion.com/v1/blocks/{self.id}/children'
        request = requests.get(base_url, headers=get_header())
        for child in request.json()['results']:
            self.children['children'].append(child)

    def get_children(self) -> dict:

        if not self.children['children']:
            return None
        return self.children['children']

    def get_date(self, slug) -> tuple:

        self._check_prop_exists(slug)
        if self._props[slug]['type'] != "date":
            raise ValueError(f"{slug}: not of type 'date'.")
        if not self._prop_has_content(slug):
            return None
        prop_stub = self._get_prop_stub(slug)
        res1 = prop_stub['start']
        res2 = prop_stub['end']
        return res1, res2

    def get_list(self, slug) -> list:

        self._check_prop_exists(slug)
        list_prop_types = ['multi_select', 'relation', 'files']
        prop_type = self._props[slug]['type']
        prop_name = self._props[slug]['name']
        if prop_type not in list_prop_types:
            raise ValueError(f"{prop_name} is not of valid list type")
        if not self._prop_has_content(slug):
            return []
        prop_stub = self._get_prop_stub(slug)

        if prop_type == "multi_select" or prop_type == "people":
            return [i['name'] for i in prop_stub]
        elif prop_type == "relation":
            relations = [i['id'] for i in prop_stub]
            if len(relations) < 24:
                return relations
            if self.json['properties'][prop_name]['has_more']:
                prop_id = self._props[slug]['id']
                full_relation_list = get_property_from_page(prop_id, self.id)
                for relation in full_relation_list['results']:
                    if relation['relation']["id"] not in relations:
                        relations.append(relation['relation']['id'])
            logger.info(
                f"Paginating {prop_name}: Retrieved {len(relations)} relations.")
            return relations

        elif prop_type == "files":
            return [i['file']['url'] for i in prop_stub]

    def get_text(self, slug) -> str:
        # slugify one more time? (allowing actual property name as argument)
        # or just 'get_text'?
        self._check_prop_exists(slug)
        if not self._prop_has_content(slug):
            return None

        res = str()
        prop_type = self._props[slug]['type']
        prop_stub = self._get_prop_stub(slug)

        if prop_type in Page.prop_group_one:
            for i in prop_stub:
                res += i['text']['content']

        elif prop_type in Page.prop_group_two:
            res = prop_stub

        elif prop_type == "select":
            res = prop_stub['name']

        elif prop_type == "multi_select":
            res = u.list_to_comma_separated([i['name'] for i in prop_stub])

        elif prop_type == "date":
            res += prop_stub['start']
            if prop_stub['end']:
                res += "/" + prop_stub['end']

        elif prop_type == "relation":
            res = u.list_to_comma_separated([i['id'] for i in prop_stub])

        elif prop_type == "people":
            res = u.list_to_comma_separated([i['name'] for i in prop_stub])

        elif prop_type == "rollup":
            # res = u.list_to_comma_separated([i for i in prop_stub['array']])
            res = None  # (temp) necessary to not break ptd functionality

        elif prop_type == "formula":
            res = prop_stub['number']

        elif prop_type == "files":
            res = u.list_to_comma_separated(
                [i['file']['url'] for i in prop_stub])

        else:
            logger.warning(f"Cannot get text for {prop_type}.")
            # raise TypeError(f"Cannot get text for {prop_type}.")

        return res

    def get_rich_text(self, slug):

        self._check_prop_exists(slug)
        if not self._prop_has_content(slug):
            return None
        if self._props[slug]['type'] != "rich_text":
            raise ValueError(f"{slug}: rich_text can only be retrieved from"
                             + " rich_text property.")

        return self._get_prop_stub(slug)

    def get_plain_text_dict(self):
        ptd = {slug: self.get_text(slug) for slug in self._props.keys()}
        ptd['id'] = self.id
        ptd['url'] = self.url
        return ptd

    def set_icon(self, icon, type="emoji"):

        if not icon:
            self.json['icon'] = None
            return
        if self.json['icon']:
            self.json['icon'].clear()
        if type == "emoji":
            self.json['icon'] = {
                "type": "emoji",
                "emoji": icon,
            }
        elif type == "external":
            self.json['icon'] = {
                "type": "external",
                "external": {
                    "url": icon,
                }
            }
        else:
            raise ValueError(f"Invalid type: {type}.")

    def set_cover(self, url):

        if not url:
            self.json['cover'] = None
            return
        self.json['cover'] = {
            "type": "external",
            "external": {"url": url},
        }

    def set(self, slug, content):

        prop_name = self._props[slug]['name']
        self._modified_props.append(prop_name)
        prop_type = self._props[slug]['type']
        prop_stub = self._get_prop_stub(slug)

        if prop_type in Page.prop_group_one:
            prop_stub.clear()
            prop_stub.append({"text": {"content": content}})

        elif prop_type in Page.prop_group_two:
            self.json['properties'][prop_name].update({prop_type: content})

        elif prop_type == "select":
            prop_stub.clear()
            prop_stub.update({'name': content})

        elif prop_type == "multi_select":
            prop_stub.clear()
            content = [content] if isinstance(content, str) else content
            for item in content:
                item_dict = {'name': item}
                prop_stub.append(item_dict)

        elif prop_type == 'date':
            import datetime
            from dateutil import tz
            tz = tz.gettz('Europe/Berlin')
            if (type(content[0]) is not datetime.datetime) and (type(content[0]) is not datetime.date):
                raise TypeError(
                    f"Invalid argument(s) provided for date property. Should be list of datetime/date objects, was {type(content[0])}.")
            start = content[0].isoformat()
            end = content[1].isoformat() if content[1] else None
            if type(content[0]) is datetime.datetime:
                start = content[0].astimezone(tz).isoformat()
            if type(content[1]) is datetime.datetime:
                end = content[1].astimezone(tz).isoformat()

            if prop_stub:
                prop_stub.clear()
            date_dict = {
                'start': start,
                'end': end,
                'time_zone': None
            }
            self.json['properties'][prop_name][prop_type] = date_dict

        # TO-DO: integrate functionality for date, relation...?

        else:
            raise TypeError(f"{prop_type} cannot be set.")

    def write(self):

        logger.debug(f"Writing to {self.id}.")
        data = {'properties': {}}
        for modified_prop in self._modified_props:
            data['properties'].update(
                {modified_prop: self.json['properties'][modified_prop]})
        r = requests.patch(Page.base_url + self.id,
                           headers=get_header(), data=json.dumps(data))
        if self.new_children['children']:
            base_url = f"https://api.notion.com/v1/blocks/{self.id}/children"
            data = json.dumps(self.new_children)
            r = requests.patch(base_url, headers=get_header(), data=data)

        # TO-DO: error check response, logging etc
        # logging.debug(f"Writing to {self.id}.")
        # r = requests.patch(Page.base_url + self.id, headers=get_header(), data=json.dumps(self.json))
        # print(r.json())
        # if self.new_children['children']:
        #     base_url = f"https://api.notion.com/v1/blocks/{self.id}/children"
        #     data = json.dumps(self.new_children)
        #     r = requests.patch(base_url, headers=get_header(), data=data)
        # TO-DO: error check response, logging etc

    # define custom exceptions within class?

    # def get_date(type/mode)
    # def get_list(slug) --- for list types .. can be worked around w. u...to_list
    # (build dict: for slug in ...: get_plain_text(slug), return dict)
    # def append_to_multi_select


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


def create_new_page_in_db(db_id=None, db_name=None):
    if not db_id:
        db_id = DatabaseID.query.filter_by(name=db_name).first().notion_id
    logger.info(f"Trying to create new page in notion db {db_id}")
    url = f"https://api.notion.com/v1/pages"
    # response = requests.post(url, headers=get_header(), data=data_json)
    data = {"parent": {"database_id": db_id}, "properties": []}
    response = requests.post(url, headers=get_header(), data=json.dumps(data))
    test = error_check_response(response)
    if not test:
        logger.error("Error in response.")
        return
    return response.json()['id']


def error_check_response(response_object):
    """checks html response for errors, prints status report"""
    if 'error' not in response_object.json()['object']:
        # logger.info('Request successfully executed.')
        return True
    else:
        logger.error('! Error in response to request.')
        return False


def get_item_count(notion_db):
    """returns the number of items in a notion db/json-object."""
    item_count = 0
    for result in notion_db["results"]:
        item_count += 1
    return item_count


def get_header():
    header = {
        "Authorization": u.get_secret("NOTION_API_KEY"),
        "Notion-Version": "2022-02-22",
        "Content-Type": "application/json",
    }
    return header


def get_db(db_name=None, data_dict=None, db_id=None):  # safe to remove "=films?"
    """retrieves the desired notion-db as json object. optional: filtering and/or sorting by providing dict
     NB: keep db_ids dict updated!"""
    base_url = "https://api.notion.com/v1/databases/"
    if not db_id:
        # db_id = db_ids[db_name]
        # logger.debug(f"Querying DatabaseID model for {db_name}.")
        try:
            db_id = DatabaseID.query.filter_by(name=db_name).first().notion_id
        except AttributeError:
            logger.error(
                f"Could not find database id for database '{db_name}'. Update config on Notion?")
            return
    data = dict()
    if data_dict:
        data.update(data_dict)
    data_json = json.dumps(data)
    # logger.info(f"Sending request to notion.")
    response = requests.post(base_url + db_id + "/query",
                             headers=get_header(), data=data_json)
    # logger.info(f"Get_db: Got back status code {response.status_code}.")
    logger.info(f"")
    test = error_check_response(response)
    if not test:
        logger.error("Error in response.")
        return

    notion_data = response.json()
    previous_request = notion_data

    # Pagination
    has_more = notion_data['has_more']
    if has_more:
        logger.info("Retrieving paginated database.")
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
        logger.warning("Empty database retrieved. Check filters?")
    logger.info(
        f"Database ('{db_name}') loaded. {item_count} items retrieved.")
    return notion_data


def get_page(page_id):
    """retrieve a notion page"""
    # logger.info(f"Retrieving page (id {page_id}).")
    # logger.info(f"Sending request to notion.")
    request = requests.get(Page.base_url + page_id, headers=get_header())
    # logger.info(f"Get_page: Got back status code {request.status_code}.")
    return request.json()


def get_page_from_db(page_id: str, source="notion_data"):
    """returns the page data (properties etc) of a single page from a PREVIOUSLY RETRIEVED database."""
    for index in range(len(source['results'])):
        if page_id in source['results'][index]['id']:
            index_match = index
            break
    return source['results'][index_match]


def get_property_from_page(property_id: str, page_id: str):
    request = requests.get(
        f"{Page.base_url}{page_id}/properties/{property_id}", headers=get_header())
    return request.json()


def page_ids_to_titles(ids: list, parent_db: str) -> dict:
    """builds dict (id:title) for ids in list from parent database"""
    # retrieve parent db
    db = get_db(parent_db)
    # figure out 'title' property
    title_prop = None
    ids_to_title = dict()
    for prop in db['results'][0]['properties']:
        if prop['type'] == 'title':
            title_prop = prop
            break
    # match ids
    for id in ids:
        for result in db['results']:
            if id == result['id']:
                title = result['properties'][title_prop]['title']['text']['content']
                ids_to_title[id] = title
                break
    return ids_to_title


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
    logger.info(f"...wrote {block_type}: '{content}' to notion.")
    return r.json()['results'][-1]['id']  # test
