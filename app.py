#TODO replace settings with cached... ideally also property?

import curses
import time

import httpx

from sqlalchemy import create_engine

from body import Body
from database.operations import store_fetched_data
from parser import ClientArgumentParser
from server.operations import fetch_data
from settings import settings  # This is causing slowdown. Adjust it.

parser = ClientArgumentParser()

class App:
    def __init__(self):
        self.engine = create_engine(settings.local_database.url)
        self.signature_key = parser.signature_key

    def _fetch_handler(self):
        client = httpx.Client(timeout=settings.server.request_timeout)
        while True:
            response = fetch_data(self.engine, self.signature_key, client)
            if response is not None:
                store_fetched_data(self.engine, response)
            time.sleep(settings.server.fetch_interval)

    def run(self):
        curses.wrapper(lambda stdscr: Body(stdscr).run())


if __name__ == '__main__':
    App().run()