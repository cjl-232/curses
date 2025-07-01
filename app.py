import curses
import time

import httpx

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from sqlalchemy import create_engine

from body import Body
from database.operations import store_fetched_data
from server.operations import fetch_data
from settings import settings

class App:
    def __init__(self):
        self.engine = create_engine(settings.local_database.url)
        self.signature_key = Ed25519PrivateKey.from_private_bytes(bytes(32))
    def _fetch_handler(self):
        client = httpx.Client(timeout=settings.server.request_timeout)
        while True:
            response = fetch_data(self.engine, self.signature_key, client)
            if response is not None:
                response.data.
            time.sleep(settings.server.fetch_interval)


    def run(self):
        curses.wrapper(lambda stdscr: Body(stdscr).run())


# import curses
# from secrets import token_urlsafe
# from sqlalchemy import create_engine
# from sqlalchemy.orm import Session
# from settings import settings
# from database.models import Base, Contact
# from database.operations import get_contacts
# from components.contacts import ContactsMenu

# engine = create_engine(settings.local_database.url)
# Base.metadata.drop_all(engine)
# Base.metadata.create_all(engine)
# with Session(engine) as session:
#     for _ in range(40):
#         session.add(Contact(name=get_full_name(), verification_key=token_urlsafe(32)+'='))
#     session.commit()
# menu = ContactsMenu(engine, get_contacts(engine))
# curses.wrapper(menu.run)

# # URI Connections

# # Modern versions of SQLite support an alternative system of connecting using a driver level URI, which has the advantage that additional driver-level arguments can be passed including options such as “read only”. The Python sqlite3 driver supports this mode under modern Python 3 versions. The SQLAlchemy pysqlite driver supports this mode of use by specifying “uri=true” in the URL query string. The SQLite-level “URI” is kept as the “database” portion of the SQLAlchemy url (that is, following a slash):

# # e = create_engine("sqlite:///file:path/to/database?mode=ro&uri=true")

# # Note

# # The “uri=true” parameter must appear in the query string of the URL. It will not currently work as expected if it is only present in the create_engine.connect_args parameter dictionary.

# # The logic reconciles the simultaneous presence of SQLAlchemy’s query string and SQLite’s query string by separating out the parameters that belong to the Python sqlite3 driver vs. those that belong to the SQLite URI. This is achieved through the use of a fixed list of parameters known to be accepted by the Python side of the driver. For example, to include a URL that indicates the Python sqlite3 “timeout” and “check_same_thread” parameters, along with the SQLite “mode” and “nolock” parameters, they can all be passed together on the query string: