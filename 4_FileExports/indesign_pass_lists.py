import csv
import os

# also have one list (notion database) to mark printed/handed out passes? mm... match by id?
# script to (optionally!) update 'pass db'?
# include sorting method in output filenames?

def main():
    # setup
    folder_location = "../exports/pass_export"
    try:
        os.makedirs(folder_location)
    except FileExistsError:
        pass

    csv_dicts = list()

    with open('../files/passes.csv', encoding="UTF-8-sig") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            csv_dicts.append(row)

    # address missing names
    for csv_dict in csv_dicts:
        if csv_dict['name'] == "Unnamed Pass":
            csv_dict['name'] = csv_dict['person.name'].title()
        if not csv_dict['name']:
            csv_dict['name'] = csv_dict['person.email']
    # sorting prompt
    sorting_prompt = input("Sort by last (n)ame or by (d)ate? ").lower()
    if sorting_prompt == "n":
        csv_dicts = sorted(csv_dicts, key=lambda x: x["name"].split()[-1])
    elif sorting_prompt == "d":
        for csv_dict in csv_dicts:
            d = csv_dict['created_at'].replace("-", "")
            csv_dict['sort_date'] = int(f"{d[:8]}")
        csv_dicts = sorted(csv_dicts, key=lambda x: x["sort_date"])

    else:
        print("No sorting method was chosen. Generating files without sorting...")
    pass_buckets = set(d['pass_bucket.name'] for d in csv_dicts)
    used_names = list()

    for pass_bucket_name in pass_buckets:
        with open(f'{folder_location}/{pass_bucket_name}.txt', 'w', newline='', encoding="UTF-16") as f:
            first_line = "#id\tname\tcompany\tcreated_at"
            f.write(first_line)
            for csv_dict in csv_dicts:
                if csv_dict['pass_bucket.name'] != pass_bucket_name:
                    pass
                else:
                    id = csv_dict["id"]
                    created_at = csv_dict["created_at"]
                    name = csv_dict['name'].title()
                    if not name:  # skip unfinished passes
                        pass
                    elif name in used_names:  # skip second/multiple passes w/ same name # OBS
                        pass
                    else:
                        used_names.append(name)
                        # address long names (could be improved with regex. leaving out email adresses)
                        if "@" in name:
                            pass
                        else:
                            if len(name) > 20:
                                name_split = name.split()
                                if len(name_split) == 3:
                                    name = f"{name_split[0]} {name_split[1][0]}. {name_split[2]}"
                                elif len(name_split) == 2:
                                    name = f"{name_split[0][0]}. {name_split[1]}"
                            # second pass
                            if len(name) > 20:
                                name = f"{name_split[0][0]}. {name_split[-1]}"
                            print(f"Abbreviated long name to {name}.")
                        pass_bucket = csv_dict['pass_bucket.name'].replace("-", "–")
                        company = csv_dict['Company / School']
                        # (address long company names?)
                        f.write(f"\n{id}\t{name}\t{company}\t{created_at}")
        print(f"wrote {pass_bucket_name}.txt")


main()