FROM python:3.10

ENV PYTHONUNBUFFERED=1
WORKDIR /root

COPY gateway gateway
COPY cmnsim cmnsim

RUN pip install --upgrade pip
RUN pip install --user --no-cache-dir -r gateway/requirements.txt
RUN python -m spacy download xx_ent_wiki_sm

ENV PYTHONPATH "$PWD:$PYTHONPATH"
CMD ["python3", "gateway/app.py", "run"]
