from fafscripts.modules import notion_new as n, utils as u
from fafscripts.models import FilmProgramme
import os
from random import randrange
import logging


def main(programme, seq):

    logger = logging.getLogger(__name__)

    dropbox_folder = u.get_secret("DROPBOX_FOLDER")

# retrieve film db ...
    programme_notion_id = FilmProgramme.query.filter_by(
        name=programme).first().notion_id
    logger.debug(programme_notion_id)
    data_dict = dict()
    n.add_filter_to_request_dict(data_dict, '🎥 Film programmes', 'relation', 'contains',
                                 filter_content=programme_notion_id)
    n.add_sorts_to_request_dict(data_dict, seq)
    films = n.get_db('films', data_dict=data_dict)

# loop
    for i, film_json in enumerate(films['results']):

        f = n.Page(json_obj=film_json)

        title = f.get_text('english-title')
        seq = str(i + 1).zfill(2)
        pic = f.get_text('pic')

        file_name = u.safe_file_name(f"{seq} {title}")

        if pic:
            file_ext = pic.split('.')[-1]
            u.dropbox_upload_from_url(
                pic, f"{dropbox_folder}/image_export/{programme}/{file_name}.{file_ext}")
