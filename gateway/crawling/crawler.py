import asyncio
import inspect
import traceback
from collections import defaultdict
from dataclasses import dataclass
from typing import Callable, Dict, Set

import aiohttp

from gateway.utils.returns import Error, Ok, Result

UserAgent = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    " AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36"
}


@dataclass
class Item:
    company_name: str
    company_url: str
    query_string: str
    normalized_name: str

    def asdict(self):
        return {
            "company_name": self.company_name,
            "company_url": self.company_url,
            "query_string": self.query_string,
            "normalized_name": self.normalized_name,
        }


class Crawler:
    """
    Urls crawler.

    Methods:
        add_transformer: Adds a transformer to the crawler.
        add_side_effect: Adds a side effect to the crawler.
        add_invader: Adds a invader to the crawler.
        crawl: Crawls the given urls and returns a mapping
         from url to the `Result` with `Item` instance.
        close: Closes the crawler's session.

    Attributes:
        transformers: The list of transformers.
        side_effects: The list of side effects.
        invaders: The list of invaders.

    Examples:
        >>> from gateway.crawling.crawler import Crawler
        >>> from gateway.utils.returns import Result, Ok, Error
        >>>
        >>> async def main():
        >>>     crawler = Crawler()
        >>>     crawler.add_invader(lambda html: html)
        >>>     crawler.add_transformer(lambda html: html)
        >>>     crawler.add_side_effect(lambda cr, html: print(html))
        >>>     result: Result[Dict[str, Set[str]]] = await crawler.crawl(['https://google.com'])
        >>>     if isinstance(result, Ok):
        >>>         print(result.result)
        >>>     else:
        >>>         print(result.message)
        >>>
        >>> asyncio.run(main())

    """

    def __init__(self):
        self.transformers = []
        self.side_effects = []
        self.invaders = []

    def add_transformer(self, transformer: Callable[[str], str]):
        """
        Adds a transformer to the crawler.
        Transformers needed to take most important
        information from invader's result.

        Args:
            transformer: The transformer to add.

        Returns:
            None
        """

        self.transformers.append(transformer)

    def add_side_effect(self, side_effect: Callable):
        """
        Adds a side effect to the crawler.
        Side effects can be: write results to file, send results to server, etc.

        Args:
            side_effect: The side effect to add.

        Returns:
            None
        """

        self.side_effects.append(side_effect)

    def add_invader(self, invader: Callable[["Crawler"], None]):
        """
        Adds a invader to the crawler.
        Invader - a function from target html to extracted data.

        Args:
            invader: The invader to add.
        """

        self.invaders.append(invader)

    async def crawl(self, urls) -> Result[Dict[str, Item]]:
        """
        Crawls the given urls and returns Result with a mapping
        from url to the results set or Error instance.

        Args:
            urls: The urls to crawl.

        Returns:
            A mapping from url to the results set.
        """

        results: Dict[str, Item] = defaultdict(lambda: Item("", "", "", ""))

        for url in urls:
            try:
                async with aiohttp.ClientSession() as session, session.get(
                    url, headers=UserAgent
                ) as resp:
                    html = await resp.text()

                    if resp.status != 200:
                        continue

                    variants: Set[str] = set()

                    for invader in self.invaders:
                        f = invader(html)
                        # make composition
                        for transformer in self.transformers:
                            f = transformer(f)

                        # if result is empty, skip
                        if not f:
                            continue

                        variants.add(f)

                        # do side effects
                        for side_effect in self.side_effects:
                            if inspect.iscoroutinefunction(side_effect):
                                await side_effect(self, f)
                                continue
                            side_effect(self, f)

                    company_url = url
                    company_name = min(variants, key=len).capitalize()
                    normalized_name = company_name.lower()
                    query_string = ""
                    results[url] = Item(
                        company_name, company_url, query_string, normalized_name
                    )

            except asyncio.exceptions.TimeoutError:
                return Error(f"Timeout error for url {url}", code=1)

            except Exception as e:
                print(traceback.format_exc())
                return Error(message=str(e), code=100)

        return Ok(results)
