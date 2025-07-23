import os

from getpass import getpass

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization

file_path = 'private_key.pem'

if os.path.exists(file_path):
    print(f'Error: {file_path} already exists.')
    exit()

encoding = serialization.Encoding.PEM
format = serialization.PrivateFormat.PKCS8
password = getpass('Enter a password for the key (or leave blank):').encode()
if password:
    confirmation = getpass('Please re-enter the password.').encode()
    if password != confirmation:
        print('Error: passwords do not match.')
        exit()
    encryption_algorithm = serialization.BestAvailableEncryption(password)
else:
    encryption_algorithm = serialization.NoEncryption()

private_key = Ed25519PrivateKey.generate()
data = private_key.private_bytes(encoding, format, encryption_algorithm)
with open(file_path, 'wb') as file:
    file.write(data)
print(f'Key saved to {file_path}.')
