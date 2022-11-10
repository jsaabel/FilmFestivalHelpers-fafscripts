from flask import render_template, Blueprint, flash, url_for, redirect, request
from flask_login import current_user, login_required
# from fafscripts.models import (CatalogueCategoryChoice, DatabaseID, ProgrammeChoice,
#         SeqChoice, GuestCategoryChoice, Guest, ReimbursementsChoice, Film, Event, Venue)
from fafscripts.modules import dbfuncs
# from fafscripts import db
import logging

main = Blueprint('main', __name__)
logger = logging.getLogger(__name__)


@main.route('/changelog')
@login_required
def changelog():
    return render_template('changelog.html', title="📯 What's new?")


@main.route('/config')  # TEMP IMPLEMENTATION
@login_required
def config():
    return render_template("config.html", title="⚙️ Config")


@main.route('/log')  # TEMP IMPLEMENTATION
@login_required
def log():
    log_entries = list()
    with open("logs/log.log", "r") as f:
        content = f.read()
        lines = content.split('\n')
        for line in lines:
            segments = line.split()
            if len(segments) < 4 or "HTTP" in line:
                continue
            message = line.split("*")[-1]
            log_dict = {
                "time": segments[1],
                "category": segments[2],
                "module": segments[3],
                "time": segments[1],
                "message": message
            }
            log_entries.append(log_dict)
#
    return render_template('log.html', contents=reversed(log_entries),
                           title="📒 Log")


@main.route('/')
@main.route('/home')
@login_required
def home():
    return render_template('home.html', title=f"👋 Home")


@main.route('/rebuild_model/<model_name>', methods=["GET", "POST"])
@login_required
def rebuild_model(model_name):

    try:
        logger.info(f"{current_user}: Rebuild {model_name}.")
        dbfuncs.rebuild_model(model_name)
    except:
        flash(f"Failed to rebuild internal database {model_name}!", "danger")
        logger.warning(
            f"{current_user}: Rebuild {model_name} failed. Try to rebuild related databases first?")
        return redirect(request.referrer)

    flash(
        f"Internal database {model_name} has been updated/rebuilt.", "success")
    if request.referrer:
        return redirect(request.referrer)
    return render_template('home.html')
