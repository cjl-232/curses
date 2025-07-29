# Cursecord

A Python-based TUI client that allows users to securely send and receive
receive messages across the public internet when used with a server running
the [Cryptcord API](https://github.com/cjl232-redux/cryptcord-server).

## Requirements

* Python 3.13 and up.

## Installation and Setup

1. Clone this repository to your system.
2. Create a virtual environment using ```python -m venv venv```.
3. Activate the virtual environment. In Bash terminals, this can be achieved
   with ```source venv/bin/activate```.
4. Install all dependencies using ```pip install -r requirements.txt```.
5. **Windows users only** must use ```pip install windows-curses```, as the
   curses library will not be installed by default.
6. Ensure that you have a securely generated 32-byte private key ready to
   provide on launch. If so, skip to step 8. This can be in one of four forms:
    - A hexadecimal value with 64 characters
    - A padded url-safe Base64-encoded value with 44 characters
    - A file containing a PEM-encoded serialization of an Ed25519 private key
    - A file containing a DER-encoded serialization of an Ed25519 private key
7. If none of these are available, a new private key can be generated using
   ```python keygen.py```. This will create a file containing a PEM-encoded
   serialization of an Ed25519 private key, and optionally allows for the file
   to be password-protected.
8. Launch the app from the command line by running ```python app.py ...```,
   specifying the public key through a command line argument. Use 
   ```python app.py --help``` to see the required syntax.
9. On successfully launching the app for the first time, settings.yaml will be
   generated in the working directory. Open this in a text editor, and adjust
   the server url settings to the desired values for an active API instance.
   Finally, close and re-open the app.

## Usage

* 