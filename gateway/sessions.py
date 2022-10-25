import logging
import os
import time
from pathlib import Path

import aioredis

from gateway.search_engine.cnsearcher import CNSearcher

log = logging.getLogger(__name__)


def setup(app):
    app.config["redis"] = os.getenv("REDIS_URL", "redis://127.0.0.1:6379")

    elastic_url = os.getenv("ELASTIC_URL")
    elastic_index = os.getenv("ELASTIC_INDEX")

    if elastic_url is None or elastic_index is None:
        log.error("Elasticsearch URI and index must be specified")
        exit(0)

    app.ctx.cn_searcher = CNSearcher(elastic_url, elastic_index)

    app.ctx.es_url = elastic_url
    app.ctx.es_index = elastic_index

    @app.listener("before_server_start")
    async def server_init(app_, loop):
        """Server init."""

        create_index = os.getenv("ELASTIC_CREATE_INDEX", "false").lower() == "true"

        log.info(f"Creating index: {create_index}")

        if create_index:
            await app.ctx.cn_searcher.es_storage.create_index(elastic_index)

        app_.ctx.redis = await aioredis.from_url(
            app_.config["redis"], decode_responses=True
        )

        # UNSAFE: only for testing
        with open(Path(__file__).parent.joinpath("api_keys.txt")) as f:
            for line in f:
                await app_.ctx.redis.set(line.strip(), 1)
        # UNSAFE
