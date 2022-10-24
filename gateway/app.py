import logging
import os

from pydantic import BaseModel
from sanic import Sanic
from sanic.request import Request
from sanic.response import json
from sanic_ext import validate

from gateway.sessions import setup

app = Sanic("cmnsim-search")
setup(app)

logging.basicConfig(level=logging.INFO, format="[%(levelname)s]: %(message)s")

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


if __name__ == "__main__":
    app.run(
        host=os.getenv("SANIC_HOST", "0.0.0.0"),
        port=int(os.getenv("SANIC_PORT", 5002)),
        workers=int(os.getenv("SANIC_WORKERS", 1)),
    )
