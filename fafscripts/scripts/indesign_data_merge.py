# creates tab separated txt files to be used as data sources in InDesign data merge.
from fafscripts.modules import notion_new as n, utils as u
from fafscripts.models import FilmProgramme
from random import randrange
import logging


def main(programme, seq):
    # setup
    logger = logging.getLogger(__name__)
    dropbox_folder = u.get_secret("DROPBOX_FOLDER")

    # retrieve film db
    programme_notion_id = FilmProgramme.query.filter_by(
        name=programme).first().notion_id
    data_dict = dict()
    n.add_sorts_to_request_dict(data_dict, seq)
    n.add_filter_to_request_dict(data_dict, '🎥 Film programmes', 'relation',
                                 'contains', programme_notion_id)
    notion_films = n.get_db('films', data_dict=data_dict)

    rand = randrange(1000)
    with open(f'temp{rand}.txt', 'w', encoding="utf16") as file_obj:
        # should add zfilled seq to file names!?
        # tab separated txt file, image denoted by @ character
        file_obj.write(f'film_name\ttitle_ov\tdirector\tyear\tplaytime\t@img')

        for i, film_json in enumerate(notion_films['results']):

            f = n.Page(json_obj=film_json)
            # build film_dict so .get() can be used?
            seq = str(i + 1).zfill(2)
            film_name = f.get_text('english-title')
            title_ov = f.get_text('original-title')
            if title_ov:
                title_ov = f"/ {title_ov}"
            else:
                title_ov = ""
            year = f.get_text('year')
            director = f.get_text('director')
            runtime = f.get_text('runtime')
            if runtime and len(runtime) > 1:
                runtime_split = runtime.split(":")
                runtime = f"{runtime_split[0]}m {runtime_split[1]}s"
            img_url = f.get_text('pic')
            file_name = None
            if img_url:
                file_ext = img_url.split(".")[-1]
                file_name = u.safe_file_name(f"{seq} {film_name}.{file_ext}")

            # tab separated txt file, image denoted by @ character
            file_obj.write(
                f"\n{film_name}\t{title_ov}\t{director}\t{year}\t{runtime}\t{file_name}")

        logger.info(f'file written for {programme}.')

    u.dropbox_upload_local_file(
        f'temp{rand}.txt', f'{dropbox_folder}/id_merge_files/{programme}.txt')
