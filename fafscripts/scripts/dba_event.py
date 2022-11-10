from fafscripts.modules import notion_new as n, utils as u
from fafscripts.scripts import database_analyzer as dba


def analyze_event(event: n.Page) -> dict:

    r = dba.get_results_dict()

    if event.get_text('hide-from-catalogue'):
        return r

    title = event.get_text('name')
    url = event.url
    type = event.get_list('category')
    if not type:
        dba.add_to_results(r, title, "e", "No category assigned.", url=url)

    # TITLE

    if not title:
        dba.add_to_results(r, title, "e", "There seems to be an empty"
                           + " database entry that should be deleted.", url=url)
        return r

    # TIME ASPECTS

    time = event.get_date('time')
    end_time = None
    if not time:
        dba.add_to_results(r, title, "e", "Missing time.", url=url)
    else:
        end_time = time[1]
        if not end_time:
            dba.add_to_results(r, title, "e", "Missing end time.", url=url)
    if end_time:
        if u.get_date_string(end_time, 'time')[-2:] == "00":
            dba.add_to_results(
                r, title, "m", "Should not end at XX:00?", url=url)

    # VENUE

    venue = event.get_list('venue')

    if not venue:
        dba.add_to_results(r, title, "e", "Venue not set.", url=url)

    if venue:
        if len(venue) > 1:
            dba.add_to_results(
                r, title, "e", "More than one venue selected.", url=url)

    # ATTENDEE / SCHEDULE ASPECTS

    attendees = event.get_list('attendees')
    functionaries = event.get_list('functionaries')
    description_attendees = event.get_text('description-guest-schedule')
    description_functionaries = event.get_text('description-functionaries')
    if attendees and not description_attendees:
        dba.add_to_results(
            r, title, "m", "Missing schedule description.", url=url)
    if functionaries and not description_functionaries:
        dba.add_to_results(
            r, title, "m", "Missing functionary description.", url=url)
    if attendees and functionaries:
        match = False
        for attendee in attendees:
            if attendee in functionaries:
                match = True
        for functionary in functionaries:
            if functionary in attendees:
                match = True
        if match:
            dba.add_to_results(
                r, title, "m", "Same person in attendees and functionaries.", url=url)

    # CATALOG

    catalog = event.get_list('catalog')
    text_catalog = event.get_text('text-catalogue')
    text_norw = event.get_text('text-norw')
    pic = event.get_text('pic')
    valid_file_extensions = ['jpg', 'jpeg', 'png', '.jpg?dl']
    if pic and pic.replace('?dl=0', '').replace('?dl=1', '').split('.')[-1].lower() not in valid_file_extensions:
        dba.add_to_results(
            r, title, "e", "Invalid filetype for picture.", url=url)

    # THIS IS COMMENTED OUT FOR A QUICK FIX (PUSHING FEATURE FILM SCREENINGS TO EVENTIVE. SHOULD BE HANDLED PROPERLY)
    # if catalog and not text_catalog:
    #     dba.add_to_results(r, title, "e", "Missing catalogue text.", url=url)
    # if catalog and not pic:
    #     dba.add_to_results(r, title, "w", "Missing pic.", url=url)
    # if catalog and not text_norw:
    #     dba.add_to_results(r, title, "m", "Missing Norwegian text.", url=url)

    return r
