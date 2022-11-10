from fafscripts.modules import notion_new as n, eventive as e, utils as u
from fafscripts.models import FilmProgramme, EventiveTag, GeoblockOption
import logging


def main(programme_names, geo_block_config):

    logger = logging.getLogger(__name__)

    try:
        template_event_id = FilmProgramme.query.filter_by(
            name=programme_names[0]).first().template_event_id
    except:
        logger.error(f"Could not find template event for {programme_names[0]}. Assign on Notion and/or"
                     + f" update internal database 'FilmProgramme' under Config.")
        raise RuntimeError("Cannot push virtual programme. Refer to log.")

    # programme retrieval
    all_film_ids = []
    for programme_name in programme_names:
        programme = FilmProgramme.query.filter_by(name=programme_name).first()
        programme_id = programme.notion_id
        seq = programme.seq
        data_dict = dict()
        n.add_filter_to_request_dict(data_dict, '🎥 Film programmes', 'relation',
                                     'contains', programme_id)
        n.add_sorts_to_request_dict(data_dict, seq)
        films = n.get_db('films', data_dict=data_dict)

        for film_json in films['results']:
            f = n.Page(json_obj=film_json)
            if not f.get_text('digital-approval'):
                continue
            f_name = f.get_text('english-title')
            eventive_url = f.get_text('eventive-link')
            if not eventive_url:
                logger.error(f"Film '{f_name}' needs to be pushed to Eventive before"
                             + f" a virtual screening can be created.")
                raise RuntimeError(
                    "Cannot create virtual screening. Refer to log.")
            eventive_id = e.film_id_from_url(eventive_url)
            all_film_ids.append(eventive_id)

    # description text etc -> retrieve from template event

    template_event = n.Page(id=template_event_id)
    template_description = template_event.get_rich_text('text-catalogue')
    if not template_description:
        logger.error(
            f"Could not find event text for {programme_names[0]}. Update on Notion.")
        raise RuntimeError("Cannot push virtual programme. Refer to log.")
    template_description = u.rich_text_to_html(template_description)
    age_limit = template_event.get_text('age-limit')
    if age_limit:
        template_description += f"<br><p>Age limit: {age_limit}</p>"

    # virtual tags
    try:
        eventive_tags_from_programme = u.comma_separated_to_list(
            FilmProgramme.query.filter_by(name=programme_names[0]).first().eventive_tags)
    except:
        logger.error(
            f"No eventive tags assigned to film programme. Update config on Notion and/or internal database 'FilmProgramme'.")
        raise RuntimeError(
            f"Cannot push virtual programme {programme_names[0]}. Refer to log.")

    virtual_tag_id = EventiveTag.query.filter_by(
        name="Virtual [GA]").first().eventive_id

    eventive_tags_from_programme.append(virtual_tag_id)
    tags = eventive_tags_from_programme

    # ballotting
    balloting = not FilmProgramme.query.filter_by(
        name=programme_names[0]).first().unballoted

    # geo blocking
    geographic_restrictions = GeoblockOption.query.filter_by(
        name=geo_block_config).first().country_codes
    geographic_restrictions = u.comma_separated_to_list(
        geographic_restrictions) if geographic_restrictions else []

    data = {
        "event_bucket": u.get_secret("EVENTIVE_BUCKET_ID"),
        "timezone": "Europe/Oslo",
        "name": programme_names[0],
        "description": template_description,
        "short_description": "",
        "is_dated": True,
        "start_time": u.get_secret("VIRTUAL_START_TIME"),
        "end_time": u.get_secret("VIRTUAL_END_TIME"),
        "tags": tags,
        "visibility": "hidden",
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
        "films": all_film_ids,
        "is_virtual": True,
        "show_in_coming_soon": True,
        "allow_preorder": True,
        "virtual_balloting_enabled": balloting,
        "use_default_event_bucket_preroll": True,
        "use_default_event_bucket_postroll": True,
        "virtual_show_donate_prompt": "default",
        "geographic_restrictions": geographic_restrictions,
    }

    logger.info(f"Geographic restrictions: {geographic_restrictions}")
    # push
    eventive_id = e.write_event(data=data)
    if eventive_id:
        logger.info("Virtual screening successfully created.")
    else:
        logger.error(
            "Was not able to create virtual screening (denied by Eventive).")
        raise RuntimeError("Request denied by Eventive.")
    # write link to notion ... where?
