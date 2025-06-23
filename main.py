import curses

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from database.models import Contact
from settings import settings

engine = create_engine(settings.local_database.url)

def draw_menu(stdscr, selected_idx, top_idx, height):
    stdscr.clear()
    with Session(engine) as session:
        options = [x for x in session.scalars(select(Contact.name))]
    visible_options = options[top_idx:top_idx + height]
    with Session(engine) as session:

        for i, option in enumerate(visible_options):
            y = i + 2
            x = 2
            if top_idx + i == selected_idx:
                stdscr.attron(curses.A_REVERSE)
                stdscr.addstr(y, x, option)
                stdscr.attroff(curses.A_REVERSE)
            else:
                stdscr.addstr(y, x, option)

        stdscr.refresh()

def main(stdscr):
    curses.curs_set(0)
    stdscr.keypad(True)
    selected_idx = 0
    top_idx = 0

    # Use terminal size to determine visible list height
    screen_height, screen_width = stdscr.getmaxyx()
    list_height = screen_height - 4  # padding for top/bottom

    with Session(engine) as session:
        options = [x for x in session.scalars(select(Contact.name))]
    while True:
        draw_menu(stdscr, selected_idx, top_idx, list_height)
        key = stdscr.getch()

        if key == curses.KEY_UP:
            if selected_idx > 0:
                selected_idx -= 1
                if selected_idx < top_idx:
                    top_idx -= 1
            print(selected_idx)
        elif key == curses.KEY_DOWN:
            if selected_idx < len(options) - 1:
                selected_idx += 1
                if selected_idx >= top_idx + list_height:
                    top_idx += 1
        elif key in [curses.KEY_ENTER, ord('\n')]:
            break

    stdscr.clear()
    stdscr.addstr(0, 0, f"You selected: {options[selected_idx]}")
    stdscr.refresh()
    stdscr.getch()

if __name__ == "__main__":
    curses.wrapper(main)

if __name__ == "__main__":
    curses.wrapper(main)