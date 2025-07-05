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

from components.windows import (
    Layout,
    LayoutMeasure,
    LayoutUnit,
    Padding,
    WindowManager,
)
from components.menus import PaginatedMenu



if __name__ == '__main__':
    def main(stdscr: curses.window):
        manager = WindowManager(stdscr)
        manager.windows.append(
            PaginatedMenu(
                items=['a', 'b', 'c', 'd', 'e'] * 30,
                layout=Layout(
                    height=LayoutMeasure([
                        (100, LayoutUnit.PERCENTAGE),
                        (-10, LayoutUnit.CHARS),
                    ]),
                    width=LayoutMeasure([
                        (50, LayoutUnit.PERCENTAGE),
                    ]),
                    top=LayoutMeasure([
                        (10, LayoutUnit.CHARS),
                    ]),
                    left=LayoutMeasure([
                        (20, LayoutUnit.CHARS),
                    ]),
                ),
                padding=Padding(1, 2, 3),
                title='Test Menu',
            )
        )
        manager.run()
    curses.wrapper(main)