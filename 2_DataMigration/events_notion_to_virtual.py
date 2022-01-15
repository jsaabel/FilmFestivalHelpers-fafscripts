# WIP 27.07.21
# integration tags/display sections?
# OBS different virtual levels etc
# experiment with/figure out geoblocking, start times, attached streams etc

from modules import eventive as e, notion as n, utils as u

tag_to_tag_id = u.get_tag_dict()  # could move this information to a separate file

# load notion db
print('Trying to retrieve notion database...')
# filter: 'make virtual'
filter_dict = dict()
n.add_filter_to_request_dict(filter_dict, 'make virtual', 'checkbox', 'equals', True)
notion_events = n.get_db('events', data_dict=filter_dict)
notion_tags = n.get_db('tags')

item_count_notion = n.get_item_count(notion_events)

for index in range(item_count_notion):
    # obtain notion id
    notion_id = n.get_property(index, property_type='id', source=notion_events)
    name = n.get_property(index, property_name='Name', property_type='title', source=notion_events)

    # determine event type
    event_type = n.get_property(index, 'Type', 'select', source=notion_events)
    # check geo-blocking
    geo_blocking = n.get_property(index, 'Geo-blocking', 'select', source=notion_events)

    description = n.get_property(index, 'Text catalogue', 'text', source=notion_events)
    if description:
        description = description.replace("<br>", "<br><br>")  # looks better on eventive. implement elsewhere?
    age_limit = n.get_property(index, 'Age Limit', 'number', source=notion_events)
    if age_limit and description:
        description = f"{description}<br><br>Age limit: {age_limit}"
    elif age_limit:
        description = f"Age limit: {age_limit}"
    balloted = n.get_property(index, 'balloted', 'checkbox', source=notion_events)

    # write events to eventive
    # add tags
    tags = list()
    if event_type == "Industry":
        tags.append(tag_to_tag_id['Virtual [Industry]'])
    elif event_type == 'Screening (Shorts)':
        tags.append(tag_to_tag_id['Virtual [GA]'])
        tags.append(tag_to_tag_id['Short film screening'])
        if balloted or "children's" in name.lower() or 'commissioned' in name.lower():
            tags.append(tag_to_tag_id['Short Film Competitions'])
        else:
            tags.append(tag_to_tag_id['Other Short Film Programmes'])
    elif event_type == 'Screening (Feature)':
        tags.append(tag_to_tag_id['Virtual [GA]'])
        tags.append(tag_to_tag_id['Feature film screening'])
    else:
        pass
    # tag_relation_ids = n.get_property(index, 'Tags', 'relation', source=notion_events)
    # for tag_relation_id in tag_relation_ids:
    #     page = n.get_page_from_db(tag_relation_id, source=notion_tags)
    #     eventive_tag_id = n.get_property_from_page('eventive_id', 'text', source=page)
    #     tags.append(eventive_tag_id)

    data_raw = {
        "event_bucket": e.event_bucket_id,
        "timezone": "Europe/Oslo",
        "name": name,
        "description": description,
        "short_description": "",
        "is_dated": True,
        "start_time": "2021-10-21T05:00:00.000Z",
        "end_time": "2021-10-27T21:55:00.000Z",
        "tags": tags,
        "visibility": "visible",
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
        "virtual_balloting_enabled": balloted,
        "use_default_event_bucket_preroll": True,
        "use_default_event_bucket_postroll": True,
        "virtual_show_donate_prompt": "default",
    }

    # add geo-blocking
    geographic_restrictions = dict()
    country_list = list()
    if geo_blocking == 'Norway':
        country_list.append("country-NO")
    elif geo_blocking == 'Nordic-Baltic':
        country_list = ["country-NO", "country-SE", "country-DK", "country-IS", "country-LV", "country-FI", "country-EE"]
    else:
        pass

    geographic_restrictions = {"geographic_restrictions": country_list}
    data_raw.update(geographic_restrictions)

    # add film(s) to request dictionary
    if event_type == 'Screening (Shorts)':
        # getting programme from rollup property (film db)
        programme = notion_events['results'][index]['properties']['Programme Tag']['rollup']['array'][0]['multi_select'][0]['name']
        data_dict = dict()
        n.add_filter_to_request_dict(data_dict, 'Programme', 'multi_select', 'contains', programme)
        n.add_sorts_to_request_dict(data_dict, 'Seq', 'ascending')
        notion_films = n.get_db('films', data_dict=data_dict)
        notion_films_count = n.get_item_count(notion_films)
        # creating list of eventive film ids and adding them to request dict
        eventive_ids = list()
        for index2 in range(0, notion_films_count):
            eventive_id = n.get_property(index2, 'eventive_id', 'text', source=notion_films)
            digital_approval = n.get_property(index2, 'Digital Approval', 'checkbox', source=notion_films)
            if not digital_approval:  # OBS make sure this is updated/correct
                pass
            else:
                eventive_ids.append(eventive_id)
        e.add_films_to_request_dict(data_raw, eventive_ids)
    # simpler process in case of feature films
    elif event_type == 'Screening (Feature)':
        notion_film_page_id = n.get_property(index, 'Film (ONE)', 'relation', source=notion_events)[0]
        notion_film_page = n.get_page(notion_film_page_id)
        eventive_film_id = n.get_property_from_page('eventive_id', 'text', source=notion_film_page)
        tag_list = list()
        tag_list.append(eventive_film_id)
        e.add_films_to_request_dict(data_raw, tag_list)
    else:
        pass

    # # live stream stuff - currently not working
    # if event_type == 'Livestream':
    #     live_stream_dict = {
    #         "films": [{
    #             "type": "livestream",
    #             "name": "Livestream Test",
    #             "start_time": "2021-09-14T22:00:00.000Z",
    #             "end_time": "2021-09-15T00:00:00.000Z",
    #             }]
    #     }
    #     data_raw.update(live_stream_dict)

    # write to eventive
    eventive_id = e.write_event(data_raw)

    # write eventive id and link back to notion
    n.write_property_to_page(page_id=notion_id, property_name='eventive_virtual_id', content=eventive_id)
    eventive_link = f"https://admin.eventive.org/event_buckets/{e.event_bucket_id}/virtual_festival/events/{eventive_id}"
    n.write_property_to_page(page_id=notion_id, property_name='virtual backend', content=eventive_link,
                             property_type='url')
