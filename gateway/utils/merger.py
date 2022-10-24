from typing import Dict, List


def merge_matches(matches: List[Dict]) -> Dict:
    """
    Merge matches from different queries.

    Args:
        matches: List of matches.

    Returns:
        Dict: Merged matches.
    """

    merged: Dict[str, Dict] = {}

    for match_dict in matches:
        for match, value in match_dict.items():
            merged[match] = merged.get(match, value)
            merged[match]["score"] = max(merged[match]["score"], value["score"])

    return merged
