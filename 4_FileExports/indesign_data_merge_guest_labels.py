from modules import notion as n

# CONNECT TO (FILTERED AND SORTED!?) GUEST DB
data_dict = dict()
n.add_filter_to_request_dict(request_dict=data_dict, property_name='Events', filter_content=True,
                             filter_condition="is_not_empty", property_type="relation")
notion_guests = n.get_db('guests', data_dict=data_dict)
item_count_notion = n.get_item_count(notion_guests)

with open('../exports/guest_names.txt', 'w', newline='', encoding="UTF-16") as f:
    f.write(f'Name')
    for index in range(item_count_notion):
        name = n.get_property(index, 'Name', 'title', source=notion_guests)
        if len(name) > 20:
            name_split = name.split()
            name = f"{name_split[0]} {name_split[-1]}"
            print(f"Abbreviated long name to {name}.")

        f.write(f'\n{name}')
print('File written.')