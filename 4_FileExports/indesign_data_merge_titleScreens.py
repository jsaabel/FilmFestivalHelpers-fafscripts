# creates tab separated txt files to be used as data sources in InDesign data merge.
from modules import notion as n, utils as u
import os

# setup
folder_location = 'C:/Users/jonas/PycharmProjects/faf2021/exports/title_screens'
try: os.makedirs(folder_location)
except FileExistsError:
    pass

# choose programmes to export
programme_list = n.programme_tags
# programme_list = []

for programme in programme_list:
    # retrieve film db
    data_dict = dict()
    n.add_sorts_to_request_dict(data_dict, 'Seq', 'ascending')
    n.add_filter_to_request_dict(data_dict, 'Programme', 'multi_select', 'contains', programme)
    notion_films = n.get_db('films', data_dict=data_dict)

    with open(f'{folder_location}/{u.safe_folder_name(programme)}.txt', 'w', encoding="utf-16") as f:
        f.write(f'film_name\ttitle_ov\tyear\tdirector\tplaytime')  # tab separated txt file, image denoted by @ character
        for index in range(0, n.get_item_count(notion_films)):
            film_name = n.get_property(index, 'English Title', 'title', source=notion_films)
            title_ov = n.get_property(index, 'Original Title', 'text', source=notion_films)
            year = n.get_property(index, 'Year', 'select', source=notion_films)
            director = n.get_property(index, 'Director', 'text', source=notion_films)
            playtime = n.get_property(index, 'Runtime', 'text', source=notion_films)
            playtime_split = playtime.split(":")
            playtime = f"{playtime_split[0]}m {playtime_split[1]}s"

            f.write(f'\n{film_name}\t{title_ov}\t{year}\t{director}\t{playtime}')

        print(f'files written for {programme}.')




