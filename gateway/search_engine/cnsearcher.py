import json
import logging
from functools import partial

from bs4 import BeautifulSoup

from cmnsim.misc.returns import Error
from cmnsim.misc.spacy_wrapper import process_spacy
from gateway.crawling.crawler import Crawler
from gateway.search_engine.elasti import CNElasticStorage
from gateway.search_engine.schemas import search_response_from_crawler
from gateway.utils import gsearch
from gateway.utils.merger import merge_matches

log = logging.getLogger(__name__)

EXCLUDE_REGEX = [
    r"https:\/\/www\.linkedin\.com\/.+",
    r"https:\/\/vk\.com\/.+",
    r"https:\/\/www\.facebook\.com\/.+",
    r"https:\/\/twitter\.com\/.+",
    r"https:\/\/www\.instagram\.com\/.+",
    r"https:\/\/www\.youtube\.com\/.+",
    r"https:\/\/www\.pinterest\.com\/.+",
    r"https:\/\/www\.tumblr\.com\/.+",
    r"https:\/\/www\.wikipedia.org\/.+",
    r"https:\/\/www\.yelp\.com\/.+",
    r"https:\/\/www\.glassdoor\.com\/.+",
    r"https:\/\/www\.ok\.ru\/.+",
]


def parse_title_from_html(html):
    """
    Parse title from html.

    Args:
        html: HTML to parse.

    Returns:
        Title or empty string.
    """

    soup = BeautifulSoup(html, "html.parser")
    if soup.title:
        return soup.title.text
    return ""


class CNSearcher:

    """
    CNSearch encapsulates search logic.

    Pipeline:
        1. Search in ES.
        2. If no results found, search company web-site in Google.
        3. If results found, crawl them, index in ES and return.
        4. If no results found, return empty results.

    Class attributes:
        TARGET_FIELDS: List of fields to search in.

    Args:
        uri: ES URI.
        index_name: ES index name.

    Attributes:
        es_storage: ES storage.
        uri: ES URI.
        index_name: ES index name.
        crawler: Crawler instance.

    Methods:
        __call__: Search for company name in ES.
        close: Close ES connection.

    """

    TARGET_FIELDS = ["company_name", "company_url", "normalized_name", "query_string"]

    def __init__(self, uri, index_name, timeout=10):
        """
        Initialize CNSearcher.

        Args:
            uri: ES URI.
            index_name: ES index name.

        """

        self.es_storage = CNElasticStorage(uri, timeout=timeout)
        self.uri = uri
        self.index_name = index_name

        self.crawler = Crawler()
        self.crawler.add_invader(parse_title_from_html)
        self.crawler.add_side_effect(
            lambda cwl, x: log.info(f"Name `{x}` was crawled.")
        )
        self.crawler.add_transformer(process_spacy)

    # noinspection PyProtectedMember
    async def __call__(self, company_name, crawling=True, *args, **kwargs):
        """
        Search for company name in ES.
        If no results found, search company web-site, crawl it
        and index them in ES.

        Args:
            company_name: Company name to search for.
            crawling: If True, crawl company web-site.
            *args: Additional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            Search results.

        .. note::
            This method is a coroutine.

        .. note::
            Searching in Google + Crawling is slow.

        ..note::
            Crawl (or search in Google) can be blocked by Google (429).
        """

        results = await self._make_request(company_name)

        log.info(f"Search results: {results}")

        log.info(f"Crawling flag: {crawling}")

        if results["query"]["matches"] or not crawling:
            return results

        log.info("No results found in ES. Searching in Google.")
        log.info(f"Query: {company_name}")

        lst = await gsearch.search(company_name, num_results=1, exclude=EXCLUDE_REGEX)

        results = []

        for url in lst:
            log.info(f"Crawl URL: {url}")
            result = await self.crawler.crawl([url])

            if isinstance(result, Error):
                log.error(result)
                continue

            item = result.result[url]

            # Crawler not known about raw query string, need to fill it manually.
            item.query_string = company_name
            results.append(item)

            await self.es_storage.insert_data(self.index_name, item.asdict())

        return search_response_from_crawler(company_name, results)

    async def _make_request(self, query):
        """
        Make search request to ES.
        Search occurs across multiple fields, such as `company_name`,
        `normalized_name`, `query_string`, `company_url`.

        Args:
            query: Query string.

        Returns:
            Search results.
        """

        do = partial(
            self.es_storage.search_data,
            index_name=self.index_name,
            query_string=query,
        )

        final_ = {"query": {"query_string": query, "matches": {}}}
        results = [await do(target_field=field) for field in self.TARGET_FIELDS]

        log.info(json.dumps(results, indent=4))

        matches = merge_matches([result["query"]["matches"] for result in results])

        log.info(f"After merge: {matches}")

        final_["query"]["matches"] = matches

        return final_

    async def close(self):
        """
        Close ES connection.

        Returns:
            None.
        """

        await self.es_storage.close()

    async def is_ready(self):
        return await self.es_storage.ping()
