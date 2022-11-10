from unicodedata import category
from fafscripts.modules import notion_new as n, utils as u, dbfuncs
from fafscripts.scripts import database_analyzer as dba
from fafscripts.models import Room
import dateutil.parser


def analyze_guest(guest: n.Page, events_data) -> dict:

    r = dba.get_results_dict()

    # gd = guest.get_plain_text_dict()

    # title = gd['name']
    title = guest.get_text('name')
    url = guest.url

    # TITLE/NAME

    if not title:
        dba.add_to_results(r, title, "e", "There seems to be an empty"
                           + " database entry that should be deleted ('tbd'?.", url=url)
        return r

    if u.check_allcaps(title):
        dba.add_to_results(r, title, "w", "ALLCAPS in name.", url=url)

    # DATE LOGIC

    arrival_date = guest.get_date('arrival')
    if arrival_date:
        arrival_date_parsed = dateutil.parser.isoparse(arrival_date[0])
    check_in = guest.get_date('checkin')
    if check_in:
        check_in_parsed = dateutil.parser.isoparse(check_in[0])
    check_out = guest.get_date('checkout')
    if check_out:
        check_out_parsed = dateutil.parser.isoparse(check_out[0])
    departure_date = guest.get_date('departure-incoming')
    if departure_date:
        departure_date_parsed = dateutil.parser.isoparse(departure_date[0])
    departure_outgoing = guest.get_date('departure-outgoing')
    if departure_outgoing:
        departure_outgoing_parsed = dateutil.parser.isoparse(
            departure_outgoing[0])
    if check_in and not check_out:
        dba.add_to_results(
            r, title, "w", "Found check-in, but not check-out.", url=url)
    if check_out and not check_in:
        dba.add_to_results(
            r, title, "w", "Found check-out, but not check-in.", url=url)
    if check_in and check_out:
        if check_in_parsed > check_out_parsed:
            dba.add_to_results(
                r, title, "e", "Check-in date is before check-out.", url=url)
    if departure_date and not departure_outgoing:
        dba.add_to_results(
            r, title, "w", "Found incoming, but not outgoing departure.", url=url)
    if departure_outgoing and not departure_date:
        dba.add_to_results(
            r, title, "w", "Found outgoing, but not incoming departure.", url=url)
    if departure_date and departure_outgoing:
        try:
            if departure_date_parsed > departure_outgoing_parsed:
                dba.add_to_results(
                    r, title, "e", "Departure date is before arrival date.", url=url)
        except TypeError:
            dba.add_to_results(
                r, title, "w", "Missing exact arrival or departure time.", url=url)
    if arrival_date and check_in:
        if u.get_date_string(arrival_date[0], 'day') != u.get_date_string(check_in[0], 'day'):
            dba.add_to_results(
                r, title, "w", "Check-in is not on arrival date.", url=url)
    if departure_outgoing and check_out:
        if u.get_date_string(departure_outgoing[0], 'day') != u.get_date_string(check_out[0], 'day'):
            dba.add_to_results(
                r, title, "m", "Check-out is not on departure day.", url=url)

    # EVENTS CHECK

    event_ids_attendee = guest.get_list('events-attendees')
    event_ids_functionary = guest.get_list('events-functionaries')
    event_ids_combined = event_ids_attendee
    first_event_date = None
    last_event_date = None

    if event_ids_combined:
        event_ids_combined.extend(
            x for x in event_ids_functionary if x not in event_ids_attendee)
        # figure out FIRST event
        data_dict_events = dict()
        # retrieved event db has to be sorted chronologically
        n.add_sorts_to_request_dict(data_dict_events, 'Time', 'ascending')
        # item_count_events = n.get_item_count(events_data)
        # all_event_ids = [n.get_property(i, property_type="id", source=events_data) for i in range(item_count_events)]
        all_event_ids = list()
        for event_json in events_data['results']:
            event = n.Page(json_obj=event_json)
            all_event_ids.append(event.id)
        first_event_id = None
        for id in all_event_ids:
            if id in event_ids_combined:
                first_event_id = id
                break

        first_event_page_json = n.get_page_from_db(first_event_id, events_data)
        first_event_page = n.Page(json_obj=first_event_page_json)

        first_event_name = first_event_page.get_text('name')
        first_event_date = first_event_page.get_date('time')
        if first_event_date:
            first_event_date_parsed = dateutil.parser.isoparse(
                first_event_date[0])
        last_event_id = None

        all_event_ids.reverse()
        for id in all_event_ids:
            if id in event_ids_combined:
                last_event_id = id
                break

        last_event_page_json = n.get_page_from_db(last_event_id, events_data)
        last_event_page = n.Page(json_obj=last_event_page_json)
        last_event_name = last_event_page.get_text('name')
        last_event_date = last_event_page.get_date('time')
        if last_event_date:
            last_event_date_parsed = dateutil.parser.isoparse(
                last_event_date[0])

    if first_event_date and arrival_date:
        try:
            if first_event_date_parsed < arrival_date_parsed:
                dba.add_to_results(r, title, "e", f"First assigned event ({first_event_name})"
                                   + " is before arrival.", url=url)
        except TypeError:
            dba.add_to_results(r, title, "m", "Failed to check first event"
                               + " against arrival time because of missing time.", url=url)

    if last_event_date and departure_outgoing:
        try:
            if last_event_date_parsed > departure_outgoing_parsed:
                dba.add_to_results(r, title, "e", f"Last assigned event ({last_event_name})"
                                   + " is after departure.", url=url)
        except TypeError:
            dba.add_to_results(r, title, "m", "Failed to check last event"
                               + " against departure time because of missing time.", url=url)

    #
    # incoming = guest.get_text('incoming')

    # ROOM aspects
    room_id = guest.get_list('room')
    if room_id:
        room_type = dbfuncs.notion_ids_to_model_props(
            room_id, model=Room)[0]['name']
        if room_type == "None" and (check_in or check_out):
            dba.add_to_results(r, title, "e", "Check-in or check-out despite"
                               + " room type 'None'.", url=url)
        shared_with = guest.get_list('room-shared-with')
        if shared_with and room_type == 'Single':
            dba.add_to_results(
                r, title, "e", "Supposed to share room but single room assigned?", url=url)

    # no category set but other things
    # problematic, as this means guest will not be included in overview
    if any([check_in, check_out, room_id, event_ids_attendee, event_ids_functionary]) and not category:

        dba.add_to_results(
            r, title, "e", "Has certain properties, but no guest category. Assign a category to avoid issues down the road!", url=url)

    #
    # booking_ref_in = guest.get_text('booking-ref-in')
    # arrival_at = guest.get_text('arrival-at')
    # transport_incoming = guest.get_text('transport-incoming')
    # outgoing = guest.get_text('outgoing')
    # booking_ref_out = guest.get_text('booking-ref-out')
    # departure_from = guest.get_text('departure-from')
    # transport_outgoing = guest.get_text('transport-outgoing')

# missing room info
# events before arrival / after departure
# check in == check out
# check out before check in
# in catalogue but no pic
# incomplete travel info
# in (important) category but no events

    return r
