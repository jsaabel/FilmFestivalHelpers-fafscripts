# NB this still uses legacy notion module
from fafscripts.models import (CatalogueCategoryChoice, DatabaseID,
                               GuestCategoryChoice, Guest, ReimbursementsChoice, Film,
                               FilmProgramme, Event, EventCategory, EventiveTag, GeoblockOption, Room, Venue,
                               PassBucket)
from fafscripts import db
from fafscripts.modules import notion as n, utils as u, eventive as e
import logging


logger = logging.getLogger(__name__)


def get_name_from_notion_id(id: str, model: db.Model) -> str:
    """Tries to find the db entry with the provided notion_id in database Model and returns its title"""

    try:
        db_entry = model.query.filter_by(notion_id=id).first()
        return db_entry.name
    except:
        logger.error(f"Could not find title for notion id {id}. "
                     + f"Internal db model {model} might have to be updated.")
        raise AttributeError(
            "Could not find corresponding internal database entry.")


def notion_ids_to_model_props(ids: list, model: db.Model) -> list:

    res = []
    if not ids:
        return res

    for id in ids:

        d = {
            "notion_id": "(unknown)",
            "name": "(unknown)",
            "notion_url": "#",
        }

        try:
            db_entry = model.query.filter_by(notion_id=id).first()
        except:  # which ExceptionType?
            logger.warning(f"Could not find local database entry for {id}."
                           + f"Local database model f'{model}' should be updated.")
            res.append(d)
            continue

        d['notion_id'] = db_entry.notion_id
        d['name'] = db_entry.name
        d['notion_url'] = db_entry.notion_url
        res.append(d)

    return res


def rebuild_model(model_name):

    logger.info(f"Trying to rebuild database model '{model_name}'.")

    model_name_to_func = {
        "CatalogueCategoryChoice": rebuild_catalogue_category_choice,
        "DatabaseID": rebuild_database_id,
        "Event": rebuild_event,
        "EventCategory": rebuild_event_category,
        "EventiveTag": rebuild_eventive_tag,
        "Film": rebuild_film,
        "FilmProgramme": rebuild_film_programme,
        "GeoblockOption": rebuild_geoblock_option,
        "Guest": rebuild_guest,
        "GuestCategoryChoice": rebuild_guest_category_choice,
        "PassBucket": rebuild_pass_bucket,
        "ReimbursementsChoice": rebuild_reimbursements_choice,
        "Room": rebuild_room,
        "Venue": rebuild_venue,
    }

    rebuild_func = model_name_to_func.get(model_name)

    if not rebuild_func:
        logger.error(f"No rebuild function found for '{model_name}'.")
        raise KeyError("No matching rebuild function found.")

    try:
        rebuild_func()
    except Exception as e:
        logger.error(f"Error encountered during execution: '{e}'.")
        raise RuntimeError

    db.session.commit()
    logger.info(f"Database model '{model_name}' was rebuilt.")


def rebuild_catalogue_category_choice():
    CatalogueCategoryChoice.__table__.drop(db.engine, checkfirst=True)
    CatalogueCategoryChoice.__table__.create(db.engine)

    catalogue_category_choices = n.get_unique_values_in_db_property('catalogue',
                                                                    'Category 1', 'select')

    for cc_choice in catalogue_category_choices:
        choice = CatalogueCategoryChoice(name=cc_choice)
        db.session.add(choice)


def rebuild_database_id():
    DatabaseID.__table__.drop(db.engine, checkfirst=True)
    DatabaseID.__table__.create(db.engine)

    notion_ids = n.get_db(db_id=u.get_secret("NOTION_DATABASES_ID"))
    item_count = n.get_item_count(notion_ids)

    for i in range(item_count):
        model_name = n.get_property(i, 'Name', 'title', source=notion_ids)
        db_id = n.get_property(i, 'notion-id', 'rich_text', source=notion_ids)
        id = DatabaseID(name=model_name, notion_id=db_id)
        db.session.add(id)


def rebuild_event():
    Event.__table__.drop(db.engine, checkfirst=True)
    Event.__table__.create(db.engine)

    data_dict = dict()
    # n.add_filter_to_request_dict(data_dict, "Guest Category", "select",
    #         "is_not_empty", True)
    n.add_sorts_to_request_dict(data_dict, "Time")
    notion_data = n.get_db('events', data_dict=data_dict)
    item_count = n.get_item_count(notion_data)

    for i in range(item_count):

        name = n.get_property(i, 'Name', 'title', source=notion_data)
        if not name:
            continue
        name = name.strip()
        notion_id = n.get_property(i, property_type="id", source=notion_data)
        notion_url = n.get_property(
            i, property_type="page_url", source=notion_data)
        category_id = n.get_property(
            i, "Category", 'relation', source=notion_data)
        if category_id:
            category = EventCategory.query.filter_by(
                notion_id=category_id[0]).first().name
        else:
            category = "[UNCATEGORIZED]"
        event = Event(name=name, notion_id=notion_id,
                      notion_url=notion_url, category=category)
        db.session.add(event)


def rebuild_event_category():
    EventCategory.__table__.drop(db.engine, checkfirst=True)
    EventCategory.__table__.create(db.engine)
    data_dict = dict()
    n.add_sorts_to_request_dict(data_dict, "Name")
    notion_data = n.get_db('event_categories', data_dict=data_dict)
    item_count = n.get_item_count(notion_data)

    # ADD UNCATEGORIZED
    event_category = EventCategory(name="[UNCATEGORIZED]", notion_id="ILLEGAL", notion_url="ILLEGAL",
                                   price=None, price_discounted=None, eventive_tags=None,
                                   wordpress_post_type=None)
    db.session.add(event_category)

    for i in range(item_count):

        name = n.get_property(i, 'Name', 'title', source=notion_data)
        if not name:
            continue
        notion_id = n.get_property(i, property_type="id", source=notion_data)
        notion_url = n.get_property(
            i, property_type="page_url", source=notion_data)
        price = n.get_property(
            i, "Default price", property_type="number", source=notion_data)
        price_discounted = n.get_property(
            i, "Default price (discounted)", property_type="number", source=notion_data)
        eventive_tags = n.get_property(
            i, 'Eventive tags', 'relation', source=notion_data)

        eventive_tags = [EventiveTag.query.filter_by(
            notion_id=id).first().eventive_id for id in eventive_tags]
        wordpress_post_type = n.get_property(
            i, 'WordPress post type', 'select', source=notion_data)
        if not wordpress_post_type:
            wordpress_post_type = "None"
        if eventive_tags:
            eventive_tags = u.list_to_comma_separated(eventive_tags)
        else:
            eventive_tags = ""
        event_category = EventCategory(name=name, notion_id=notion_id, notion_url=notion_url,
                                       price=price, price_discounted=price_discounted, eventive_tags=eventive_tags,
                                       wordpress_post_type=wordpress_post_type)
        db.session.add(event_category)


def rebuild_eventive_tag():
    EventiveTag.__table__.drop(db.engine, checkfirst=True)
    EventiveTag.__table__.create(db.engine)

    notion_data = n.get_db('eventive_tags')
    item_count = n.get_item_count(notion_data)

    for i in range(item_count):

        name = n.get_property(i, 'Name', 'title', source=notion_data)
        if not name:
            continue
        notion_id = n.get_property(i, property_type="id", source=notion_data)
        notion_url = n.get_property(
            i, property_type="page_url", source=notion_data)
        eventive_url = n.get_property(
            i, 'Url', property_type='url', source=notion_data)  # OBS
        eventive_id = e.url_to_tag_id(eventive_url)
        eventive_tag = EventiveTag(name=name, notion_id=notion_id, notion_url=notion_url,
                                   eventive_id=eventive_id)
        db.session.add(eventive_tag)


def rebuild_film():
    Film.__table__.drop(db.engine, checkfirst=True)
    Film.__table__.create(db.engine)

    data_dict = dict()
    n.add_filter_to_request_dict(data_dict, "🎥 Film programmes", "relation",
                                 "is_not_empty", True)
    n.add_sorts_to_request_dict(data_dict, "Seq")
    notion_data = n.get_db('films', data_dict=data_dict)
    page_count = n.get_item_count(notion_data)

    for i in range(page_count):
        title = n.get_property(i, 'English Title', 'title', source=notion_data)
        if not title:
            continue
        notion_id = n.get_property(i, property_type="id", source=notion_data)
        notion_url = n.get_property(
            i, property_type="page_url", source=notion_data)
        # programmes = n.get_property(i, 'Programme', 'multi_select', source=notion_data)
        programmes_ids = n.get_property(
            i, '🎥 Film programmes', 'relation', source=notion_data)
        programmes = [get_name_from_notion_id(
            id, FilmProgramme) for id in programmes_ids]
        programmes = u.list_to_comma_separated(programmes)
        seq = n.get_property(i, 'Seq', 'number', source=notion_data)
        eventive_link = n.get_property(
            i, 'eventive_link', 'url', source=notion_data)
        eventive_id = None
        if eventive_link:
            eventive_id = eventive_link.split('/')[-1]

        film = Film(name=title, notion_id=notion_id, notion_url=notion_url,
                    seq=seq, programmes=programmes, eventive_id=eventive_id)
        db.session.add(film)


def rebuild_film_programme():
    FilmProgramme.__table__.drop(db.engine, checkfirst=True)
    FilmProgramme.__table__.create(db.engine)
    data_dict = dict()
    n.add_sorts_to_request_dict(data_dict, "Name")
    notion_data = n.get_db('film_programmes', data_dict=data_dict)
    page_count = n.get_item_count(notion_data)

    for i in range(page_count):
        title = n.get_property(i, 'Name', 'title', source=notion_data)
        if not title:
            continue
        notion_id = n.get_property(i, property_type="id", source=notion_data)
        notion_url = n.get_property(
            i, property_type="page_url", source=notion_data)
        seq = n.get_property(i, 'Seq', 'select', source=notion_data)
        unballoted = n.get_property(
            i, 'Unballoted', 'checkbox', source=notion_data)
        age_limit = n.get_property(
            i, 'Age limit', 'number', source=notion_data)
        eventive_tags = n.get_property(
            i, 'Eventive tags', 'relation', source=notion_data)
        if eventive_tags:
            eventive_tags = [EventiveTag.query.filter_by(
                notion_id=id).first().eventive_id for id in eventive_tags]
            eventive_tags = u.list_to_comma_separated(eventive_tags)
        else:
            eventive_tags = ""
        template_event = n.get_property(
            i, 'template for virtual', 'relation', source=notion_data)
        template_event_id = template_event[0] if template_event else None
        film_programme = FilmProgramme(name=title, notion_id=notion_id, notion_url=notion_url,
                                       seq=seq, unballoted=unballoted, age_limit=age_limit,
                                       eventive_tags=eventive_tags, template_event_id=template_event_id)
        db.session.add(film_programme)


def rebuild_geoblock_option():
    GeoblockOption.__table__.drop(db.engine, checkfirst=True)
    GeoblockOption.__table__.create(db.engine)

    notion_data = n.get_db('geoblocking')
    item_count = n.get_item_count(notion_data)

    for i in range(item_count):

        name = n.get_property(i, 'Name', 'title', source=notion_data)
        if not name:
            continue
        notion_id = n.get_property(i, property_type="id", source=notion_data)
        notion_url = n.get_property(
            i, property_type="page_url", source=notion_data)
        country_codes = n.get_property(
            i, 'Country codes', 'multi_select', source=notion_data)
        country_codes = u.list_to_comma_separated(
            [f"country-{cc}" for cc in country_codes]) if country_codes else ""

        geoblock_option = GeoblockOption(name=name, notion_id=notion_id, notion_url=notion_url,
                                         country_codes=country_codes)
        db.session.add(geoblock_option)


def rebuild_guest():
    Guest.__table__.drop(db.engine, checkfirst=True)
    Guest.__table__.create(db.engine)

    data_dict = dict()
    # n.add_filter_to_request_dict(data_dict, "Guest Category", "select",
    #         "is_not_empty", True)
    n.add_sorts_to_request_dict(data_dict, "Name")
    notion_data = n.get_db('guests', data_dict=data_dict)
    item_count = n.get_item_count(notion_data)

    for i in range(item_count):

        name = n.get_property(i, 'Name', 'title', source=notion_data)
        if not name:
            continue
        name = name.strip()
        notion_id = n.get_property(i, property_type="id", source=notion_data)
        notion_url = n.get_property(
            i, property_type="page_url", source=notion_data)
        category = n.get_property(
            i, 'Guest Category', 'select', source=notion_data)
        if not category:
            category = "[UNCATEGORIZED]"
        guest = Guest(name=name, notion_id=notion_id, notion_url=notion_url,
                      category=category)
        db.session.add(guest)


def rebuild_guest_category_choice():
    GuestCategoryChoice.__table__.drop(db.engine, checkfirst=True)
    GuestCategoryChoice.__table__.create(db.engine)

    guest_category_choices = n.get_unique_values_in_db_property(
        'guests', 'Guest Category', 'select')

    # ADD UNCATEGORIZED
    choice = GuestCategoryChoice(name="[UNCATEGORIZED]")
    db.session.add(choice)

    for guest_category_choice in guest_category_choices:
        choice = GuestCategoryChoice(name=guest_category_choice)
        db.session.add(choice)


def rebuild_pass_bucket():
    PassBucket.__table__.drop(db.engine, checkfirst=True)
    PassBucket.__table__.create(db.engine)

    data_dict = dict()
    n.add_sorts_to_request_dict(data_dict, "Name")
    notion_data = n.get_db('pass_buckets', data_dict=data_dict)
    item_count = n.get_item_count(notion_data)

    for i in range(item_count):
        name = n.get_property(i, 'Name', 'title', source=notion_data)
        if not name:
            continue
        notion_id = n.get_property(i, property_type="id", source=notion_data)
        notion_url = n.get_property(
            i, property_type="page_url", source=notion_data)
        print_title = n.get_property(
            i, "Print title", property_type="rich_text", source=notion_data)
        eventive_url = n.get_property(
            i, "URL", property_type='url', source=notion_data)
        eventive_id = eventive_url.split('/')[-1]
        color = n.get_property(i, "Text color", 'select', source=notion_data)
        third_line = n.get_property(
            i, "Third line", 'select', source=notion_data)
        print = n.get_property(i, "print", "checkbox", source=notion_data)

        pass_bucket = PassBucket(name=name, notion_id=notion_id, notion_url=notion_url,
                                 print_title=print_title, eventive_id=eventive_id, color=color,
                                 third_line=third_line, print=print)

        db.session.add(pass_bucket)


def rebuild_reimbursements_choice():
    ReimbursementsChoice.__table__.drop(db.engine, checkfirst=True)
    ReimbursementsChoice.__table__.create(db.engine)

    reimbursements_choices = n.get_unique_values_in_db_property(
        'receipts', 'Reimburse', 'select')

    for reimbursements_choice in reimbursements_choices:
        choice = ReimbursementsChoice(name=reimbursements_choice)
        db.session.add(choice)


def rebuild_room():
    Room.__table__.drop(db.engine, checkfirst=True)
    Room.__table__.create(db.engine)
    notion_data = n.get_db('rooms')
    item_count = n.get_item_count(notion_data)
    for i in range(item_count):

        name = n.get_property(i, 'Name', 'title', source=notion_data)
        if not name:
            continue
        notion_id = n.get_property(i, property_type="id", source=notion_data)
        notion_url = n.get_property(
            i, property_type="page_url", source=notion_data)

        room = Room(name=name, notion_id=notion_id, notion_url=notion_url)
    # room_types = n.get_unique_values_in_db_property('rooms', 'Name', 'title')

        db.session.add(room)


def rebuild_venue():
    Venue.__table__.drop(db.engine, checkfirst=True)
    Venue.__table__.create(db.engine)

    data_dict = dict()
    n.add_sorts_to_request_dict(data_dict, "Name")
    notion_data = n.get_db('venues', data_dict=data_dict)
    item_count = n.get_item_count(notion_data)

    for i in range(item_count):

        name = n.get_property(i, 'Name', 'title', source=notion_data)
        if not name:
            continue

        eventive_url = n.get_property(i, "eventive_url", property_type='url')
        eventive_id = eventive_url.split("/")[-1] if eventive_url else None
        notion_id = n.get_property(i, property_type="id", source=notion_data)
        notion_url = n.get_property(
            i, property_type="page_url", source=notion_data)

        venue = Venue(name=name, notion_id=notion_id, notion_url=notion_url,
                      eventive_id=eventive_id)
        db.session.add(venue)
