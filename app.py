import curses
from names import get_full_name
from secrets import token_urlsafe
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from settings import settings
from database.models import Base, Contact
from components.contacts import ContactsMenu

engine = create_engine(settings.local_database.url)
Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)
with Session(engine) as session:
    for _ in range(40):
        session.add(Contact(name=get_full_name(), verification_key=token_urlsafe(32)+'='))
    session.commit()
menu = ContactsMenu(engine)
curses.wrapper(menu.run)