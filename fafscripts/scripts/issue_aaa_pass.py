from fafscripts.modules import eventive as e, notion, notion_new as n, utils as u
import logging


def main(email, name, guest_id, message=""):
    logger = logging.getLogger(__name__)
    logger.info(f"Trying to issue AAA pass to {name}/{email}.")

    if not message:
        message = (f"Dear {name.split()[0]}, we have just issued you an All"
                   + f" Access Pass to our festival. Kindly take the time to fill in some"
                   + f" additional data we ask from our guests by following the link below"
                   + f" and clicking on 'edit details'. Should you have any questions, don't"
                   + f" hesitate to contact me at {u.get_secret('FESTIVAL_EMAIL')}.")

    try:
        req = e.issue_all_access_pass(email, message=message)
        pass_id = req['orders'][0]['passes'][0]['id']
    except KeyError:
        raise RuntimeError("Failed to issue pass for unknown reason.")

    logger.info(f"Pass has been issued (id {pass_id}.")

    logger.info(f"Trying to write pass id to Notion.")
    guest = n.Page(id=guest_id)
    guest.set('pass-id', pass_id)
    guest.write()

    logger.info(f"Trying to rename Unnamed Pass to {name}.")

    try:
        req = e.update_pass_name(pass_id=pass_id, name=name)
        pass_id = req['id']
        logger.info("Succesfully changed pass name.")
    except KeyError:
        logger.warning("Failed to update pass name! You may have to change it"
                       + " manually on Eventive.")
