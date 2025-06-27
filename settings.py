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


class _SettingsModel(BaseModel):
    display: _DisplaySettingsModel = _DisplaySettingsModel()
    key_bindings: _KeyBindingsModel = _KeyBindingsModel()
    local_database: _DatabaseSettingsModel = _DatabaseSettingsModel()

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