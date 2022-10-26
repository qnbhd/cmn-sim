import logging
import os
from pathlib import Path
from urllib.parse import unquote

from aiohttp import ClientSession
from rich.logging import RichHandler
from sanic import Sanic
from sanic.response import redirect
from service.utils.j2 import setup_jinja

from cmnsim.preprocessing import FullTransformersPipeline

app = Sanic("cmnsim")
app.config["GATEWAY_URI"] = os.getenv("GATEWAY_URI", "http://127.0.0.1:5000")
app.config["GATEWAY_API_KEY"] = os.getenv("GATEWAY_API_KEY", "")

app.static("/static", Path(__file__).parent / "static")

setup_jinja(app)

logging.basicConfig(
    level="INFO", format="%(message)s", datefmt="[%X]", handlers=[RichHandler()]
)

log = logging.getLogger(__name__)


@app.route("/")
async def index(request):
    return app.ctx.j2.render("index.html", request=request)


@app.route("/search")
async def search(request):
    return redirect("/")


@app.route("/search/<query>")
async def search_name(request, query):

    uri = f"{app.config['GATEWAY_URI']}/search"
    query = unquote(query)

    [query] = FullTransformersPipeline().transform([query])

    req = {"query": str(query)}
    headers = {"X-API-KEY": request.app.config["GATEWAY_API_KEY"]}

    async with ClientSession() as session:
        async with session.post(uri, json=req, headers=headers) as response:
            try:
                relevant = await response.json()
            except Exception as e:
                relevant = {"error": str(e)}

    if "error" in relevant:
        print("Error:", relevant["error"])

    result = []
    query_result = relevant.get("query", {"matches": dict()})

    for match, value in query_result["matches"].items():
        result.append(value)

    result = sorted(result, key=lambda x: x["score"], reverse=True)
    return app.ctx.j2.render("search.html", request=request, results=result)


if __name__ == "__main__":
    app.run(
        host=os.getenv("CMNSIM_SERVICE_HOST", "localhost"),
        port=int(os.getenv("CMNSIM_SERVICE_PORT", 8000)),
        workers=int(os.getenv("CMNSIM_SERVICE_WORKERS", 1)),
    )
