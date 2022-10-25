FROM elasticdump/elasticsearch-dump

WORKDIR /root
COPY dumps dumps

ARG ELASTIC_URL=http://elasticsearch:9200/test

CMD ["elasticdump", "--input=dumps/elastic_companies_dump.json", "--output=$ELASTIC_URL", "--type=data"]
