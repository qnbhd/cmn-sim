from pathlib import Path

import jinja2
from jinja2 import ChoiceLoader, Environment, FileSystemLoader
from sanic import html


class Jinja:
    def __init__(self):
        loader1 = FileSystemLoader(Path(__file__).parent.parent / "static")
        loader = ChoiceLoader([loader1])
        self.env = Environment(loader=loader)

    @staticmethod
    def update_request_context(request, context):
        context.setdefault("request", request)
        context.update({"url_for": request.app.url_for})

    def render_string(self, template, request, **context):
        self.update_request_context(request, context)
        return self.env.get_template(template).render(**context)

    def render(self, template, request, **context):
        return html(self.render_string(template, request, **context))


jinja2.select_autoescape(
    enabled_extensions=("html", "htm", "xml"),
    disabled_extensions=(),
)


def setup_jinja(app):
    app.ctx.j2 = Jinja()
