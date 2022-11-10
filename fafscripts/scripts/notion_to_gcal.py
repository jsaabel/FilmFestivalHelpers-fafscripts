from fafscripts.modules import notion_new as n
import logging

logger = logging.getLogger(__name__)

# This is super hacky/ugly and NOT how it should be done, but works for now..


def url_to_id(url):
    """extract notion id from a given url."""
    if "&p=" in url:  # event is opened in standard/window view
        split = url.split('&')
        id = split[-2][2:]
        return id
    # event is opened as full page
    split = url.split('-')
    a = len(split) - 1
    return split[a]


def notion_to_gcal(notion_date):
    # convert items to desired format
    output1 = []
    for item in notion_date:
        if not item:
            pass
        else:
            new_item = item.replace('-', '').replace(':', '').replace('+', '')
            if 'T' in new_item:
                output1.append(new_item[:-10])
            else:
                output1.append(new_item)
    # generate link segment
    start_date = output1[0]
    if len(output1) == 1:  # start day and/or time only
        if "T" in output1[0]:
            end_date = start_date
            link_segment = f"{start_date}00/{end_date}00"
        else:
            end_date = str(int(start_date) + 1)
            link_segment = f"{start_date}/{end_date}"

    else:
        if "T" in output1[1]:
            end_date = output1[1]
        else:
            if output1[0] == output1[1]:
                end_date = str(int(output1[1]) + 1)
            else:
                end_date = output1[1]

        if "T" in output1[0]:
            link_segment = f"{start_date}00/{end_date}00"
        else:
            link_segment = f"{start_date}/{end_date}"

    return link_segment


def main(user_url: str) -> str:

    page_id = url_to_id(user_url)
    calendar_page = n.Page(id=page_id)

    id = calendar_page.id

# # get data and generate gcal link incl. link to notion

    event_title = calendar_page.get_text('name')

    res1, res2 = calendar_page.get_date('date')
    res = res1, res2
    event_date = notion_to_gcal(res)

    id1 = event_title.replace(' ', '+')
    id2 = id.replace('-', '')
    event_link = f"https://www.notion.so/{id1}-{id2}"
#
    link_base = "https://www.google.com/calendar/render?action=TEMPLATE"
    link_end = "&sf=true&output=xml"

    link = f"{link_base}&text={event_title}&dates={event_date}&details={event_link}" \
           f"{link_end}"

    logger.info(f"{__name__} generated link: {link}")
    return link
