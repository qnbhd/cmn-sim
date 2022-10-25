from pathlib import Path

import pandas as pd
from elasticsearch import Elasticsearch, helpers

from cmnsim.preprocessing import FullTransformersPipeline

es = Elasticsearch(["http://localhost:9200/"])
print(es.ping())

pd.set_option("display.width", None)


def preprocess(lb, ub):
    df = pd.read_csv(Path(__file__).parent.joinpath("0-train-raw.csv"))

    df = df[df["is_duplicate"] == 0][lb:ub]

    names = pd.concat([df["name_1"], df["name_2"]])
    names.drop_duplicates(inplace=True)
    names = names[names.str.len() >= 2]

    normalized = pd.Series(FullTransformersPipeline().transform(names))

    frame = {
        "company_name": normalized.str.capitalize(),
    }

    df = pd.DataFrame(frame)
    df["normalized_name"] = normalized
    df["company_url"] = ""
    df["query_string"] = pd.Series(names.values)
    df["id"] = df.index

    return df


def doc_generator(df, index_name):
    df_iter = df.iterrows()
    for index, document in df_iter:
        res = {
            "_index": index_name,
            # "_id": f"{document['id']}",
            "_source": {key: value for key, value in document.items() if key != "id"},
        }
        print(res)
        yield res


def main():
    from rich.progress import track

    for lindex in track(range(0, 497000, 1000)):
        df = preprocess(lindex, lindex + 1000)
        helpers.bulk(es, doc_generator(df, "test"))


if __name__ == "__main__":
    main()
