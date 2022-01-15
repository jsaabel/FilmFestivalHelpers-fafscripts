# creates tab separated txt files to be used as data sources in InDesign data merge.
from modules import notion as n, utils as u
import os

# setup
img_folder_location = 'C:/Users/jonas/PycharmProjects/faf2021/exports/id_pics'
try: os.makedirs(img_folder_location)
except FileExistsError:
    pass

# choose programmes to export
# (this should be implemented as a prompt)
programme_list = n.programme_tags
# programme_list = []

for programme in programme_list:
    # retrieve film db
    data_dict = dict()
    n.add_sorts_to_request_dict(data_dict, 'Seq', 'ascending')
    n.add_filter_to_request_dict(data_dict, 'Programme', 'multi_select', 'contains', programme)
    notion_films = n.get_db('films', data_dict=data_dict)

    with open(f'{img_folder_location}/{programme}.txt', 'w') as f:
        # (could implement more common properties (year etc), and include sort!
        f.write(f'film_name\tdirector\t@img')  # tab separated txt file, image denoted by @ character
        for index in range(0, n.get_item_count(notion_films)):
            film_name = n.get_property(index, 'English Title', 'title', source=notion_films)
            director = n.get_property(index, 'Director', 'text', source=notion_films)
            img_url = n.get_property(index, 'Pic', 'url', source=notion_films)
            file_name = u.safe_file_name(film_name)
            img_path = u.save_img(img_url, file_name, location=img_folder_location)
            f.write(f'\n{film_name}\t{director}\t{img_path}')
        print(f'files written for {programme}.')




