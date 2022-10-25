import json
import logging
from pathlib import Path
from typing import Dict, List

from elasticsearch import AsyncElasticsearch

from gateway.search_engine.schemas import (
    Fuzziness,
    elastic_match_fuzzy,
    elastic_relevant_response,
)

log = logging.getLogger(__name__)


class CNElasticStorage:
    def __init__(self, uri: str, timeout=10):
        self.es_client = AsyncElasticsearch([uri], timeout=timeout)

    async def create_index(self, index_name: str, force=False):
        """
        Create an ES index.

        Args:
            index_name (str): Name of the index.
            force (bool): Force create index.

        Returns:
            None
        """

        with open(Path(__file__).parent / "elastic_mapping.json") as f:
            mapping = json.load(f)

        log.info(
            f"Creating index {index_name} with the following schema:"
            f" {json.dumps(mapping, indent=2)}"
        )

        if force:
            await self.es_client.indices.delete(index=index_name, body=mapping)  # type: ignore

        if not await self.es_client.indices.exists(index=index_name):
            await self.es_client.indices.create(index=index_name, body=mapping)  # type: ignore
        else:
            log.info(f"Index {index_name} already exists.")

    async def insert_data(self, index_name: str, data: Dict, check_exists=False):
        """
        Insert data into an ES index.

        Args:
            index_name (str): Name of the index.
            data (Dict): Data to be inserted.
            check_exists (bool): Check if the data already exists.

        Returns:
            None
        """

        log.info(f"Trying to insert data into ES {data}")

        if check_exists:
            resp = await self.search_data(
                index_name=index_name,
                target_field="normalized_name",
                query_string=data["normalized_name"],
                fuzziness="0",
            )

            if resp["query"]["matches"]:
                log.info(f"Data already exists in ES {data}")
                return

        log.info(f"Inserting data into index {index_name}")

        await self.es_client.index(index=index_name, body=data)  # type: ignore

    async def search_data(
        self,
        *,
        index_name: str,
        target_field: str,
        query_string: str,
        fuzziness: Fuzziness = "1",
    ) -> Dict:
        """
        Search data in an ES index.

        Args:
            index_name (str): Name of the index.
            query_string (str): Query string.
            target_field (str): Target field to search in.
            fuzziness (str): Fuzziness level.

        Returns:
            List: List of results.
        """

        assert fuzziness in ("0", "1", "2"), "Fuzziness must be 0, 1 or 2"
        assert target_field in (
            "normalized_name",
            "query_string",
            "company_name",
            "company_url",
        ), (
            "Target field must be one of"
            " normalized_name, query_string,"
            " company_name or company_url"
        )

        log.info(f"Searching data from index {index_name}")

        res = await self.es_client.search(  # type: ignore
            index=index_name,
            body=elastic_match_fuzzy(
                query=query_string, field=target_field, fuzziness=fuzziness
            ),
        )

        log.info(f"Search results: {res}")

        relevant = elastic_relevant_response(query_string, res["hits"]["hits"])

        log.info(f"Relevant results: {json.dumps(relevant, indent=4)}")

        return relevant

    async def ping(self):
        try:
            await self.es_client.ping()
            return True
        except Exception:
            return False

    async def close(self):
        await self.es_client.close()
