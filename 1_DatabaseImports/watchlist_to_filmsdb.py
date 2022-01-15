# 22.11.21: This should be made superfluous by combining watchlist and film database
# 22.07.21
from modules import notion as n, utils as u

# read from watchlist
# get only films that are assigned a programme
filter_dict = {
        "filter": {
                'property': 'Programme',
                'multi_select': {'is_not_empty': True},
        }
}
notion_data = n.get_db('watchlist', filter_dict=filter_dict)
item_count_notion = n.get_item_count(notion_data)


for index in range(0, item_count_notion):
    # dict structure: TargetPropertyName/KEY: [PropertyValue/VALUE[0], TargetPropertyType/VALUE[1]
    film_data = {
        "English Title": [n.get_property(index, "English Title", 'title', source=notion_data), 'title'],
        "Runtime_min": [n.get_property(index, "Duration (m)", 'number', source=notion_data), 'number'],
        "Programme": [n.get_property(index, "Programme", 'multi_select', source=notion_data), 'multi_select'],
        "Year": [n.get_property(index, "Year", 'select', source=notion_data), 'select'],
        "Director": [n.get_property(index, "Director", 'text', source=notion_data).title(), 'text'],
        "Synopsis": [n.get_property(index, "Synopsis", 'text', source=notion_data), 'text'],
        "Country": [n.get_property(index, "Country", 'multi_select', source=notion_data), 'multi_select'],
        "Technique": [n.get_property(index, "Technique", 'multi_select', source=notion_data), 'multi_select'],
        "Gender": [n.get_property(index, "Gender", 'select', source=notion_data), 'select'],
    }

    for key in film_data.keys():
        if not film_data[key][0]:  # avoid 400 response error in case of missing synopsis.
            film_data[key][0] = "(NA)"

    # mapping input to output. OBS: property names and types
    data_raw = dict()
    n.add_parent_id_to_request_dict(data_raw, parent_id=n.db_ids['test'])  # target notion db

    for key, value in film_data.items():
        n.add_property_to_request_dict(data_raw, content=value[0], property_type=value[1], property_name=key)

    print(f"Trying to write {film_data['English Title'][0]} to database...")
    n.write_to_db(data_raw, db_id=n.db_ids['test'])
