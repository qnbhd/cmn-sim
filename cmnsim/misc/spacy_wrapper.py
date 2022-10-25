from functools import lru_cache

import spacy


@lru_cache(None)
def get_nlp(language):
    """
    Get spacy NLP.

    Args:
        language: Language SPACY model.

    Returns:
        NLP object.
    """

    # noinspection PyBroadException
    try:
        nlp = spacy.load(language)
    except Exception:
        from spacy.cli.download import download

        download(language)
        nlp = spacy.load(language)
    return nlp


def process_spacy(x: str) -> str:
    """
    Process spacy.

    Args:
        x: Text to process.

    Returns:
        Normalized text.
    """

    nlp = get_nlp("xx_ent_wiki_sm")
    result = nlp(str(x)).ents

    if result:
        return result[0].text

    return x
