import pathlib
import tomllib
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # main settings
    debug: bool = False
    app_name: str = 'Template backend'
    port: int = 8000

    # proxy settings
    root_path: str = ''
    workers: int = 4

    model_config = SettingsConfigDict(env_file='.env', extra='ignore')


@lru_cache
def get_version() -> str:
    with pathlib.Path('pyproject.toml').open('rb') as f:
        data = tomllib.load(f)
    return data['project']['version']


@lru_cache
def get_description() -> str:
    with pathlib.Path('pyproject.toml').open('rb') as f:
        data = tomllib.load(f)
    return data['project']['description']


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
descriiption = get_description()
version = get_version()
