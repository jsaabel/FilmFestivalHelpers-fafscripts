from flask import render_template, Blueprint, flash, url_for, redirect, request
from flask_login import current_user, login_required
# from fafscripts.models import (CatalogueCategoryChoice, DatabaseID, ProgrammeChoice,
#         SeqChoice, GuestChoice, ReimbursementsChoice)
from fafscripts.modules import dbfuncs, notion as n, utils as u, notion_new as nn
from fafscripts.models import Event, EventCategory, Film, Guest, GuestCategoryChoice, Venue, FilmProgramme
from fafscripts.scripts import dba_event, dba_film, dba_guest, schedule_export_script
import logging

dbviews = Blueprint('dbviews', __name__)
logger = logging.getLogger(__name__)


def flash_success():
    flash("Script has been run :) Check the log for details.", "success")


def flash_warning():
    flash("Error: Script crashed :( Consult the log or ask your admin for"
          + " assistance.", "danger")


@dbviews.route('/events')
@login_required
def events_overview():

    return render_template('events_overview.html', title="🎭Events overview",
                           events=Event.query.all(), categories=EventCategory.query.all())


@dbviews.route('/events/<notion_id>', methods=["GET"])
@login_required
def event_view(notion_id):

    event = nn.Page(id=notion_id)
    event_data = event.get_plain_text_dict()
    if event_data.get('text-catalogue'):
        event_data['text-catalogue'] = u.rich_text_to_html(
            event.get_rich_text('text-catalogue'))
    if event_data.get('description-functionaries'):
        event_data['description-functionaries'] = u.rich_text_to_html(
            event.get_rich_text('description-functionaries'))
    if event_data.get('description-schedule'):
        event_data['description-schedule'] = u.rich_text_to_html(
            event.get_rich_text('description-schedule'))
    venue_id = event.get_list('venue')
    venue = {}
    if venue_id:
        venue = dbfuncs.notion_ids_to_model_props(venue_id, Venue)[0]
    time = event.get_date('time')
    if time and "T" in time[0]:
        time_split = time[0].split("T")
        time = f"{time_split[0]}, {time_split[1][:5]}"

    issues = dba_event.analyze_event(event)
    error_count = len(issues['errors'])
    issue_count = len(issues['warnings']) + error_count

    return render_template("event_view.html", event_data=event_data, issues=issues,
                           issue_count=issue_count, event=event, venue=venue, time=time, error_count=error_count)


@dbviews.route('/films')
@login_required
def films_overview():
    return render_template('films_overview.html', title="🎞️ Films overview",
                           programmes=FilmProgramme.query.all(), films=Film.query.all())


@dbviews.route('/films/<notion_id>', methods=["GET"])
@login_required
def film_view(notion_id):

    f = nn.Page(id=notion_id)
    # data_source = n.get_page(notion_id)
    film_data = f.get_plain_text_dict()
    programme_ids = f.get_list('film-programmes')
    programmes = [FilmProgramme.query.filter_by(
        notion_id=id).first().name for id in programme_ids]
    film_data['programmes'] = u.list_to_comma_separated(programmes)
    if film_data.get('bio'):
        film_data['bio'] = u.rich_text_to_html(f.get_rich_text('bio'))
    if film_data.get('synopsis'):
        film_data['synposis'] = u.rich_text_to_html(
            f.get_rich_text('synopsis'))
    # eventive = False if not film_data.get('eventive-id') else True

    issues = dba_film.analyze_film(f)
    error_count = len(issues['errors'])
    issue_count = len(issues['warnings']) + error_count

    return render_template("film_view.html", film_data=film_data, issues=issues,
                           issue_count=issue_count, error_count=error_count)


@dbviews.route('/guests')
@login_required
def guests_overview():
    return render_template('guests_overview.html', title="🤹 Guests overview",
                           guests=Guest.query.all(),
                           guest_categories=GuestCategoryChoice.query.all())


@dbviews.route('/guests/<notion_id>', methods=["GET"])
@login_required
def guest_view(notion_id):

    guest = nn.Page(id=notion_id)
    guest_data = guest.get_plain_text_dict()
    bio = u.rich_text_to_html(guest.get_rich_text('bio-eng'))
    events_attendee = dbfuncs.notion_ids_to_model_props(
        guest.get_list('events-attendees'), Event)
    # id_to_name_attendee = dbfuncs.notion_ids_to_model_props(events_attendee, Event)
    events_functionary = dbfuncs.notion_ids_to_model_props(
        guest.get_list('events-functionaries'), Event)
    # id_to_name_functionary = dbfuncs.notion_ids_to_model_props(events_functionary, Event)

    # (only for issues)
    data_dict_events = dict()
    # retrieved event db has to be sorted chronologically
    nn.add_sorts_to_request_dict(data_dict_events, 'Time', 'ascending')
    events_data = nn.get_db('events', data_dict=data_dict_events)

    issues = dba_guest.analyze_guest(guest, events_data)
    issue_count = len(issues['messages'] +
                      issues['warnings'] + issues['errors'])

    return render_template("guest_view.html", guest_data=guest_data, issues=issues,
                           issue_count=issue_count, bio=bio, events_attendee=events_attendee,
                           events_functionary=events_functionary)


@dbviews.route('/schedule_preview/<notion_id>', methods=["GET"])
@login_required
def schedule_preview(notion_id):
    logger.info(f"Trying to generate schedule preview for id {notion_id}.")
    try:
        guest = Guest.query.filter_by(notion_id=notion_id).first()
        logger.info(f"Matched notion id to {guest.name}.")
        schedule_export_script.main(
            guest.name, all=False, pdf=False, upload=False)
        flash_success()
        logger.debug(f"schedule_export_script.py successfully executed.")
        html = u.docx_to_html(f"schedule_temp_{notion_id}.docx")
        return render_template("schedule_preview.html", html=html,
                               notion_id=notion_id, title="Schedule preview", notion_url=guest.notion_url)
    except Exception as e:
        flash_warning()
        logger.error(
            f"schedule_export_script.py crashed under execution: {e}.")
        return redirect(request.referrer)
