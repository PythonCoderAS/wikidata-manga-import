from typing import Iterable

from pony.orm import Database, PrimaryKey, Required, db_session, select

db = Database()


class Item(db.Entity):
    item_id = PrimaryKey(int)
    completed = Required(bool, sql_default=False)


def init_db():
    db.bind(provider="sqlite", filename="database.sqlite", create_db=True)
    db.generate_mapping(create_tables=True)


@db_session
def get_ids():
    return list(select(item.item_id for item in Item if not item.completed))


@db_session
def add_ids(ids: Iterable[str]):
    for id in ids:
        Item(item_id=int(id.lstrip("Q")), completed=False)


@db_session
def mark_completed(item_id: str):
    item = Item[int(item_id.lstrip("Q"))]
    item.completed = True


@db_session
def reset_db():
    db.drop_table("Item", with_all_data=True)
