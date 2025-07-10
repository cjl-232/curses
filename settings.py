import curses
import os

from functools import cached_property
from typing import Annotated

from pydantic import BaseModel, BeforeValidator, Field
from yaml import safe_dump, safe_load

class _DatabaseSettingsModel(BaseModel):
    url: str = Field(
        default='sqlite:///database.db',
        title='Local Database URL',
        description=(
            'A SQLAlchemy-compatible URL pointing to a secure database. This '
            'will be used to store shared secrets and message plaintext, and '
            'therefore MUST be fully secure. Ideally, it should be either an '
            'SQLite file or a locally hosted PostgreSQL database.'
        ),
    )

class _DisplaySettingsModel(BaseModel):
    max_page_height: int = Field(
        ge=1,
        default=16,
        title='Maximum Page Height',
        description=(
            'The maximum number of lines in the terminal the UI should use for'
            'each page. Applies only to components that use pagination.'
        ),
    )
    await_inputs: bool = Field(
        default=True,
        title='Await Inputs',
        description=(
            'Whether UI components should pause refreshing while awaiting '
            'inputs. Disabling this will make inputs behave more smoothly, '
            'especially when holding down keys, but may reduce performance.'
        ),
    )
    top_padding: int = Field(
        ge=0,
        default=1,
        title='Top Padding',
        description=(
            'The horizontal padding between the content and top border of '
            'each window.'
        ),
    )
    bottom_padding: int = Field(
        ge=0,
        default=1,
        title='Bottom Padding',
        description=(
            'The horizontal padding between the content and the bottom border '
            'of each window.'
        ),
    )
    left_padding: int = Field(
        ge=0,
        default=1,
        title='Left Padding',
        description=(
            'The horizontal padding between the content and left border of '
            'each window.'
        ),
    )
    right_padding: int = Field(
        ge=0,
        default=1,
        title='Right Padding',
        description=(
            'The horizontal padding between the content and right border of '
            'each window.'
        ),
    )

def _validate_key(key: int | str) -> str:
    if isinstance(key, int):
        key = str(key)
    return key.lower()

def _validate_keys(keys: list[int | str] | set[int | str]) -> list[str]:
    return [_validate_key(key) for key in keys]

type _KeyBindingList = Annotated[
    list[str],
    BeforeValidator(_validate_keys),
]

class _KeyBindingsModel(BaseModel):
    up_keys: _KeyBindingList = ['w']
    down_keys: _KeyBindingList = ['s']
    left_keys: _KeyBindingList = ['a']
    right_keys: _KeyBindingList = ['d']
    
    @cached_property
    def up_key_set(self):
        return set([curses.KEY_UP] + [ord(x) for x in self.up_keys])
    @cached_property
    def down_key_set(self):
        return set([curses.KEY_DOWN] + [ord(x) for x in self.down_keys])
    @cached_property
    def left_key_set(self):
        return set([curses.KEY_LEFT] + [ord(x) for x in self.left_keys])
    @cached_property
    def right_key_set(self):
        return set([curses.KEY_RIGHT] + [ord(x) for x in self.right_keys])
    
class _UrlSettingsModel(BaseModel):
    scheme: str = 'https'
    subdomain: str | None = Field(default=None)
    second_level_domain: str = 'cryptcord-server.onrender'
    top_level_domain: str = 'com'
    port: int | None = Field(default=None, ge=0)
    ping_path: str = '/ping'
    fetch_data_path: str = '/data/fetch'
    post_exchange_key_path: str = '/data/post/exchange-key'
    post_message_path: str = '/data/post/message'

    @property
    def base_url(self) -> str:
        result = f'{self.scheme}://'
        if self.subdomain:
            result += f'{self.subdomain}.'
        result += f'{self.second_level_domain}.{self.top_level_domain}'
        if self.port is not None:
            result += f':{self.port}'
        return result

    @property
    def ping_url(self):
        return self.base_url + self.ping_path

    @property
    def fetch_data_url(self):
        return self.base_url + self.fetch_data_path

    @property
    def post_exchange_key_url(self):
        return self.base_url + self.post_exchange_key_path

    @property
    def post_message_url(self):
        return self.base_url + self.post_message_path

class _ServerSettingsModel(BaseModel):
    url: _UrlSettingsModel = _UrlSettingsModel()
    ping_timeout: float = Field(default=1.0, gt=0.0)
    request_timeout: float = Field(default=5.0, gt=0.0)
    fetch_interval: float = Field(default=5.0, gt=0.0)
    key_response_interval: float = Field(default=5.0, gt=0.0)

class _SettingsModel(BaseModel):
    display: _DisplaySettingsModel = _DisplaySettingsModel()
    key_bindings: _KeyBindingsModel = _KeyBindingsModel()
    local_database: _DatabaseSettingsModel = _DatabaseSettingsModel()
    server: _ServerSettingsModel = _ServerSettingsModel()

def _load_settings():
    # Create the settings file if necessary.
    if not os.path.exists('settings.yaml'):
        with open('settings.yaml', 'w') as _:
            pass

    # Load settings from the file.
    with open('settings.yaml', 'r') as file:
        data = safe_load(file)
        if isinstance(data, dict):
            settings = _SettingsModel.model_validate(data)
        else:
            settings = _SettingsModel()

    # Add default values to the file.
    with open('settings.yaml', 'w') as file:
        safe_dump(settings.model_dump(), file)

    # Return the settings object.
    return settings

settings = _load_settings()