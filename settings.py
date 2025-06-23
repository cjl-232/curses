import os

from pydantic import BaseModel, Field
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

class _SettingsModel(BaseModel):
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