from fafscripts.modules import eventive as e, utils as u
from fafscripts.scripts import make_pass
from fafscripts.models import PassBucket
import logging

logger = logging.getLogger(__name__)


def main(bucket_ids: list, sort, day_diff):

    r = u.get_results_dict()
    for bucket_id in bucket_ids:

        bucket_name = PassBucket.query.filter_by(
            eventive_id=bucket_id).first().name
        logger.info(f"Exporting {bucket_name}...")
        passes = e.get_passes(bucket_id)
        logger.info(f"Retrieved {len(passes['passes'])} passes.")

        for pass_json in passes['passes']:

            temp_dict = make_pass.main(pass_json, sort, day_diff)
            if temp_dict:
                for error in temp_dict['errors']:
                    r['errors'].append(error)
                for warning in temp_dict['warnings']:
                    r['warnings'].append(warning)
                for message in temp_dict['messages']:
                    r['messages'].append(message)

    return r
