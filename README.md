# cdot_rest

REST server for [cdot](https://github.com/SACGF/cdot/), tuned for internal MaveDB use.

See http://cdot.cc


### Building for Docker

The Docker file for this repo will build a container containing the cdot-rest source code with
dependencies installed and the static files downloaded. Because loading the data requires a Redis
instance, this must be done as a separate step.

```
docker build --tag cdot-rest .
```

Run this image as part of a docker-compose stack with
```
version: "3"

services:

  redis:
    image: redis:7.2.3
    env_file:
      - settings/.env.template
    ports:
      - "6381:6379"

  cdot-rest:
    image: cdot-rest
    command: bash -c "gunicorn cdot_rest.wsgi:application --bind 0.0.0.0:8000"
    env_file:
      - settings/.env.template
    depends_on:
      - redis
    ports:
      - "8002:8000"
```

_Note that building the image in this manner will ignore Gunicorn and Nginx configuration in the
/config directory._

### Loading data

You may load data from individual files with the following command
```
python3 manage.py import_transcript_json <filename> --annotation-consortium=<annotation-consortium> --cdot-data-version <version>
```

You may also load a batch of files from a given directory by using the `load_cdot_transcript_files.py`
script. Loading files in this manner will infer the annotation consortium and cdot data version from
the filename:
```
python3 load_cdot_transcript_files.py /data
```
