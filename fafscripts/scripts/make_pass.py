from fafscripts.modules import utils as u
from fafscripts.models import PassBucket
from PIL import Image, ImageDraw, ImageFont
from pyqrcode import QRCode
import os
from random import randrange
from enum import Enum
from dateutil import parser, tz
import datetime
import logging


class Color(Enum):

    WHITE = (255, 255, 255, 255)
    GREEN = (93, 137, 91, 255)
    BACKGROUND = (0, 0, 0, 0)


class XYPos(Enum):
    POS_PASS_TYPE = (43, 812)
    POS_NAME = (43, 906)
    POS_COMPANY_POSITION = (43, 941)
    POS_QR = (420, 795)


logger = logging.getLogger(__name__)


def main(pass_json, sort="name", day_diff=-1) -> dict:

    date = parser.parse(pass_json['updated_at'])
    # adjust timezone
    from_zone = tz.tzutc()
    to_zone = tz.gettz('Europe/Berlin')
    date = date.replace(tzinfo=from_zone)
    date = date.astimezone(to_zone)

    # exit if day_diff is too high
    if day_diff != -1:
        time_delta = datetime.date.today() - date.date()
        day_delta = int(time_delta.days)
        if day_delta > day_diff:
            return

    r = u.get_results_dict()

    name = pass_json['name']
    pass_id = pass_json['id']
    try:
        customer_name = pass_json['person']['name']
    except KeyError:
        logger.error(f"No customer name assigned for pass id {pass_id}!")
        u.add_to_results(r, "Unknown", "e", f"Cannot make pass for unknown customer. Click to fix!",
                         f"https://admin.eventive.org/passes/{pass_id}")
        return r

    if name.lower() == "unnamed pass":
        logger.warning(
            f"Customer {customer_name} has not provided name for pass {pass_id}. Cannot generate pass.")  # OBS TEMP
        u.add_to_results(r, customer_name, "e", "Cannot make file for unnamed pass. Click to fix!",
                         f"https://admin.eventive.org/passes/{pass_id}")
        return r

    logger.info(f"Working on pass {pass_id}.")
    name = abbreviate_name_if_needed(name)

    bucket_id = pass_json['pass_bucket']['id']
    # date_stamp = pass_json['updated_at'].split('T')[0]
    date_stamp = date.strftime("%-y-%m-%d-%H%M")
    bucket_code = pass_json['pass_bucket']['code']
    company_position = None  # temp

    bucket_model = PassBucket.query.filter_by(eventive_id=bucket_id).first()

    if pass_json['supplementary_data']:
        third_line_key = get_third_line_key(
            pass_json, third_line_prop_name=bucket_model.third_line)
        company_position = get_third_line_content(
            pass_json, prop_key=third_line_key)

    color = Color.WHITE.value if bucket_model.color == 'white' else Color.GREEN.value

    pass_img = Image.open(f"files/pass_templates/{bucket_id}.png")
    pass_img.convert("RGBA")

    qr_file = make_qr_code(pass_id, color=color)
    qr_img = Image.open(qr_file)
    pass_img.paste(qr_img, XYPos.POS_QR.value, qr_img.convert("RGBA"))
    pass_img = place_text(pass_img, bucket_model,
                          color, name, company_position)

    rand = randrange(1000)
    png_filename = f"{rand}.png"
    pass_img.save(png_filename)
    pass_img = Image.open(png_filename)
    pdf_img = pass_img.convert('RGB')
    pdf_img.save(f"{rand}.pdf")
    if sort == "date":
        filename = f"{date_stamp}_{name}_{bucket_code}.pdf"
        u.add_to_results(r, customer_name, "m", f"Uploaded {filename}", "#")
    elif sort == "name":
        filename = f"{name.split()[-1]}_{name}_{bucket_code}.pdf"
        u.add_to_results(r, customer_name, "m", f"Uploading {filename}", "#")

    u.dropbox_upload_local_file(
        f"{rand}.pdf", f"{u.get_secret('DROPBOX_FOLDER')}/passes/{filename}")

    # cleanup
    os.remove(qr_file)
    os.remove(png_filename)

    return r


def abbreviate_name_if_needed(original_name: str) -> str:

    if len(original_name) <= 20:
        return original_name
    name_split = original_name.split()
    if len(name_split) > 2:
        name = f"{name_split[0]} {name_split[1][0]}. {name_split[-1]}"
    elif len(name_split) == 2:
        name = f"{name_split[0][0]}. {name_split[1]}"
    # second pass
    if len(name) > 20:
        name = f"{name_split[0][0]}. {name_split[-1]}"
    logger.info(f"Abbreviated name {original_name} to {name}.")
    return name


def get_third_line_key(pass_json, third_line_prop_name) -> str:
    for d in pass_json['pass_bucket']['supplementary_data']:
        if d['label'] == third_line_prop_name:
            return d['key']


def get_third_line_content(pass_json, prop_key) -> str:
    if pass_json['supplementary_data']:
        return pass_json['supplementary_data'].get(prop_key)
    return None


def place_text(image: Image, bucket_model: PassBucket, color: Color, name, company_position=None):

    logger.info("Placing text...")
    pos_pass_type = XYPos.POS_PASS_TYPE.value
    pos_name = XYPos.POS_NAME.value
    pos_company = XYPos.POS_COMPANY_POSITION.value

    suisse_medium = ImageFont.truetype(
        "files/fonts/SuisseIntl-Medium.otf", size=25)
    suisse_regular = ImageFont.truetype(
        "files/fonts/SuisseIntl-Regular.otf", size=25)

    draw = ImageDraw.Draw(image)
    second_line = ""
    if company_position:
        # regular case
        if len(company_position) <= 30:
            first_line = company_position
        # take care of overlength lines, move all lines up
        else:
            company_position_split = company_position.split()
            if (len(company_position_split[0]) > 30):
                first_line = f"{company_position[:26]}[...]"
            else:
                first_line = ""
                i = 0
                while len(first_line) + len(company_position_split[i]) < 30:
                    first_line += f"{company_position_split[i]} "
                    i += 1
                while i < len(company_position_split):
                    second_line += f"{company_position_split[i]} "
                    i += 1
                if len(second_line) > 30:
                    second_line = f"{second_line[:26]}[...]"

                if second_line:
                    pos_name = (43, 871)
                    pos_company = XYPos.POS_NAME.value
                    pos_extra_line = XYPos.POS_COMPANY_POSITION.value

    draw.text(pos_pass_type, bucket_model.print_title,
              font=suisse_medium, fill=color)
    draw.text(pos_name, name, font=suisse_regular, fill=color)
    if company_position:
        draw.text(pos_company, first_line, font=suisse_regular, fill=color)
    if second_line:
        draw.text(pos_extra_line, second_line, font=suisse_regular, fill=color)

    return image


def make_qr_code(pass_id, color: Color) -> str:
    qr = QRCode(pass_id)

    rand = randrange(1000)
    filename = f"code{rand}.png"
    with open(filename, 'wb') as fstream:
        qr.png(fstream, scale=6, module_color=color, background=Color.BACKGROUND.value,
               quiet_zone=1)
    return filename
