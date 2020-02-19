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
            if model_name == 'meme':
                continue

            cur = db.cursor()
            cur.execute(f'SELECT * FROM {model_name}')

            rows = cur.fetchall()
            rows_n = len(rows)
            print(model, model_name, 'count:', rows_n)

            batch = []
            invalid_c = 0

            for i, row in enumerate(rows):
                skip = False
                if model_name not in ['post']:
                    del row['id']

                if model_name == 'ban':
                    if not row['userid']:
                        # print('invalid row', row)
                        skip = True
                elif model_name == 'starboard':
                    if not row['starboard_id']:
                        # print('invalid row', row)
                        skip = True
                elif model_name == 'usernote':
                    if not row['note']:
                        # print('invalid row', row)
                        skip = True

                if not skip:
                    batch.append(model.create(**row))
                else:
                    invalid_c += 1

                if len(batch) >= 10000 or (i == (rows_n - 1) and len(batch) > 0):
                    print('batch in', i+1, rows_n)
                    model.insert_many(batch)
                    batch = []
            print('invalid rows:', invalid_c)


if __name__ == '__main__':
    run()
