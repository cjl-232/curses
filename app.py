#TODO replace settings with cached... ideally also property?
#TODO figure this out... derive from prompts, get a result property that takes
# into account NUMERIC choices as well. Text prompt vs choice prompt.
# Implement as a enum in the PromptNode field?

import curses
import time

from base64 import urlsafe_b64encode
from datetime import datetime
from threading import Thread

import httpx

from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import Session

from components.contacts import ContactsMenu, ContactsPrompt
from components.logs import Log
from components.messages import MessageEntry, MessageLog
from database.models import Base, FernetKey, ReceivedExchangeKey
from database.operations import (
    add_contact,
    get_fernet_key,
    get_unmatched_keys,
    store_fetched_data,
    store_posted_exchange_key,
    store_posted_message,
)
from database.schemas.inputs import ContactInputSchema
from parser import ClientArgumentParser
from server.operations import fetch_data, post_exchange_key, post_message
from settings import settings  # This is causing slowdown. Adjust it.
from states import State

parser = ClientArgumentParser()

class App:
    def __init__(
            self,
            stdscr: curses.window,
            engine: Engine,
            contacts_menu: ContactsMenu,
            message_log: MessageLog,
            message_entry: MessageEntry,
            output_log: Log,
        ) -> None:
        self.stdscr = stdscr
        self.engine = engine
        self.signature_key = parser.signature_key
        self.contacts_menu = contacts_menu
        self.message_log = message_log
        self.message_entry = message_entry
        self.output_log = output_log
        self.windows = [contacts_menu, message_log, message_entry, output_log]
        self.focus_index = 0

    def _fetch_handler(self):
        client = httpx.Client(timeout=settings.server.request_timeout)
        while True:
            response = fetch_data(self.engine, client, self.signature_key)
            if response is not None:
                store_fetched_data(self.engine, response)
            time.sleep(settings.server.fetch_interval)

    def _key_response_handler(self):
        client = httpx.Client(timeout=settings.server.request_timeout)
        while True:
            keys = get_unmatched_keys(self.engine)
            for key in keys:
                private_key = X25519PrivateKey.generate()
                response = post_exchange_key(
                    client,
                    self.signature_key,
                    key.contact.verification_key,
                    private_key.public_key(),
                    key.public_key,
                )
                
                shared_secret = private_key.exchange(key.public_key)
                fernet_obj = FernetKey(
                    contact_id=key.contact.id,
                    encoded_bytes=urlsafe_b64encode(shared_secret).decode(),
                    timestamp=response.data.timestamp,
                )
                
                private_key.exchange(key.public_key)
                with Session(self.engine) as session:
                    key_obj = session.get_one(ReceivedExchangeKey, key.id)
                    key_obj.matched = True
                    session.add(fernet_obj)
                    session.commit()                    

            time.sleep(settings.server.key_response_interval)

    def _refresh_handler(self):
        while True:
            self.message_log.update()
            time.sleep(1.0)

    def _handle_key_standard(self, key: int) -> State:
        match key:
            case 9:   # Tab
                return State.NEXT_WINDOW
            case curses.KEY_BTAB:
                return State.PREV_WINDOW
            case curses.KEY_RESIZE:
                return State.RESIZE
            case 27:  # Esc
                return State.TERMINATE
            case _:
                return self.windows[self.focus_index].handle_key(key)

    def run(self):
        self.stdscr.keypad(True)
        self.stdscr.nodelay(True)
        self.stdscr.clear()
        self.stdscr.refresh()
        for window in self.windows:
            window.place(self.stdscr)
        Thread(target=self._fetch_handler, daemon=True).start()
        Thread(target=self._refresh_handler, daemon=True).start()
        Thread(target=self._key_response_handler, daemon=True).start()
        main_client = httpx.Client(timeout=settings.server.request_timeout)
        state = State.STANDARD
        while self.windows and state != State.TERMINATE:
            match state:
                case State.STANDARD:
                    for index, window in enumerate(self.windows):
                        if window.draw_required:
                            window.draw(index == self.focus_index)
                    state = self._handle_key_standard(self.stdscr.getch())
                case State.NEXT_WINDOW:
                    for _ in range(len(self.windows)):
                        self.focus_index += 1
                        if self.focus_index >= len(self.windows):
                            self.focus_index = 0
                        if self.windows[self.focus_index].focusable:
                            break
                    state = State.STANDARD
                case State.PREV_WINDOW:
                    for _ in range(len(self.windows)):
                        self.focus_index -= 1
                        if self.focus_index < 0:
                            self.focus_index = len(self.windows) - 1
                        if self.windows[self.focus_index].focusable:
                            break
                    state = State.STANDARD
                case State.RESIZE:
                    self.stdscr.erase()
                    self.stdscr.refresh()
                    for window in self.windows:
                        window.place(self.stdscr)
                    state = State.STANDARD
                case State.ADD_CONTACT:
                    self.stdscr.erase()
                    self.stdscr.refresh()
                    state = State.PROMPT_ACTIVE
                    prompt = ContactsPrompt()
                    prompt.place(self.stdscr)
                    while state == State.PROMPT_ACTIVE:
                        if prompt.draw_required:
                            prompt.draw()
                            prompt.draw_required = False
                        key = self.stdscr.getch()
                        if key == curses.KEY_RESIZE:
                            prompt.place(self.stdscr)
                        else:
                            state = prompt.handle_key(key)
                    match state:
                        case State.PROMPT_SUBMITTED:
                            try:
                                name, public_key = prompt.retrieve_contact()
                                contact = ContactInputSchema.model_validate({
                                    'name': name,
                                    'verification_key': public_key,
                                })
                                add_contact(self.engine, contact)
                                self.output_log.add_item(
                                    text=f"Added new contact '{name}'.",
                                    cached=False,
                                    title='Successful Operation',
                                    timestamp=datetime.now(),
                                )
                            except Exception as e:
                                self.output_log.add_item(
                                    text=str(e),
                                    cached=False,
                                    title='Add Contact Error',
                                    timestamp=datetime.now(),
                                )
                            self.contacts_menu.refresh()


                        case _:
                            pass
                    self.stdscr.erase()
                    self.stdscr.refresh()
                    for window in self.windows:
                        window.draw_required = True
                    state = State.STANDARD
                case State.SELECT_CONTACT:
                    selected_contact = self.contacts_menu.current_contact
                    self.message_log.set_contact(selected_contact)
                    self.message_entry.set_contact(selected_contact)
                    state = State.STANDARD
                case State.SEND_EXCHANGE_KEY:
                    try:
                        private_exchange_key = X25519PrivateKey.generate()
                        contact = self.contacts_menu.current_contact
                        post_exchange_key(
                            main_client,
                            self.signature_key,
                            contact.verification_key,
                            private_exchange_key.public_key(),
                        )
                        store_posted_exchange_key(
                            self.engine,
                            contact.id,
                            private_exchange_key,
                        )
                        self.output_log.add_item(
                            text=f"Posted exchange key to {contact.name}.",
                            cached=False,
                            title='Successful Operation',
                            timestamp=datetime.now(),
                        )
                    except Exception as e:
                        self.output_log.add_item(
                            text=str(e),
                            cached=False,
                            title='Post Exchange Key Error',
                            timestamp=datetime.now(),
                        )
                    state = State.STANDARD
                case State.SEND_MESSAGE:
                    if self.message_entry.input:
                        contact = self.contacts_menu.current_contact
                        try:
                            key = get_fernet_key(self.engine, contact)
                            encrypted_text = key.encrypt(
                                self.message_entry.input.encode(),
                            )
                            response = post_message(
                                main_client,
                                self.signature_key,
                                contact.verification_key,
                                encrypted_text,
                            )
                            store_posted_message(
                                self.engine,
                                self.message_entry.input,
                                contact.id,
                                response,
                            )
                            self.output_log.add_item(
                                text=f"Posted message to {contact.name}.",
                                cached=False,
                                title='Successful Operation',
                                timestamp=datetime.now(),
                            )
                            self.message_entry.input = ''
                            self.message_entry.draw_required = True
                            self.message_entry.cursor_index = 0
                        except Exception as e:
                            self.output_log.add_item(
                                text=str(e),
                                cached=False,
                                title='Post Message Error',
                                timestamp=datetime.now(),
                            )
                    state = State.STANDARD
                case _:
                    state = State.STANDARD
        self.stdscr.clear()

            

from styling import (
    Layout,
    LayoutMeasure,
    LayoutUnit,
    Padding,
)
from components.contacts import ContactsMenu



if __name__ == '__main__':
    def main(stdscr: curses.window):
        engine = create_engine(settings.local_database.url)
        Base.metadata.create_all(engine)
        app = App(
            stdscr,
            engine,
            ContactsMenu(
                engine=engine,
                layout=Layout(
                    height=LayoutMeasure(
                        (80, LayoutUnit.PERCENTAGE),
                    ),
                    width=LayoutMeasure(
                        (20, LayoutUnit.PERCENTAGE),
                    ),
                    top=LayoutMeasure(),
                    left=LayoutMeasure(),
                ),
                padding=Padding(1),
            ),
            MessageLog(
                engine=engine,
                contact=None,
                layout=Layout(
                    height=LayoutMeasure(
                        (80, LayoutUnit.PERCENTAGE),
                        (-4, LayoutUnit.CHARS),
                    ),
                    width=LayoutMeasure(
                        (80, LayoutUnit.PERCENTAGE),
                    ),
                    top=LayoutMeasure(),
                    left=LayoutMeasure(
                        (20, LayoutUnit.PERCENTAGE),
                    ),
                ),
                padding=Padding(1),
            ),
            MessageEntry(
                engine=engine,
                contact=None,
                layout=Layout(
                    height=LayoutMeasure(
                        (4, LayoutUnit.CHARS),
                    ),
                    width=LayoutMeasure(
                        (80, LayoutUnit.PERCENTAGE),
                    ),
                    top=LayoutMeasure(
                        (80, LayoutUnit.PERCENTAGE),
                        (-4, LayoutUnit.CHARS),
                    ),
                    left=LayoutMeasure(
                        (20, LayoutUnit.PERCENTAGE),
                    ),
                ),
                padding=Padding(0, 1),
            ),
            Log(
                layout=Layout(
                    height=LayoutMeasure(
                        (20, LayoutUnit.CHARS),
                    ),
                    width=LayoutMeasure(
                        (100, LayoutUnit.PERCENTAGE),
                    ),
                    top=LayoutMeasure(
                        (80, LayoutUnit.PERCENTAGE),
                    ),
                    left=LayoutMeasure(),
                ),
                padding=Padding(0, 1),
            ),
        )
        app.run()
    curses.wrapper(main)

# TODO go back to having a windowmanager class that the app is derived from
# Use the app class constructor to make the windows based on settings