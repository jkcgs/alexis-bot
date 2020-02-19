import sqlite3

from bot import Manager


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


def run():
    with sqlite3.connect("db.sqlite3") as db:
        db.row_factory = dict_factory

        for model in Manager.get_all_models():
            model_name = model.__name__.lower()
            if model_name in ['meme', 'post']:
                continue

            print('processing model', model_name)

            cur = db.cursor()
            try:
                cur.execute(f'SELECT * FROM {model_name}')
            except sqlite3.OperationalError as e:
                print('error fetching content (does table exist?)', e)
                continue

            rows = cur.fetchall()

            if model_name == 'usernamereg':
                rows = process_names(rows)

            rows_n = len(rows)
            batch = []
            invalid_c = 0
            inserted = 0

            print(model_name, 'count:', rows_n)
            for i, row in enumerate(rows):
                if model_name != 'post':
                    del row['id']

                skip = False
                if model_name == 'ban':
                    if not row['userid']:
                        skip = True
                elif model_name == 'starboard':
                    if not row['starboard_id']:
                        skip = True
                elif model_name == 'usernote':
                    if not row['note']:
                        skip = True

                if not skip:
                    batch.append(row)
                else:
                    invalid_c += 1

                if len(batch) >= 10000 or (i == (rows_n - 1) and len(batch) > 0):
                    inserted += len(batch)
                    print('batch in', inserted, (rows_n - invalid_c))
                    model.insert_many(batch).execute()
                    batch = []
            print('invalid rows:', invalid_c)


def process_names(rows):
    name_count = {}
    for row in rows:
        if row['userid'] not in name_count:
            name_count[row['userid']] = 1
        else:
            name_count[row['userid']] += 1

    rows = [row for row in rows if name_count[row['userid']] > 1]

    names_list = {}
    rows2 = []
    for row in rows:
        if row['userid'] not in names_list:
            names_list[row['userid']] = []

        if len(names_list[row['userid']]) == 0 or names_list[row['userid']][-1] != row['name']:
            rows2.append(row)
            names_list[row['userid']].append(row['name'])

    rows = rows2
    print('username rows total (filtered):', len(rows))
    return rows


if __name__ == '__main__':
    run()
