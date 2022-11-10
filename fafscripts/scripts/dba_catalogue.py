from fafscripts.modules import utils as u, notion_new as n, dbfuncs
from fafscripts.scripts import database_analyzer as dba
from fafscripts.models import Event, Guest


def analyze_catalogue_page(page: n.Page) -> dict:

    r = dba.get_results_dict()

    title = page.get_text('heading')
    page_id = page.id
    url = page.url
    data_source = page.get_text('data-source')
    film_relation = page.get_list('films')
    guest_relation = page.get_list('guests')
    event_relation = page.get_list('events')
    file = page.get_list('file')
    seq = page.get_text('seq')

    # Catalog heading vs Event title / Guest name
    if data_source == "from db" and event_relation:
        event_name = dbfuncs.get_name_from_notion_id(
            id=event_relation[0], model=Event)
        if event_name != title:
            dba.add_to_results(
                r, title, "w", "Heading does not equal title of associated event.", url=url)

    elif data_source == "from db" and guest_relation:
        guest_name = dbfuncs.get_name_from_notion_id(
            id=guest_relation[0], model=Guest)
        if guest_name != title:
            dba.add_to_results(
                r, title, "w", "Heading does not equal name of associated guest.", url=url)

    # SEQ
    if not seq and data_source != '(nn)':
        dba.add_to_results(
            r, title, "w", "No sequence set or set to 0. Should be > 0.", url=url)

    # DATA SOURCE, FILES ETC
    if not data_source:
        dba.add_to_results(r, title, "w", "Data source not selected.", url=url)

    if data_source == "(nn)":
        if (guest_relation or event_relation or file):
            dba.add_to_results(r, title, "e", "'nn' chosen as data source, but"
                               + " database relation or file selected.", url=url)

    if data_source == "from db" and not (guest_relation or event_relation or film_relation):
        dba.add_to_results(
            r, title, "w", "Missing database relation.", url=url)

    if not (data_source == "from db" or data_source == "txt from event") and (guest_relation or event_relation):
        dba.add_to_results(r, title, "w", "Database relation exists, but 'from db/txt from event' is not"
                           + " chosen as data source.", url=url)

    if data_source == "from file" and not file:
        dba.add_to_results(r, title, "w", "Missing file.", url=url)

    if data_source != "from file" and file:
        dba.add_to_results(r, title, "e", "File uploaded, but 'from file' not chosen as"
                           + " data source.", url=url)

    if data_source == "txt from event" and not event_relation:
        dba.add_to_results(r, title, "e", "'txt from event' chosen as data source, but"
                           + "no event(s) assigned.", url=url)

    if file and len(file) > 1:
        dba.add_to_results(r, title, "m", "More than one file chosen. Script will"
                           + " export the first one only.", url=url)

    legal_filetypes = ['jpg', 'jpeg', 'png', 'pdf']
    if file and file[0].split('?')[0].split('.')[-1] not in legal_filetypes:
        dba.add_to_results(r, title, "e", "Invalid file type.", url=url)

    if data_source == "from page":
        page.retrieve_children()
        page_children = page.get_children()
        # page_children = n.get_children_ids(page_id)
        if not page_children:
            dba.add_to_results(
                r, title, "w", "Data source 'from page' and page is empty.", url=url)

    return r
