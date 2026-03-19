import typing as tp

from gunicorn.app.wsgiapp import WSGIApplication
from gunicorn.config import Config
from src.apps.http.settings import settings
from uvicorn.workers import UvicornWorker


class ServerManager(WSGIApplication):
    """ Реализация программной конфигурации сервера gunicorn """

    def __init__(self,
                 app_url: str,
                 options: dict[str, tp.Any] | None = None,
                 ) -> None:
        """
        Args:
            app_url (str): путь (import-like) до запускаемого приложения
            options (dict[str, tp.Any] | None, optional): словарь настроек сервера gunicorn
        """
        self.app_url = app_url
        self.options = options or {}
        super().__init__()

    def load_config(self) -> None:
        config = {
            key: value
            for key, value in self.options.items()
            if isinstance(self.cfg, Config) and key in self.cfg.settings and value is not None
        }

        for key, value in config.items():
            if isinstance(self.cfg, Config):
                self.cfg.set(key.lower(), value)


class Worker(UvicornWorker):
    CONFIG_KWARGS = {  # noqa: RUF012
        "root_path": settings.root_path
    }
