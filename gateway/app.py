import logging
import os

from pydantic import BaseModel
from rich.logging import RichHandler
from sanic import Sanic
from sanic.request import Request
from sanic.response import json
from sanic_ext import validate
from sanic_healthcheck import HealthCheck

from gateway.sessions import setup

app = Sanic("cmnsim-search")
setup(app)
health_check = HealthCheck(app)

logging.basicConfig(
    level="INFO", format="%(message)s", datefmt="[%X]", handlers=[RichHandler()]
)

log = logging.getLogger(__name__)


class SearchItem(BaseModel):
    query: str


class InsertItem(BaseModel):
    company_name: str
    company_url: str
    query_string: str
    normalized_name: str


def protected(func):
    async def wrapper(request: Request, *args, **kwargs):
        api_key = request.headers.get("X-API-KEY")
        if not await request.app.ctx.redis.exists(api_key):
            return json({"error": "Unauthorized"}, status=401)
        return await func(request, *args, **kwargs)

    return wrapper


@app.route("/insert", methods=["POST"])
@validate(json=InsertItem)
async def insert(request: Request, body: InsertItem):
    await request.app.ctx.cn_searcher.es_storage.insert_data(
        request.app.ctx.es_index, body.dict()
    )
    return json({}, status=202)


@app.route("/search", methods=["POST"])
@validate(json=SearchItem)
@protected
async def search(request, body: SearchItem):
    run_crawling = os.getenv("CRAWLING", "true").lower() == "true"
    result = await request.app.ctx.cn_searcher(body.query, crawling=run_crawling)
    return json(result)


# Define checks for the health check.
def check_health_random():
    return True, "Service is healthy"


if __name__ == "__main__":
    health_check.add_check(check_health_random)
    app.run(
        host=os.getenv("CMNSIM_GATEWAY_HOST", "localhost"),
        port=int(os.getenv("CMNSIM_GATEWAY_PORT", 5000)),
        workers=int(os.getenv("CMNSIM_WORKERS", 1)),
    )
