from textual.app import App
from textual.widgets import Footer, Header

class CryptcordApp(App[None]):
    def __init__(self):
        super().__init__()

    def compose(self):
        yield Header()
        yield Footer()

if __name__ == '__main__':
    app = CryptcordApp()
    app.run()
