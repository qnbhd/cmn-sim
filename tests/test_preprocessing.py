import numpy.testing as npt

from cmnsim.preprocessing import (
    CleancoCleaner,
    FullTransformersPipeline,
    Lowercaser,
    NotWordsEliminator,
    NumbersEliminator,
    RusStopWordsCleaner,
    Spacy,
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


def test_rus_stop_words_cleaner():
    cleaner = RusStopWordsCleaner()

    npt.assert_array_equal(
        cleaner.transform(["ооо рога и копыта групп", "ооо рога и копыта групп"]),
        ["рога и копыта", "рога и копыта"],
    )


def test_unidecoder():
    unidecoder = Unidecoder()
    npt.assert_array_equal(
        unidecoder.transform(['ООО "Рога и Копыта 123"', 'ООО "Рога и Копыта 123"']),
        ['OOO "Roga i Kopyta 123"', 'OOO "Roga i Kopyta 123"'],
    )


def test_spacy():
    sp = Spacy()
    npt.assert_array_equal(
        sp.transform(["VK mobile version | VK"]),
        "VK",
    )


def test_pipeline():
    pipeline = FullTransformersPipeline()

    npt.assert_array_equal(
        pipeline.transform(
            [
                '"Big Pharma", LTD',
                '"Big Pharma 123", LLC',
                'ооо 123 "рога и копыта групп" 456',
                "ооо рога и копыта групп",
            ]
        ),
        ["big pharma", "big pharma", "roga i kopyta", "roga i kopyta"],
    )
