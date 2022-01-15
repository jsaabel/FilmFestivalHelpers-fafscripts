# Prerequisites:
# select properties (visibility) in film db are set, 'Programme' names correspond exactly with names in tags db

from modules import notion as n, eventive as e, utils as u

# compile list of programme titles
programme_titles = list()
data_dict = dict()
n.add_filter_to_request_dict(data_dict, 'Seq', 'number', 'equals', 1)
notion_data = n.get_db(db_name='films', data_dict=data_dict)
item_count_notion = n.get_item_count(notion_data)
for i in range(item_count_notion):
    programmes = n.get_property(i, 'Programme', 'multi_select', source=notion_data)
    for programme in programmes:
        if programme not in programme_titles:
            programme_titles.append(programme)

# programmes_to_export = ['Kindergarten Films', ]  # all films from programmes in this list are exported
# # watch out for spelling errors and films in multiple programmes, which will result in double entries (delete manually?)
# # make sure the eventive id/link in notion db 'belongs' to the film entry that still exists.

# retrieve film db from notion


for programme in sorted(programme_titles):

    # ask for confirmation
    export_prompt = input(f'Proceed to export {programme}? (y/n/q) > ')
    if export_prompt.lower() == 'q':
        break
    elif export_prompt.lower() == 'n':
        pass
    elif export_prompt == 'y':
        # filtering film db. run script one time for each programme, or loop through list of programme names.
        print(f"\nTrying to retrieve: {programme}...")
        data_dict = dict()
        n.add_filter_to_request_dict(data_dict, 'Programme', 'multi_select', 'contains', programme)
        notion_data = n.get_db(db_name='films', data_dict=data_dict)
        item_count_notion = n.get_item_count(notion_data)
        print(f"Database loaded. {item_count_notion} items found.")


        print("\nAssigning film data...")

        # START FILM LOOP
        for index in range(0, item_count_notion):
            # NB: make sure property names and types match those from database
            # assign film data
            film_data = {
                "title": n.get_property(index, "English Title", 'title', source=notion_data),
                "title_ov": n.get_property(index, "OrigTitle", 'text', source=notion_data),
                "year": n.get_property(index, "Year", 'select', source=notion_data),
                "director": n.get_property(index, "Director", 'text', source=notion_data),
                "screenwriter": n.get_property(index, 'Screenwriter', source=notion_data),
                "synopsis": n.get_property(index, "Synopsis", 'text', source=notion_data),
                "bio": n.get_property(index, "Bio", 'text', source=notion_data),
                "country": u.list_to_comma_separated(n.get_property(index, "Country", 'multi_select', source=notion_data)),
                "runtime": n.get_property(index, "Runtime", 'text', source=notion_data),  # OBS
                "technique": u.list_to_comma_separated(n.get_property(index, "Technique", 'multi_select', source=notion_data)),
                "production": n.get_property(index, "Production", 'text', source=notion_data),
                "animation": n.get_property(index, "Animation", 'text', source=notion_data),
                "category": n.get_property(index, "Tags", 'select', source=notion_data),
                "still_img": n.get_property(index, "Pic", 'url', source=notion_data),
                "trailer_url": n.get_property(index, 'Trailer URL', 'url', source=notion_data),
                'programme': n.get_property(index, 'Programme', 'multi_select', source=notion_data),
                "unballoted": n.get_property(index, 'unballoted', 'checkbox', source=notion_data),
                "visibility": n.get_property(index, "visibility", 'select', source=notion_data),
            }

            # compose description for eventive entry
            description = f"{film_data['synopsis']}<br><br>{film_data['bio']}"

            # get notion page id
            notion_id = n.get_property(index, property_type='id', source=notion_data)

            # write to eventive and retrieve film id
            print(f"Trying to write film {film_data['title']} to eventive...")
            data = {
                "event_bucket": e.event_bucket_id,
                "name": film_data['title'],
                "details": {
                    "year": film_data['year'],
                    "runtime": film_data['runtime'],
                    "language": "",
                    "country": film_data['country'],
                    "premiere": "",
                    "rating": "",
                    "note": ""
                },
                "credits": {
                    "director": film_data['director'],
                    "screenwriter": film_data['screenwriter'],
                    "producer": film_data['production'],
                    "executive_producer": "",
                    "co_producer": "",
                    "filmmaker": "",
                    "cast": "",
                    "cinematographer": "",
                    "editor": "",
                    "animator": film_data['animation'],
                    "production_design": "",
                    "composer": "",
                    "sound_design": "",
                    "music": ""
                },
                "trailer_url": film_data['trailer_url'],
                "description": description,
                "cover_image_external": "",
                "still_image_external": film_data['still_img'],
                "short_description": '',
                "visibility": film_data['visibility'],
                "unballoted": film_data['unballoted']
            }

            # add tags
            # ... OBS doesn't this have to be passed through 'tag to tags id' or similar function?
            e.add_tags_to_request_dict(request_dict=data, tags_list=film_data['programme'])

            # this function both executes the request and gets back/returns the eventive id.
            eventive_id = e.write_film(data)

            # write eventive film id and link back to notion
            n.write_property_to_page(page_id=notion_id, property_name='eventive_id', content=eventive_id, property_type='text')

            eventive_link = f"https://admin.eventive.org/event_buckets/{e.event_bucket_id}/films/{eventive_id}/edit"
            n.write_property_to_page(notion_id, property_name='eventive_link', content=eventive_link, property_type='url')

    else:
        print('Invalid input!')
