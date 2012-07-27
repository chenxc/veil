from __future__ import unicode_literals, print_function, division
from sandal.collection import *
from sandal.binding import *
from sandal.command import *
from veil.database import *

demo_db = register_database('demo')

@command
@transactional(demo_db)
def create_item(name=not_empty):
    item_id = demo_db().insert('items', returns_id=True, name=name)
    return Item(item_id, name)


def list_items():
    rows = demo_db().list('SELECT * FROM items')
    return [Item(**row._asdict()) for row in rows]


class Item(Entity):
    def __init__(self, id, name):
        super(Item, self).__init__(id=id, name=name)