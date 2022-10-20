"""Module that contains functions for preprocessing data."""

import abc

import numpy as np
import pandas as pd
from cleanco import basename
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.utils import column_or_1d
from unidecode import unidecode

__all__ = [
    "CleancoCleaner",
    "Lowercaser",
    "NumbersEliminator",
    "NotWordsEliminator",
    "Unidecoder",
]

_basename = np.vectorize(basename)
_lower = np.vectorize(str.lower)
_unidecode = np.vectorize(unidecode)


class _NoFitNeededTransformer(TransformerMixin, BaseEstimator, metaclass=abc.ABCMeta):

    """
    A base class for transformers that don't need to be fitted.
    Need to implement the `transform` method.
    """

    # noinspection PyUnusedLocal
    def fit(self, y):
        """
        Fit the transformer. Does nothing.

        Args:
            y: Array-like target.

        Returns:
            self.
        """

        return self

    @abc.abstractmethod
    def transform(self, y):
        """
        Transform the data.

        Args:
            y: Array-like target.

        Returns:
            Transformed data.

        """
        raise NotImplementedError()


# noinspection PyMethodMayBeStatic
class CleancoCleaner(_NoFitNeededTransformer):
    """
    A transformer that transforms labels to normalized company names.

    Examples:
        >>> from cmnsim.preprocessing import CleancoCleaner
        >>> cleaner = CleancoCleaner()
        >>> cleaner.transform(['ООО "Рога и Копыта"', 'ООО "Рога и Копыта"'])
        array(['ООО "Рога и Копыта"', 'ООО "Рога и Копыта"'])
        >>> cleaner.transform(["Some Big Pharma, LLC", "Some Big Pharma, LTD"])
        array(['Some Big Pharma', 'Some Big Pharma'])
    """

    def transform(self, y):
        """Transform labels to normalized company names."""
        y = column_or_1d(y, warn=True)
        return _basename(y)


# noinspection PyMethodMayBeStatic,SpellCheckingInspection
class Lowercaser(_NoFitNeededTransformer):

    """
    A transformer that transforms labels to lowercase.

    Examples:
        >>> from cmnsim.preprocessing import Lowercaser
        >>> lowercaser = Lowercaser()
        >>> lowercaser.transform(['ООО "Рога и Копыта"', 'ООО "Рога и Копыта"'])
        array(['ооо "рога и копыта"', 'ооо "рога и копыта"'])
    """

    def transform(self, y):
        """Transform labels to lowercase."""
        y = column_or_1d(y, warn=True)
        return _lower(y)


class RusStopWordsCleaner(_NoFitNeededTransformer):
    """
    A transformer that transforms labels to normalized russian company names.
    """

    STOP_WORDS = [
        "ооо",
        "общество с огранниченной ответственностью",
        "оао",
        "ао",
        "гк",
        "зао",
        "лтд",
        "нпф",
        "групп",
        "дистрибьюшн",
        "лимитед",
    ]

    def transform(self, y):
        """Transform labels to normalized company names."""
        y = column_or_1d(y, warn=True)
        return pd.Series(y).replace(self.STOP_WORDS, "", regex=True).values


# noinspection PyMethodMayBeStatic
class RegexEliminator(_NoFitNeededTransformer):

    """
    Base class for transformers that eliminate regex patterns from labels.
    """

    @property
    @abc.abstractmethod
    def _regex(self):
        """Return regex to eliminate."""
        raise NotImplementedError()

    def transform(self, y):
        """Transform labels to lowercase."""
        y = column_or_1d(y, warn=True)
        return (
            pd.Series(y)
            .replace(self._regex, " ", regex=True)
            .str.strip()
            .replace(r"\s\s+", "", regex=True)
            .values
        )


class NumbersEliminator(RegexEliminator):
    """
    Eliminate numbers from text.

    Examples:
        >>> from cmnsim.preprocessing import NumbersEliminator
        >>> eliminator = NumbersEliminator()
        >>> eliminator.transform(['ООО "Рога и Копыта 123"', 'ООО "Рога и Копыта 123"'])
        array(['ООО "Рога и Копыта"', 'ООО "Рога и Копыта"'])
    """

    _regex = r"\d+"


class NotWordsEliminator(RegexEliminator):
    r"""
    Eliminate not words by regex pattern [\W+].

    Examples:
        >>> from cmnsim.preprocessing import NotWordsEliminator
        >>> eliminator = NotWordsEliminator()
        >>> eliminator.transform(
        ...     ['ООО "Рога и Копыта ()"', 'ООО "Рога и Копыта 123 ()"']
        ... )
        array(['ООО Рога и Копыта', 'ООО Рога и Копыта 123'])
    """
    _regex = r"\W+"


# noinspection PyMethodMayBeStatic,SpellCheckingInspection
class Unidecoder(_NoFitNeededTransformer):
    """
    A transformer that transforms labels to unidecoded.

    Examples:
        >>> from cmnsim.preprocessing import Unidecoder
        >>> unidecoder = Unidecoder()
        >>> unidecoder.transform(['ООО "Рога и Копыта"', 'ООО "Рога и Копыта"'])
        array(['OOO "Roga i Kopyta"', 'OOO "Roga i Kopyta"'])
    """

    def transform(self, y):
        """Transform labels to lowercase."""
        y = column_or_1d(y, warn=True)
        return _unidecode(y)
