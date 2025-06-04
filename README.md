# cdot_rest

REST server for [cdot](https://github.com/SACGF/cdot/)

We host historical versions of RefSeq and Ensembl transcripts (GRCh37/GRCh38), to resolve [HGVS](http://varnomen.hgvs.org/)

See http://cdot.cc


### Building for Docker

The Docker file for this repo will build a container containing the cdot-rest source code with
dependencies installed and the static files downloaded. Because loading the data requires a Redis
instance, this must be done as a separate step.

```
docker build --tag cdot-rest .
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
python3 load_cdot_transcript_files.py
```
