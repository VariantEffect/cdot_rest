FROM python:3.11-slim AS python-base

# git CLI
RUN apt-get update && apt-get install -y git gcc libpq-dev && rm -rf /var/lib/apt/lists/*

## Prepare virtual env
ENV VIRTUAL_ENV="/venv"
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
RUN python3 -m venv $VIRTUAL_ENV

## Python path
ENV PYTHONPATH="$PYTHONPATH:/code/cdot_rest"

WORKDIR /code

## Prepare dependencies
COPY requirements.txt .
# python deps
RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install gunicorn
RUN python3 -m pip install psycopg2
# application deps
RUN python3 -m pip install -r requirements.txt

## Download static CDOT transcript files
WORKDIR /data
COPY bin/download_latest_cdot_transcript_files.py .
RUN python3 download_latest_cdot_transcript_files.py
RUN rm download_latest_cdot_transcript_files.py

## Prepare rest server
WORKDIR /code
COPY manage.py .
COPY bin/load_cdot_transcript_files.py .
COPY cdot_json/ cdot_json/
COPY cdot_rest/ cdot_rest/
