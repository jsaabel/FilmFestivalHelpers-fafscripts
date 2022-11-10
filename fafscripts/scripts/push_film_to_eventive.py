from fafscripts.modules import notion_new as n, eventive as e, utils as u
from fafscripts.models import FilmProgramme
import logging

# integrate push/update functionality?


def main(notion_id: str):

    logger = logging.getLogger(__name__)
    # retrieve film data
    f = n.Page(id=notion_id)
    film_url = f.get_text('eventive-link')
    film_id = e.url_to_film_id(film_url) if film_url else None
    logger.info(f"Trying to push {f.get_text('english-title')} to Eventive.")
    synopsis = u.rich_text_to_html(f.get_rich_text('synopsis'))
    bio = u.rich_text_to_html(f.get_rich_text('bio'))
    description = f"{synopsis}<br>{bio}" if bio else synopsis
    pic = f.get_text('pic')
    poster = f.get_text('poster')
    if not poster:
        poster = pic
    # handle programme
    programme_ids = f.get_list('film-programmes')
    programmes = [FilmProgramme.query.filter_by(
        notion_id=programme_id).first() for programme_id in programme_ids]
    eventive_tags = u.comma_separated_to_list(programmes[0].eventive_tags)
    for programme in programmes:
        eventive_tags.extend(
            u.comma_separated_to_list(programme.eventive_tags))
    eventive_tags = list(set(eventive_tags))
    # determine balloting status
    unballoted = True
    for programme in programmes:
        if not programme.unballoted:
            unballoted = False
            break

    data = {
        "event_bucket": u.get_secret("EVENTIVE_BUCKET_ID"),
        "name": f.get_text('english-title'),
        "details": {
            "year": f.get_text('year'),
            "runtime": f.get_text('runtime'),
            "language": "",
            "country": f.get_text('country'),
            "premiere": "",
            "rating": "",
            "note": "",
        },
        "credits": {
            "director": f.get_text('director'),
            "screenwriter": f.get_text('screenwriter'),
            "producer": f.get_text('production'),
            "executive_producer": "",
            "co_producer": "",
            "filmmaker": "",
            "cast": "",
            "cinematographer": "",
            "editor": "",
            "animator": f.get_text('animation'),
            "production_design": "",
            "composer": "",
            "sound_design": "",
            "music": "",
        },
        "trailer_url": f.get_text('trailer-url'),
        "description": description,
        "poster_image_external": poster,
        "cover_image_external": f.get_text('pic'),
        "still_image_external": f.get_text('pic'),
        "short_description": "",
        "visibility": "hidden",
        "unballoted": unballoted,
    }

    e.add_tags_to_request_dict(data, eventive_tags)

    eventive_id = e.write_film(data, film_id=film_id)
    if eventive_id:
        eventive_link = f"https://admin.eventive.org/event_buckets/{u.get_secret('EVENTIVE_BUCKET_ID')}/films/{eventive_id}"
        f.set('eventive-link', eventive_link)
        f.write()
    else:
        logger.error("Failed to push film to Eventive.")
        raise RuntimeError

    # add film data to eventive request dict
    # ... pay special attention to eventive tags
    # ... and balloting
    # ... remember/test html functionality

    # push to eventive/make request

    # write id (+ x?) back to notion
