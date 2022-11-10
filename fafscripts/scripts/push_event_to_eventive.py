from fafscripts.modules import eventive as e, notion_new as n, utils as u
from fafscripts.models import Film, EventCategory, EventiveTag, FilmProgramme
import logging


def main(event_id, mode="create"):

    logger = logging.getLogger(__name__)
    # parse json, log info
    event = n.Page(id=event_id)
    name = event.get_text('name')
    logger.info(f'Retrieved data for {name}.')
    pic = event.get_text('pic')
    age_limit = event.get_text('age-limit')

    # load venue
    venue_id = event.get_list('venue')
    if not venue_id:
        logger.error("Event needs to have a venue with eventive id assigned."
                     + "Update notion and/or internal database(s) and try again.")
    venue = n.Page(id=venue_id[0])
    eventive_url = venue.get_text('eventive-url')
    if not eventive_url:
        logger.error("Event needs to have a venue with eventive id assigned."
                     + " Update Notion and/or internal database(s) and try again.")
    venue_eventive_id = eventive_url.split('/')[-1]

    # quantity
    venue_default_capacity = venue.get_text('capacity')
    event_capacity = event.get_text('capacity')
    capacity = event_capacity if event_capacity else venue_default_capacity

    description_rich = event.get_rich_text('text-catalogue')
    description_html = u.rich_text_to_html(
        description_rich) if description_rich else ""

    if age_limit:
        description_html += f"<p>Age limit: {age_limit}</p>"

    # get event_dict and fill it
    data = {
        "event_bucket": u.get_secret("EVENTIVE_BUCKET_ID"),
        "name": name,
        "films": [],
        "description": description_html,
        "short_description": "",
        "venue": venue_eventive_id,
        "start_time": event.get_date('time')[0],
        "end_time": event.get_date('time')[1],
        "trailer_url": "",
        "visibility": "visible",
        "hide_tickets_button": True,
        "image_external": pic,
        "require_mailing_address": False,
        "require_phone_number": False,
        "ticket_buckets": [
            {
                "name": "General Admission",
                "price": "",
                "unlimited": False,
                "reserved_seating_category": "",
                "quantity": capacity,
                "public": True,
                "exclude_capacity": False,
                "lock_admin_only": False,
                "variants": [],
                "applicable_pass_buckets": [],
                "pass_adjusted": {}
            }],
    }

    # add tags from 'category', plus additional (union),
    eventive_tags_event_notion_ids = event.get_list('eventive-tags')
    eventive_tags_event = [EventiveTag.query.filter_by(
        notion_id=id).first().eventive_id for id in eventive_tags_event_notion_ids]
    event_category_notion_id = event.get_list('category')[0]
    event_category = EventCategory.query.filter_by(
        notion_id=event_category_notion_id).first()
    event_category_eventive_tags = []
    try:
        event_category_eventive_tags = u.comma_separated_to_list(
            event_category.eventive_tags)
    except:
        logger.warning('No eventive tags tied to event category.')
        pass
    eventive_tags = list(
        set(eventive_tags_event + event_category_eventive_tags))
    logger.info(eventive_tags)

    eventive_tags_names = [EventiveTag.query.filter_by(
        eventive_id=id).first().name for id in eventive_tags]
    logger.info(f"Applying eventive tags: {eventive_tags_names}.")

    data['tags'] = eventive_tags

    category_name = event_category.name

    # FILM SCREENINGS
    if 'screening' in category_name.lower():
        data['ticket_buckets'][0]['price'] = event_category.price * 100
        ticket_variants = [{
            "name": "Children/Seniors",
            "price": event_category.price_discounted * 100
        }]
        data['ticket_buckets'][0]['variants'] = ticket_variants

        film_ids_notion = event.get_list('film-s-one')
        if not film_ids_notion:
            logger.error(
                'No film assigned to Event. Assign film and try again.')
            raise RuntimeError(
                "Cannot proceed without film assigned to Event.")
        film_ids_eventive = []

        film = n.Page(id=film_ids_notion[0])

        if 'feature' in category_name.lower():
            # .... add related film
            logger.info("Identified feature film screening.")
            film_ids_eventive.append(Film.query.filter_by(
                notion_id=film_ids_notion[0]).first().eventive_id)

        else:
            # ... add all films in programme
            film_programme = FilmProgramme.query.filter_by(
                notion_id=film.get_list('film-programmes')[0]).first()
            data_dict = dict()
            n.add_filter_to_request_dict(
                data_dict, "🎥 Film programmes", "relation", "contains", film_programme.notion_id)
            n.add_sorts_to_request_dict(data_dict, film_programme.seq)
            films = n.get_db('films', data_dict=data_dict)
            for film_json in films['results']:
                f = n.Page(json_obj=film_json)
                eventive_link = f.get_text('eventive-link')
                if not eventive_link:
                    logger.error("Cannot push screening to Eventive unless all films in programme exist on Eventive. "
                                 + "(This is checked by looking for the 'Eventive' url property in the film db on Notion.")
                    raise RuntimeError(
                        "Missing eventive link for film in film programme.")
                eventive_id = eventive_link.split('/')[-1]
                film_ids_eventive.append(eventive_id)

        e.add_films_to_request_dict(data, film_ids_eventive)
        logger.info(
            f"Added {len(data['films'])} film(s) to event before pushing to Eventive.")

    # TICKETED EVENT
    elif 'ticket' in category_name.lower():
        data['ticket_buckets'][0]['price'] = event_category.price * 100

    elif 'free' in category_name.lower():
        data['ticket_buckets'][0]['price'] = 0

    # push
    if mode == "create":
        eventive_id = e.write_event(data=data)
    elif mode == "update":
        existing_eventive_id = event.get_text('eventive').split('/')[-1]
        eventive_id = e.update_event(data=data, event_id=existing_eventive_id)

    # write link to notion ('eventive')
    eventive_url = f"https://admin.eventive.org/event_buckets/{u.get_secret('EVENTIVE_BUCKET_ID')}/events/{eventive_id}"

    event.set('eventive', eventive_url)
    event.write()

    # pic working as expected??
