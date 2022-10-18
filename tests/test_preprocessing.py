import numpy.testing as npt
from sklearn.pipeline import Pipeline

from cmnsim.preprocessing import (
    CleancoCleaner,
    Lowercaser,
    NotWordsEliminator,
    NumbersEliminator,
    Unidecoder,
)


def test_cleanco_cleaner():
    cleaner = CleancoCleaner()

    npt.assert_array_equal(
        cleaner.transform(["Some Big Pharma, LLC", "Some Big Pharma, LTD"]),
        ["Some Big Pharma", "Some Big Pharma"],
    )


def test_lowercaser():
    lowercaser = Lowercaser()
    npt.assert_array_equal(
        lowercaser.transform(['ООО "Рога и Копыта"', 'ООО "Рога и Копыта"']),
        ['ооо "рога и копыта"', 'ооо "рога и копыта"'],
    )


def test_numbers_eliminator():
    eliminator = NumbersEliminator()
    npt.assert_array_equal(
        eliminator.transform(['ООО "Рога и Копыта 123"', 'ООО "Рога и Копыта 123"']),
        ['ООО "Рога и Копыта"', 'ООО "Рога и Копыта"'],
    )


def test_not_words_eliminator():
    eliminator = NotWordsEliminator()
    npt.assert_array_equal(
        eliminator.transform(['ООО "Рога и Копыта 123"', 'ООО "Рога и Копыта 123"']),
        ["ООО Рога и Копыта 123", "ООО Рога и Копыта 123"],
    )


def test_unidecoder():
    unidecoder = Unidecoder()
    npt.assert_array_equal(
        unidecoder.transform(['ООО "Рога и Копыта 123"', 'ООО "Рога и Копыта 123"']),
        ['OOO "Roga i Kopyta 123"', 'OOO "Roga i Kopyta 123"'],
    )


def test_pipeline():
    pipeline = Pipeline(
        [
            ("cleanco_cleaner", CleancoCleaner()),
            ("lowercaser", Lowercaser()),
            ("numbers_eliminator", NumbersEliminator()),
            ("not_words_eliminator", NotWordsEliminator()),
            ("unidecoder", Unidecoder()),
        ]
    )

    npt.assert_array_equal(
        pipeline.transform(
            ['"Big Pharma", LTD', '"Big Pharma 123", LLC', 'ООО "Рога и Копыта 123"']
        ),
        ["big pharma", "big pharma", "ooo roga i kopyta"],
    )
