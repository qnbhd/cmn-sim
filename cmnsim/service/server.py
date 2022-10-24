import logging
import os
from pathlib import Path
from urllib.parse import unquote

from aiohttp import ClientSession
from sanic import Sanic, redirect

from cmnsim.preprocessing import FullTransformersPipeline
from cmnsim.service.tools.j2 import setup_jinja

app = Sanic("cmnsim")
app.config["GATEWAY_URI"] = os.getenv("GATEWAY_URI", "http://localhost:8000")
app.config["GATEWAY_API_KEY"] = os.getenv("GATEWAY_API_KEY", "KEY")

app.static("/static", Path(__file__).parent / "static")

setup_jinja(app)

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
    app.run(host="localhost", port=8000, debug=True, auto_reload=True)
