from fafscripts.modules import notion_new as n, utils as u
import logging


def main():
    logger = logging.getLogger(__name__)
    logger.info("Executing.")
    pass_buckets = n.get_db('pass_buckets')

    for pb_json in pass_buckets['results']:

        pb = n.Page(json_obj=pb_json)
        files = pb.get_list('template')
        if not files:
            continue

        eventive_url = pb.get_text('url')
        id = eventive_url.split('/')[-1]

        u.save_first_img(files, file_name=f"files/pass_templates/{id}")
