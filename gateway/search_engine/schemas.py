from typing import Any, Dict, List, Literal

from gateway.crawling.crawler import Item

ElasticRequest = Dict[str, Any]
Fuzziness = Literal["0", "1", "2", "AUTO"]


def elastic_match_fuzzy(
    *,
    query: str,
    field: str,
    fuzziness: Fuzziness = "1",
) -> ElasticRequest:
    """
    Match query with fuzziness.

    Args:
        query: Query string.
        field: Field to match.
        fuzziness: Fuzziness level.

    Returns:
        ElasticRequest: Elastic request.
    """

    return {
        "query": {
            "match": {
                field: {
                    "query": query,
                    "fuzziness": fuzziness,
                }
            }
        }
    }


def search_response_from_crawler(query_string, items: List[Item]) -> Dict:
    """
    Get search response from Items list.

    Args:
        query_string: Query string.
        items: List of items.

    Returns:
        Dict: Search response.
    """

    return {
        "query": {
            "query_string": query_string,
            "matches": {
                item.normalized_name: {
                    "score": 1.0,
                    "company_name": item.company_name,
                    "company_url": item.company_url,
                    "query_string": item.query_string,
                }
                for item in items
            },
        }
    }


def elastic_relevant_response(query_string: str, hits: list, threshold=0.01) -> Dict:
    """
    Get relevant response from ES hits.

    Args:
        query_string: Query string.
        hits: List of hits.
        threshold: Threshold value.

    Returns:
        Dict: Search response.
    """

    def get_shorter_name(hit):
        source = hit["_source"]
        return min((x for x in source if "_name" in x), key=len)

    return {
        "query": {
            "query_string": query_string,
            "matches": {
                get_shorter_name(hit): {
                    "score": hit["_score"],
                    "normalized_name": hit["_source"]["normalized_name"],
                    "company_name": hit["_source"]["company_name"],
                    "company_url": hit["_source"]["company_url"],
                }
                for hit in hits
                if hit["_score"] > threshold
            },
        }
    }
