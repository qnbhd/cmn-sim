FROM python:3.10

ENV PYTHONUNBUFFERED=1
WORKDIR /root

COPY service service
COPY cmnsim cmnsim

RUN pip install --upgrade pip
RUN pip install --user --no-cache-dir -r service/requirements.txt
RUN pip install --user --no-cache-dir -r cmnsim/requirements.txt

RUN python -m spacy download xx_ent_wiki_sm

ENV PYTHONPATH "$PWD:$PYTHONPATH"
CMD ["python3", "service/server.py", "run"]
