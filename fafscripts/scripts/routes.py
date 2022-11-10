from flask import (Blueprint, render_template,
                   url_for, flash, redirect, request)
from flask_login import current_user, login_required
from fafscripts.scripts.forms import (DBChoiceForm,
                                      GuestChoiceForm, CatalogueCategoryChoiceForm, ReimbursementsForm,
                                      SimpleSubmitForm, SimpleInputForm, PassBucketChoiceForm,
                                      ProgrammeChoiceForm, VenueChoiceForm, VirtualScreeningForm)

from fafscripts.scripts import (notion_to_catalogue, database_analyzer,
                                image_export, indesign_data_merge, issue_aaa_pass, film_list_export_script,
                                schedule_export_script, hotel_list_export, make_pass, make_virtual_screening,
                                make_virtual_event, norwegian_html,
                                notion_to_gcal, push_film_to_eventive, push_guest_to_wordpress,
                                reimbursements_script, download_pass_templates, pass_export_batch,
                                push_event_to_wordpress, push_event_to_eventive, tech_sheets, tech_sheet_combined,
                                update_stats, volunteer_schedules)

from fafscripts.modules import eventive
from fafscripts.models import (CatalogueCategoryChoice, FilmProgramme, GeoblockOption,
                               Guest, ReimbursementsChoice, PassBucket, Venue)
import traceback
import logging

logger = logging.getLogger(__name__)

scripts = Blueprint('scripts', __name__)


def flash_success():
    flash("Script has been run :) Check the log for details.", "success")


def flash_warning():
    flash("Error: Script crashed :( Consult the log or ask your admin for assistance.", "danger")


@scripts.route('/scripts')
@login_required
def scripts_overview():
    return render_template('scripts_overview.html')


@scripts.route('/scripts/gcal_script', methods=["GET", "POST"])
@login_required
def gcal_script():
    form = SimpleInputForm()
    gcal_link = None
    if form.validate_on_submit():
        link = form.link.data
        logger.info(
            f"{current_user.username}: SimpleInputForm validated: {link}.")
        try:
            gcal_link = notion_to_gcal.main(link)
            flash_success()
            logger.info("notion_to_gcal.py executed as intended.")
        except Exception as e:
            flash_warning()
            logger.error(f"notion_to_gcal.py crashed under execution: {e}.")
    return render_template('gcal_script.html',
                           title="🤖 Google calendar link generator", form=form, gcal_link=gcal_link)


@scripts.route('/scripts/catalogue_export', methods=["GET", "POST"])
@login_required
def catalogue_export():
    form = CatalogueCategoryChoiceForm()
    form.categories.choices = [choice.name for choice in
                               CatalogueCategoryChoice.query.all()]
    form.programmes.choices = [choice.name for choice in
                               FilmProgramme.query.all()]

    if form.validate_on_submit():

        text = form.text.data
        img = form.img.data
        categories = form.categories.data
        programmes = form.programmes.data
        logger.info(
            f"{current_user.username}: CatalogueCategoryChoiceForm validated: {categories}, {text}, {img}, {programmes}.")
        try:
            notion_to_catalogue.main(
                categories, text, img, chosen_programmes=programmes)
            logger.debug(f"notion_to_catalogue.py successfully executed.")
            flash_success()
        except Exception as e:
            flash_warning()
            # logger.error(traceback.format_exc())
            logger.error(
                f"notion_to_catalogue.py crashed under execution: {e}.")

    return render_template('catalogue_export.html', title="🤖 Catalogue export",
                           form=form)


@scripts.route('/scripts/db_analyzer', methods=["GET", "POST"])
@login_required
def db_analyzer():
    form = DBChoiceForm()
    results = None
    if form.validate_on_submit():
        db = form.db.data
        logger.debug(f"{current_user.username}: DBChoiceForm validated: {db}.")
        try:
            results = database_analyzer.main(db.lower())
            flash_success()
            logger.debug(f"database_analyzer.py successfully executed.")
        except Exception as e:
            flash_warning()
            logger.error(f"database_analyzer.py crashed under execution: {e}.")
            logger.error(traceback.format_exc())
    return render_template('db_analyzer.html', title="🤖 DB Analyzer",
                           form=form, results=results)


@scripts.route('/scripts/issue_pass')
@login_required
def issue_pass():
    email = request.args.get('email', None)
    name = request.args.get('name', None)
    message = request.args.get('mode', None)
    guest_id = request.args.get('guest_id', None)
    try:
        issue_aaa_pass.main(email, name, guest_id, message)
        flash_success()
    except Exception as e:
        flash_warning()
        logger.error(f"issue_aaa_pass.py crashed under execution: {e}")
    return redirect(request.referrer)


@scripts.route('/make_virtual_event/<notion_id>')
@login_required
def push_virtual_event(notion_id):
    try:
        make_virtual_event.main(notion_id)
        flash_success()
    except Exception as e:
        flash_warning()
        logger.error(f"make_virtual_event.py crashed under exection: {e}")
    return redirect(request.referrer)


@scripts.route('/scripts/make_virtual_screening', methods=["GET", "POST"])
@login_required
def make_virtual_screening_script():
    form = VirtualScreeningForm()
    form.programmes.choices = [
        programme.name for programme in FilmProgramme.query.all()]
    form.geo_blocking.choices = [
        choice.name for choice in GeoblockOption.query.all()]

    if form.validate_on_submit():
        programmes = form.programmes.data
        geo_blocking = form.geo_blocking.data
        logger.debug(
            f"{current_user.username}: VirtualScreeningForm validated: {programmes}, {geo_blocking}.")
        try:
            make_virtual_screening.main(programmes, geo_blocking)
            logger.debug(f"make_virtual_screening.py successfully executed.")
            flash_success()
        except Exception as e:
            flash_warning()
            logger.error(traceback.format_exc())
            logger.error(
                f"make_virtual_screening.py crashed under execution: {e}.")

    return render_template('make_virtual_screening.html', title="👾 Make virtual screening",
                           form=form)


@scripts.route('/push_event_to_eventive/')
@login_required
def event_to_eventive():
    notion_id = request.args.get('notion_id', None)
    mode = request.args.get('mode', None)
    try:
        push_event_to_eventive.main(notion_id, mode=mode)
        flash_success()
    except Exception as e:
        flash_warning()
        logger.error(
            f"push_event_to_eventive.py crashed under execution: {e}.")
        logger.error(traceback.format_exc())

    return redirect(request.referrer)


@scripts.route('/push_film_to_eventive/<notion_id>')
@login_required
def film_to_eventive(notion_id):
    try:
        push_film_to_eventive.main(notion_id)
        flash_success()
    except Exception as e:
        flash_warning()
        logger.error(f"push_film_to_eventive.py crashed under execution: {e}.")

    return redirect(request.referrer)


@scripts.route('/push_event_to_wordpress/<notion_id>')
@login_required
def event_to_wordpress(notion_id):
    try:
        push_event_to_wordpress.main(notion_id)
        flash_success()
    except Exception as e:
        flash_warning()
        logger.error(
            f"push_event_to_wordpress.py crashed under execution: {e}. (Check the database entry for completeness and try again?)")
        # logger.error(traceback.format_exc())

    return redirect(request.referrer)


@scripts.route('/push_guest_to_wordpress/<notion_id>')
@login_required
def guest_to_wordpress(notion_id):
    try:
        push_guest_to_wordpress.main(notion_id)
        flash_success()
    except Exception as e:
        flash_warning()
        logger.error(
            f"push_guest_to_wordpress.py crashed under execution: {e}.")

    return redirect(request.referrer)


@scripts.route('/scripts/hotel_list', methods=["GET", "POST"])
@login_required
def hotel_list():
    form = SimpleSubmitForm()
    results = None

    if form.validate_on_submit():
        try:
            results = hotel_list_export.main()
            flash_success()
            logger.debug(
                f"{current_user.username}: SimpleSubmitForm validated")
        except Exception as e:
            flash_warning()
            logger.error(f"hotel_list_export.py crashed under execution: {e}.")

    return render_template('hotel_list_export.html', title="🤖 Hotel list export",
                           form=form, results=results)
    return r


@scripts.route('/scripts/img_export', methods=["GET", "POST"])
@login_required
def img_export():
    form = ProgrammeChoiceForm()

    form.programme.choices = [
        choice.name for choice in FilmProgramme.query.all()]
    # form.seq.choices = [choice.name for choice in SeqChoice.query.all()]

    if form.validate_on_submit():
        programme = form.programme.data
        # seq = form.seq.data
        seq = FilmProgramme.query.filter_by(name=programme).first().seq
        logger.debug(f"ProgrammeChoiceForm valided with parameters {programme}"
                     + f" / {seq}.")
        try:
            image_export.main(programme, seq)
            flash_success()
            logger.debug(f"image_export.py successfully executed.")
        except Exception as e:
            flash_warning()
            logger.error(f"image_export.py crashed under execution: {e}.")

    return render_template('img_export.html', title="🤖 Image export", form=form)


@scripts.route('/scripts/id_merge_export', methods=["GET", "POST"])
@login_required
def id_merge_export():
    form = ProgrammeChoiceForm()

    form.programme.choices = [
        choice.name for choice in FilmProgramme.query.all()]

    if form.validate_on_submit():
        programme = form.programme.data
        seq = FilmProgramme.query.filter_by(name=programme).first().seq
        logger.debug(f"{current_user.username}: ProgrammeChoiceForm"
                     + " validated with parameters {programme}" + f" / {seq}.")
        try:
            indesign_data_merge.main(programme, seq)
            flash_success()
            logger.debug(f"indesign_data_merge.py successfully executed.")
        except Exception as e:
            flash_warning()
            logger.error(
                f"indesign_data_merge.py crashed under execution: {e}.")

    return render_template('id_merge_export.html', title="🤖 Merge file export", form=form)


@scripts.route('/scripts/film_list_export', methods=["GET", "POST"])
@login_required
def film_list_export():
    form = ProgrammeChoiceForm()

    form.programme.choices = [
        choice.name for choice in FilmProgramme.query.all()]

    if form.validate_on_submit():
        programme = form.programme.data
        seq = FilmProgramme.query.filter_by(name=programme).first().seq
        norwegian_mode = form.norwegian_mode.data
        logger.debug(f"{current_user.username}: ProgrammeChoiceForm validated"
                     + f" with parameters {programme},  {seq}, Norwegian mode: {norwegian_mode}")
        try:
            film_list_export_script.main(programme, seq, norwegian_mode)
            flash_success()
            logger.debug(f"film_list_export_script.py successfully executed.")
        except Exception as e:
            flash_warning()
            logger.error(
                f"film_list_export_script.py crashed under execution: {e}.")

    return render_template('film_list_export.html', title="🤖 Film list export",
                           form=form)


@scripts.route('/scripts/reimbursements', methods=["GET", "POST"])
@login_required
def reimbursements():
    form = ReimbursementsForm()
    form.name.choices = [
        choice.name for choice in ReimbursementsChoice.query.all()]

    if form.validate_on_submit():
        name = form.name.data
        address = form.address.data
        account_number = form.account_number.data
        id_number = form.id_number.data
        export_files = form.export_files.data
        logger.debug(f"{current_user.username}: ReimbursementsForm validated with parameters {name},"
                     + f" {address}, {account_number}, {id_number}, {export_files}")
        try:
            reimbursements_script.main(name, address, account_number, id_number,
                                       export_files)
            flash_success()
            logger.debug(f"reimbursements_script.py successfully executed.")
        except Exception as e:
            flash_warning()
            logger.error(
                f"reimbursements_script.py crashed under execution: {e}.")

    return render_template('reimbursements.html', title="🤖 Reimbursements",
                           form=form)


@scripts.route('/scripts/schedule_export', methods=["GET", "POST"])
@login_required
def schedule_export():
    form = GuestChoiceForm()
    form.name.choices = [choice.name for choice in Guest.query.all()]

    if form.validate_on_submit():
        guest = form.name.data
        all = form.all.data
        pdf = form.pdf.data
        logger.debug(f"{current_user.username}: GuestChoiceForm validated with parameters {guest}"
                     + f" , all={all}, pdf={pdf}")
        try:
            schedule_export_script.main(guest, all=all, pdf=pdf)
            flash_success()
            logger.debug(f"schedule_export_script.py successfully executed.")
        except Exception as e:
            flash_warning()
            logger.error(
                f"schedule_export_script.py crashed under execution: {e}.")
            logger.error(traceback.format_exc())

    return render_template('schedule_export.html', title="🕰️ Schedule export",
                           form=form)


@scripts.route('/scripts/schedule_export/<notion_id>')
@login_required
def schedule_export_with_id(notion_id):
    logger.info(f'{current_user}: Schedule export with id {notion_id}')
    try:
        guest = Guest.query.filter_by(notion_id=notion_id).first()
        logger.info(f"Matched notion id to {guest.name}.")
        schedule_export_script.main(guest.name, all=False, pdf=False)
        flash_success()
        logger.debug(f"schedule_export_script.py successfully executed.")
    except Exception as e:
        flash_warning()
        logger.error(
            f"schedule_export_script.py crashed under execution: {e}.")
        # logger.error(traceback.format_exc())

    return redirect(request.referrer)


@scripts.route('/scripts/make_pass/', methods=["GET", "POST"])
@login_required
def pass_maker():

    form = SimpleInputForm()
    results = None
    if form.validate_on_submit():
        url = form.link.data
        logger.info(
            f"{current_user.username}: SimpleInputForm validated: {url}.")
        try:
            pass_id = url.split('=')[-1]
            pass_json = eventive.get_pass(pass_id)
            results = make_pass.main(pass_json)
            flash_success()
        except Exception as e:
            flash_warning()
            logger.error(f"make_pass.py crashed under execution: {e}.")

    return render_template("pass_script.html", form=form, title="🤖 Pass script (single)", results=results)


@scripts.route('/scripts/pass_export_batch', methods=["GET", "POST"])
@login_required
def pass_export_batch_route():

    form = PassBucketChoiceForm()
    form.pass_buckets.choices = [
        pass_bucket.name for pass_bucket in PassBucket.query.all()]
    form.day_diff.choices = [i for i in range(-1, 31)]
    form.sort.choices = ["name", "date"]
    results = None

    if form.validate_on_submit():
        pass_buckets = form.pass_buckets.data
        day_diff = int(form.day_diff.data)
        sort = form.sort.data
        pass_bucket_ids = [PassBucket.query.filter_by(
            name=pass_bucket).first().eventive_id for pass_bucket in pass_buckets]
        logger.info(
            f"{current_user.username}: PassBucketChoiceForm validated: {pass_buckets}, {sort}, {day_diff}.")
        logger.info(f"Matched ids: {pass_bucket_ids}.")
        try:
            results = pass_export_batch.main(
                pass_bucket_ids, sort=sort, day_diff=day_diff)
            flash_success()
        except Exception as e:
            flash_warning()
            logger.error(f"pass_export_batch.py crashed under execution: {e}.")
            logger.error(traceback.format_exc())

    return render_template("pass_script_batch.html", form=form, title="🤖 Pass script (batch)",
                           results=results)


@scripts.route('/scripts/tech_sheets', methods=["GET", "POST"])
@login_required
def export_tech_sheets():

    form = VenueChoiceForm()
    form.venues.choices = [venue.name for venue in Venue.query.all()]

    if form.validate_on_submit():
        venue_names = form.venues.data
        venue_ids = [Venue.query.filter_by(
            name=venue_name).first().notion_id for venue_name in venue_names]
        combine = form.combine.data

        if not combine:

            try:
                for venue_id in venue_ids:
                    tech_sheets.main(venue_id)
                flash_success()
            except Exception as e:
                flash_warning()
                logger.error(f"tech_sheets.py crashed under execution: {e}.")
                logger.error(traceback.format_exc())

        else:

            try:
                tech_sheet_combined.main(venue_ids)
                flash_success()
            except Exception as e:
                flash_warning()
                logger.error(
                    f"tech_sheets_combined.py crashed under execution: {e}.")
                logger.error(traceback.format_exc())

    return render_template("tech_sheets.html", form=form, title="🤖 Tech sheet export")


@scripts.route('/scripts/update_pass_templates')
@login_required
def update_pass_templates():
    try:
        download_pass_templates.main()
        flash_success()
    except Exception as e:
        flash_warning()
        logger.error(
            f"download_pass_templates.py crashed under execution: {e}.")
    return redirect(request.referrer)


@scripts.route('/scripts/update_stats', methods=["GET", "POST"])
@login_required
def stats_update():

    form = SimpleSubmitForm()
    if form.validate_on_submit():
        try:
            update_stats.main()
            flash_success()
        except Exception as e:
            flash_warning()
            logger.error(f"update_stats.py crashed under execution: {e}.")

    return render_template("update_stats.html", form=form, title="🤖 Update statistics")


@scripts.route('/scripts/volunteer_schedules', methods=["GET", "POST"])
@login_required
def volunteer_schedules_script():

    results = None
    form = SimpleSubmitForm()
    if form.validate_on_submit():
        try:
            results = volunteer_schedules.main()
            flash_success()
        except Exception as e:
            flash_warning()
            logger.error(
                f"volunteer_schedules.py crashed under execution: {e}.")
            logger.error(traceback.format_exc())

    return render_template("volunteer_schedules.html", form=form, title="🤖 Volunteer schedules", results=results)


@scripts.route('/scripts/norwegian_html', methods=["GET", "POST"])
@login_required
def norwegian_html_export():

    form = SimpleSubmitForm()
    if form.validate_on_submit():
        try:
            norwegian_html.main()
            flash_success()
        except Exception as e:
            flash_warning()
            logger.error(f"norwegian_html.py crashed under execution: {e}.")

    return render_template("norwegian_html.html", title="🖨️ Norwegian html export", form=form)
