import http
import importlib
import time
import typing as tp
from contextlib import asynccontextmanager
from importlib import resources

import uvicorn
from fastapi import APIRouter, FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html, get_swagger_ui_oauth2_redirect_html
from fastapi.staticfiles import StaticFiles
from src.apps.http.manager import ServerManager
from src.apps.http.settings import descriiption, settings, version


@asynccontextmanager
async def _lifespan(_app: FastAPI) -> tp.AsyncGenerator[None, None]:
    print('Lifespan calls')
    yield


app = FastAPI(
    lifespan=_lifespan,
    title=settings.app_name,
    summary=descriiption,
    version=version,
    root_path=settings.root_path,
    redoc_url=None,
    docs_url=None
)

app.mount(
    "/static",
    StaticFiles(directory="./src/apps/http/_static"),
    name="static"
)

# подключаем все роуты
plugins = [
    resource.name
    for resource in resources.files("src.apps.http").iterdir()
    if not resource.is_file() and not resource.name.startswith("_")
]

routers: list[APIRouter] = []
for plugin in sorted(plugins):
    module = importlib.import_module(f"src.apps.http.{plugin}.router")
    routers.append(module.router)

routers.sort(key=lambda r: r.prefix)
for router in routers:
    app.include_router(router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def custom_middleware(request: Request, call_next: tp.Callable[[Request], tp.Any]) -> Response:
    start_time = time.time()
    try:
        response: Response = await call_next(request)
        process_time_ms = round((time.time() - start_time) * 1000, 6)
        response.headers["X-Process-Time"] = f"{process_time_ms} ms"
        return response
    except Exception as e:
        process_time_ms = round((time.time() - start_time) * 1000, 6)
        response = Response(
            content=http.HTTPStatus.INTERNAL_SERVER_ERROR.phrase,
            status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR.real
        )
        response.headers["X-Process-Time"] = f"{process_time_ms} ms"
        raise e


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html() -> Response:
    return get_swagger_ui_html(
        openapi_url=f"{settings.root_path}.{app.openapi_url}",
        title=app.title,
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url=f"{settings.root_path}/static/swagger/swagger-ui-bundle.js",
        swagger_css_url=f"{settings.root_path}/static/swagger/swagger-ui.css",
        swagger_favicon_url=f"{settings.root_path}/static/swagger/favicon.png",
    )


@app.get(app.swagger_ui_oauth2_redirect_url or '', include_in_schema=False)
async def swagger_ui_redirect() -> Response:
    return get_swagger_ui_oauth2_redirect_html()


def main() -> None:
    app_path: str = "src.apps.http.main:app"

    if settings.debug:
        uvicorn.run(
            app_path,
            host="127.0.0.1",
            reload=True,
            port=settings.port,
            workers=1,
            access_log=True,
            root_path=settings.root_path
        )
    else:
        options = {
            "bind": f"0.0.0.0: {settings.port}",
            "workers": settings.workers,
            "worker_class": "src.apps.http.manager.Worker",
            "accesslog": "-"
        }

        ServerManager(app_path, options).run()


if __name__ == "__main__":
    main()
