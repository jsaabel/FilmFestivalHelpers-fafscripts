from fafscripts.modules import notion_new as n, eventive as e, utils as u
from fafscripts.models import EventiveTag, EventCategory
import logging

# next year: ask eventive about adding pic from url


def main(event_id):

    logger = logging.getLogger(__name__)

    event = n.Page(id=event_id)

    # check that the event to be pushed is not a screening
    event_category_notion_id = event.get_list('category')[0]
    event_category = EventCategory.query.filter_by(
        notion_id=event_category_notion_id).first()
    if 'screening' in f"{event_category}".lower():
        logger.error(
            "Cannot create virtual film screening from event site. Use the 'make virtual screening (film programme)' script instead.")
        raise RuntimeError(
            "Film screening events cannot be pushed to Virtual. Refer to log.")

    virtual_tag_id = EventiveTag.query.filter_by(
        name="Virtual [Industry]").first().eventive_id
    livestream_tag_id = EventiveTag.query.filter_by(
        name="Live Streams").first().eventive_id

    time = event.get_date('time')
    pic_url = event.get_text('pic')
    pic = pic_url if pic_url else ""

    data = {
        "event_bucket": u.get_secret("EVENTIVE_BUCKET_ID"),
        "timezone": "Europe/Oslo",
        "name": event.get_text('name'),
        "description": u.rich_text_to_html(event.get_rich_text('text-catalogue')),
        "short_description": "",
        "is_dated": True,
        "start_time": time[0],
        "end_time": time[1],
        "tags": [virtual_tag_id, livestream_tag_id],
        "visibility": "hidden",
        "hide_tickets_button": False,
        "require_mailing_address": False,
        "tickets_button_label": "Unlock",
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
        "virtual_balloting_enabled": False,
        "use_default_event_bucket_preroll": True,
        "use_default_event_bucket_postroll": True,
        "virtual_show_donate_prompt": "default",
        "geographic_restrictions": [],
    }

    # check if eventive_id exists
    event_url = event.get_text('eventive-virtual')
    event_id = e.url_to_film_id(event_url) if event_url else None
    # push
    eventive_id = e.write_event(data=data, event_id=event_id)
    if eventive_id:
        logger.info("Virtual screening successfully created.")
    else:
        logger.error(
            "Was not able to create virtual screening (denied by Eventive).")
        raise RuntimeError("Request denied by Eventive.")

    event.set('eventive-virtual',
              f"https://admin.eventive.org/event_buckets/{u.get_secret('EVENTIVE_BUCKET_ID')}/virtual_festival/events/{eventive_id}")
    event.write()
    logger.info("Wrote link back to Notion.")
