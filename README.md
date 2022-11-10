# Project description
This [Flask](https://flask.palletsprojects.com/en/2.2.x/) app bundles a collection of Python scripts I wrote to help streamline 
and automate various common tasks for a film festival I have been working with in recent years and makes them available to coworkers without a coding background.

Besides the time-saving aspect of automating a significant amount of menial 
and repetetive work, users benefit from 
being able to rely on a single source of truth from which information is retrieved,
avoiding otherwise common and potentially harmful mistakes made when manually transfering
information from one place to another. 

For this particular festival, most data is entered into, manipulated, stored and retrieved 
from a number of [Notion](https://www.notion.so)-databases in the runup to the event, which  
relies on the [Eventive](https://www.eventive.org) platform for the schedule, ticketing system and the streaming of films, as well as WordPress for the [public website](https://animationfestival.no). Most file handling is done in Dropbox. 
Once things are correctly configured, we have found this setup to be pleasantly flexible and budget friendly, yet powerful enough for the needs of our small to mid-size festival.

Some of the scripts make use of the various services' APIs to update 
and synchronize data between the platforms, while others perform more specialized 
tasks, such as exporting film texts and images for use in the festival catalog, generating 
personal schedules for festival guests, issuing passes or generating files for large batch print jobs.

For additional convenience, database entries can be viewed directly on the site, with relevant scripts being accessible from the sidebar.

More detailed information about the individual scripts and their operation 
can be found in their respective docstrings, as well as in the overview on the bottom of this page.

# Getting started
A word of warning: This project has evolved from what essentially were my first tries in Python scripting, which is easy to see in the codebase. Amongst others, while I enjoyed building [my own Python wrapper](fafscripts/modules/notion_new.py) for the Notion API and use it in this project, bigger and better implementations are [easily found](https://github.com/jamalex/notion-py).
Since the scripts, database views etc. are custom-written for a particular festival, virtually none of them will be ready to use
"out of the box". They do however offer solutions for a significant number of tasks that most seasoned festival
workers will be familiar with. Equipped with some curiousity and basic knowledge of the Flask stack, you might find they can serve as a point of departure or inspiration for your own festival-related coding journey.


Should you nevertheless wish to more or less directly recreate some of my solutions, the following information
about my configuration might save you some frustration:
- Working API keys for my Notion, Eventive, Wordpress, Dropbox and Eventive account, along with a number of other secrets are stored in */etc/config.json* and retrieved by the `get_secret()` function in [utils.py](fafscripts/modules/utils.py).
- Notion database ids and corresponding names are stored in an internal SQLAlchemy database. The same is true for  minimal portions of most Notion databases (names etc), helping reduce the number of requests made to the Notion API. Have a look at [models.py](fafscripts/models.py) and [dbfuncs.py](fafscripts/modules/dbfuncs.py) for an idea on how to (re)build these.
- The names (and sometimes types) of properties in Notion databases will have to match those used in the scripts 
or be adjusted accordingly.
- Some scripts depend on the existence of template files referenced in the code. In most cases, a blank file
of the appropriate format should do to get you started.
- Required third-party packages can be installed using pip: `pip install -r requirements.txt`
- When deploying to a live server, you might want to set your nginx/alternative timeout limit significantly higher than the default value to give more involved scripts enough time to finish.

# Scripts overview

The scripts and codebase can be seperated into **categories** as follows, losely
following the sequence of required tasks in the runup to the festival outlined below:

## "Development helpers"
*(Found in the outdated **2021** branch of this repo.)*
Contains a small number of files regularly used for testing purposes,
such as displaying and storing API response json-data in a reader-friendly
format ([pretty_print_json.py](0_DevelopmentHelpers/pretty_print_json.py)).

## "Database imports"
*(Found in the outdated **2021** branch of this repo.)*
The scripts in this folder are used to import data on submitted and/or selected films into the festival's 
notion database.  [ff_to_filmsdb.py](1_DatabaseImports/ff_to_filmsdb.py)
takes an excel spreadsheet with film submissions exported from 
[FilmFreeway](https://www.filmfreeway.com),
while [watchlist_to_filmsdb.py](1_DatabaseImports/watchlist_to_filmsdb.py)
moves other selected films from a preliminary database to the final working
 film database on notion.

[ff_img_import.py](1_DatabaseImports/ff_img_import.py) automatically
downloads html files for FilmFreeway film submissions, crawls them for image links
and adds these to the respective film's notion database entry.

## "Data migration"
After all data on films, events, guests and other festival assets has been worked on and finalized
in their respective Notion database, these scripts are used to push it to other platforms and formats.

This includes:
- checking the databases for common mistakes in formatting, logic etc ([database_analyzer.py](fafscripts/scripts/database_analyzer.py))
- pushing films to eventive ([push_film_to_eventive.py](fafscripts/scripts/push_film_to_eventive.py))
- pushing screening and events to eventive ([push_event_to_eventive.py](fafscripts/scripts/push_event_to_eventive.py))
and eventive virtual festival ([make_virtual_event.py](fafscripts/scripts/make_virtual_event.py) /[make_virtual_screening.py](fafscripts/scripts/make_virtual_screening.py))
- generating correctly named, sequenced and formatted .docx, .xlsx and image files to be used by the designers
of the printed catalogue ([notion_to_catalogue.py](fafscripts/scripts/notion_to_catalogue.py) and subscripts)
- pushing information to the festival website/wordpress ([push_event_to_wordpress.py](fafscripts/scripts/push_event_to_wordpress.py)/[push_guest_to_wordpress.py](fafscripts/scripts/push_guest_to_wordpress.py)

Where appropriate, backlinks to the respective entries on eventive are automatically written to
the original database(s), facilitating updates and additional functionality down the road.

## "Data updates"
*(Found in the outdated *2021* branch of this repo. Update functionality is included in the newer version references above.)* 
Scripts used to peform batch updates to all or selected films and events previously pushed to eventive.
This can include changes to the entries' visibility, their availability for purchase etc.

Files included: [eventive_update_events.py](3_DataUpdates/eventive_update_events.py),
[eventive_update_films.py](3_DataUpdates/eventive_update_films.py) (not used),
[eventive_update_virtual.py](3_DataUpdates/eventive_update_virtual.py) (not used).

## "File exports"
Scripts used to export information from Notion databases in various formats,
ranging from simple lists and spreadsheets to more complex documents:

- formatted lists of films with selected credits ([film_list_export_script.py](fafscripts/scripts/film_list_export_script.py))
- an overview (and count) of hotel rooms needed ([hotel_list_export.py](fafscripts/scripts/hotel_list_export.py))
- formatted personal event schedules for guests ([schedule_export_script.py](fafscripts/scripts/schedule_export_script.py))
- .csv files used for batch printing and image generation in Adobe InDesign ([indesign_data_merge.py](fafscripts/scripts/indesign_data_merge.py)),
- schedules and overview of technical requirements/instructions for technical staff ([tech_sheets.py](fafscripts/scripts/tech_sheet_combined.py))
- pass images with individual qr codes ([pass_export_batch.py](fafscripts/scripts/pass_export_batch.py))
- volunteer schedules ([volunteer_schedules.py](fafscripts/scripts/volunteer_schedules.py))

## "Financials"
Simplifying the process of having large numbers of private expenses reimbursed after the festival,
[reimbursements_script.py](fafscripts/scripts/reimbursements_script.py) automatically sorts entries from database,
converts foreign currencies, saves receipts with appropriate filenames and generates a reimbursement form to be submitted to the accountant.

## "Misc"
A lose collection of scripts not easily classified, in development or written to solve smaller ad-hoc tasks:
- [update_stats.py](fafscripts/scripts/update_stats.py) lists the number of sold passes and other fun stats
- [notion_to_gcal.py](fafscripts/scripts/notion_to_gcal.py) can save an event in the Notion calendar to Google calendar
- [issue_aaa_pass.py](fafscripts/scripts/issue_aaa_pass.py) can be used to issue free passes to guests

# Outlook and contact
For future iterations of this project, I am looking to incorporate more automated ticketing solutions, look into automating film logistics (down-/uploads etc.) and more. On the practical side, I plan to publish a containerized, more general and easily-deployed version that works out of the box, features appropriate unit tests and can be adjusted to individual needs much more easily. Should you be interested in exchanging ideas or have any questions, please don't hesitate to contact me through my [LinkedIn](https://www.linkedin.com/in/jonas-saabel/).
