from fafscripts.modules import notion_new as n, utils as u
from fafscripts.scripts import database_analyzer as dba


def analyze_film(f: n.Page):

    r = dba.get_results_dict()

    fd = f.get_plain_text_dict()

    url = f.url

    # TITLE

    title = fd['english-title']
    if not title:
        dba.add_to_results(r, title, "e", "There seems to be an empty"
                           + " database entry that should be deleted.", url=url)
        return r

    if fd['original-title']:
        if fd['original-title'] == fd['english-title']:
            dba.add_to_results(
                r, title, "e", "Original title same as title.", url=url)

    # TEXT PROPERTIES (Bio and Synopsis)

    ending_characters = ['.', '!', '?']

    if not fd['bio']:
        dba.add_to_results(r, title, "w", "Missing bio.", url=url)

    if fd['bio']:
        if u.ends_with_whitespace(fd['bio']):
            dba.add_to_results(
                r, title, "w", f"Bio ends with redundant 'space'.", url=url)
        if not u.ends_on_standard_character(fd['bio']):
            dba.add_to_results(
                r, title, "w", "Bio does not end on standard character (./!/?).", url=url)

    if not fd['synopsis']:
        dba.add_to_results(r, title, "e", "Missing synopsis.", url=url)

    if fd['synopsis']:
        if u.ends_with_whitespace(fd['synopsis']):
            dba.add_to_results(
                r, title, "w", f"Synopsis ends with redundant 'space'.", url=url)
        if not u.ends_on_standard_character(fd['synopsis']):
            dba.add_to_results(
                r, title, "w", "Synopsis does not end on standard character (./!/?).", url=url)

    if fd['bio'] and fd['synopsis']:
        if len(fd['bio'] + fd['synopsis']) > dba.get_max_text_length():
            dba.add_to_results(
                r, title, "w", "More than 1200 chars of combined text in synopsis/bio.", url=url)

    # YEAR

    if not fd['year']:
        dba.add_to_results(r, title, "e", "Missing year.", url=url)

    # CREDITS

    existing_credits = []

    if not fd['director']:
        dba.add_to_results(r, title, "e", "Missing director.", url=url)

    if fd['director']:
        existing_credits.append(fd['director'])
        if u.check_allcaps(fd['director']):
            dba.add_to_results(
                r, title, "m", "ALLCAPS in director name.", url=url)

    if not fd['production']:
        dba.add_to_results(r, title, "m", "Missing production.", url=url)

    if fd['production']:
        existing_credits.append(fd['production'])

    if fd['production'] and u.check_allcaps(fd['production']):
        dba.add_to_results(r, title, "m", "ALLCAPS in production.", url=url)

    if fd['animation']:
        existing_credits.append(fd['animation'])
        if u.check_allcaps(fd['animation']):
            dba.add_to_results(r, title, "m", "ALLCAPS in animation.", url=url)

    if not fd['animation']:
        dba.add_to_results(r, title, "m", "Missing animation.", url=url)

    if not fd['country']:
        dba.add_to_results(r, title, "e", "Missing country.", url=url)

    if fd['country']:
        existing_credits.append(fd['country'])

    # Check that credits do NOT end on ending character.
    for credit in existing_credits:
        if u.ends_on_standard_character(credit):
            dba.add_to_results(
                r, title, "w", f"Should credit property {credit} end on '{credit[-1]}'?", url=url)
        if u.ends_with_whitespace(credit):
            dba.add_to_results(
                r, title, "w", f"{credit} ends on redundant 'space'.", url=url)

    # RUNTIME

    if not fd['runtime']:
        dba.add_to_results(r, title, "e", "Missing runtime.", url=url)

    if (fd['runtime'] and len(fd['runtime']) < 3) or (fd['runtime'] and len(fd['runtime']) > 7):
        dba.add_to_results(
            r, title, "e", "Wrong formatting for runtime.", url=url)

    # PIC

    if not fd['pic']:
        dba.add_to_results(r, title, "w", "missing pic.", url=url)

    legal_filetypes = ['jpg', 'jpeg', 'png']

    if fd['pic'] and fd['pic'].split('.')[-1] not in legal_filetypes:
        dba.add_to_results(
            r, title, "e", "Invalid file type for image.", url=url)

    # encoding
    if fd['pic']:
        try:
            fd['pic'].encode('ascii')
        except UnicodeError:
            dba.add_to_results(
                r, title, "e", "Non-ASCII char found in pic url. This will most likely cause scripts to crash and should be changed!", url=url)

    # Eventive

    if not fd['eventive-link']:
        dba.add_to_results(
            r, title, "m", "Not yet pushed to Eventive.", url=url)

    return r
