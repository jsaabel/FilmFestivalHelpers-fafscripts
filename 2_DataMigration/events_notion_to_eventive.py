from modules import eventive as e, notion as n

# OBS important improvement for 2022: Set standalone ticket sales to disabled for Industry events
# load notion dbs
print('Trying to retrieve notion databases...')
notion_events = n.get_db('events')
notion_venues = n.get_db('venues')  # eventive ids for venues are retrieved from here

item_count_notion = n.get_item_count(notion_events)

for index in range(0, item_count_notion):
    # exclude?
    export_checkbox = n.get_property(index, 'export_eventive', 'checkbox', source=notion_events)
    if not export_checkbox:
        pass
    else:
        name = n.get_property(index, property_name='Name', property_type='title', source=notion_events)
        if "(second screening)" in name:
            name = name.replace("(second screening)", "")
        # init list of tag ids
        tags_ids = list()
        # determine event type and add appropriate tag(s). OBS: SPELLING
        event_type = n.get_property(index, 'Type', 'select', source=notion_events)
        if event_type == 'Industry':
            tags_ids.append(e.tag_to_tag_id['Industry event'])
        elif event_type == 'Screening (Shorts)':
            tags_ids.append(e.tag_to_tag_id['Short film screening'])
        elif event_type == 'Screening (Feature)':
            tags_ids.append(e.tag_to_tag_id['Feature film screening'])
        elif event_type == 'Free Event':
            tags_ids.append(e.tag_to_tag_id['Free event'])
        elif event_type == 'Ticketed Event':
            tags_ids.append(e.tag_to_tag_id['Ticketed event'])

        # (CONTINUE HERE)
        # obtain notion id
        notion_id = n.get_property(index, property_type='id', source=notion_events)
        # RETRIEVE VARIOUS INFORMATION
        pic = n.get_property(index, 'Pic', 'url', source=notion_events)
        # (picture import currently not working due to API limitations. Figure out or check on status next year!
        description = n.get_property(index, 'Text catalogue', 'text', source=notion_events)
        times = n.get_property(index, 'Time', 'date', source=notion_events)
        age_limit = n.get_property(index, 'Age Limit', 'number', source=notion_events)
        if age_limit:
            description = f"{description}<br><br>Age limit: {age_limit}"
        # check for film relation
        film_relation = n.get_property(index, 'Film (ONE)', 'relation', source=notion_events)
        if film_relation:
            programme = \
                notion_events['results'][index]['properties']['Programme Tag']['rollup']['array'][0]['multi_select'][0][
                    'name']
        # retrieve venue id from venues db
        venue_notion_id = n.get_property(index, 'Venue', 'relation', source=notion_events)  # venue is a relation
        venue_notion_page = n.get_page_from_db(venue_notion_id[0], source=notion_venues)
        venue = n.get_property_from_page('eventive_id', 'text', source=venue_notion_page)  # OBS TEST MODE?

        # ticket variants / ticket bucket adjustments
        ticket_variants = []  # default value for ticket variants (equates to None)
        if 'Screening' in event_type:  # adding a ticket variant (reduced price) to screenings
            ticket_variants = [{
                "name": "Children/Seniors",
                "price": e.event_type_to_price[event_type][1]
            }]
        reserved_seating = ""  # default value for reserved seating
        ticket_quantity = n.get_property(index, 'Capacity', 'number', source=notion_events)
        if ticket_quantity == -1:  # value -1 in event db triggers reserved seating/seatmap. only use when/if necessary!
            ticket_quantity = ""
            reserved_seating = "1"

        # WRITE EVENT TO EVENTIVE
        data_raw = {
            "event_bucket": e.event_bucket_id,
            "name": name,
            "films": [],
            "description": description,
            "short_description": "",
            "venue": venue,
            "start_time": times[0],
            "end_time": times[1],
            "trailer_url": "",
            "visibility": n.get_property(index, 'visibility', 'select', source=notion_events),
            "hide_tickets_button": True,
            "image_external": pic,
            "require_mailing_address": False,
            "require_phone_number": False,
            "ticket_buckets": [
                {
                    "name": "General Admission",
                    "price": e.event_type_to_price[event_type][0],
                    "unlimited": False,
                    "reserved_seating_category": reserved_seating,
                    "quantity": ticket_quantity,
                    "public": True,
                    "exclude_capacity": False,
                    "lock_admin_only": False,
                    "variants": ticket_variants,
                    "applicable_pass_buckets": [],
                    "pass_adjusted": {}
                }],
        }

        # add tag ids to request dictionary
        data_raw.update({'tags': tags_ids})

        # add film(s) to request dictionary
        if event_type == 'Screening (Shorts)':
            # get programme
            # OBS this grabs value from rollup property, which depends on a (film db) relation property higher up.
            # choose any one film from the programme that is exclusively in this particular programme.
            # getting films for programme
            data_dict = dict()
            n.add_filter_to_request_dict(data_dict, 'Programme', 'multi_select', 'contains', programme)
            if "children's" in name.lower():
                n.add_sorts_to_request_dict(data_dict, "Seq Children's Film", 'ascending')
            else:
                n.add_sorts_to_request_dict(data_dict, "Seq", 'ascending')
            notion_films = n.get_db('films', data_dict=data_dict)
            notion_films_count = n.get_item_count(notion_films)
            # retrieving film ids and adding them to request dictionary
            eventive_ids = list()
            for index2 in range(notion_films_count):
                eventive_id = n.get_property(index2, 'eventive_id', 'text', source=notion_films)
                eventive_ids.append(eventive_id)
            e.add_films_to_request_dict(data_raw, eventive_ids)
        elif event_type == 'Screening (Feature)':
            # for feature films, the related film is chosen 'directly'
            eventive_film_id_list = []
            notion_film_page_id = n.get_property(index, 'Film (ONE)', 'relation', source=notion_events)[0]
            notion_film_page = n.get_page(notion_film_page_id)
            eventive_film_id = n.get_property_from_page('eventive_id', source=notion_film_page)
            eventive_film_id_list.append(eventive_film_id)
            e.add_films_to_request_dict(data_raw, eventive_film_id_list)
        elif event_type == 'Free Event':
            if not film_relation:
                pass
            else:
                data_dict = dict()
                n.add_filter_to_request_dict(data_dict, 'Programme', 'multi_select', 'contains', programme)
                n.add_sorts_to_request_dict(data_dict, "Seq", 'ascending')
                notion_films = n.get_db('films', data_dict=data_dict)
                notion_films_count = n.get_item_count(notion_films)
                # retrieving film ids and adding them to request dictionary
                eventive_ids = list()
                for index2 in range(notion_films_count):
                    eventive_id = n.get_property(index2, 'eventive_id', 'text', source=notion_films)
                    eventive_ids.append(eventive_id)
                e.add_films_to_request_dict(data_raw, eventive_ids)

        else:
            pass

        # write to eventive
        eventive_id = e.write_event(data_raw)

        # write eventive id and link back to notion
        n.write_property_to_page(page_id=notion_id, property_name='eventive_id', content=eventive_id)
        eventive_link = f"https://admin.eventive.org/event_buckets/{e.event_bucket_id}/events/{eventive_id}"
        n.write_property_to_page(page_id=notion_id, property_name='Physical Event_backend',
                                 content=eventive_link, property_type='url')
