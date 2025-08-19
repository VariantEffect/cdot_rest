import os
import gzip
import ijson
import json
import pickle
import redis
import logging
import re
from itertools import islice

import click

from cdot.hgvs.dataproviders import LocalDataProvider
from cdot import __version__
from cdot_rest.settings import REDIS_KWARGS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def chunks(data, size=10000):
    """Yield successive chunks of data."""
    it = iter(data)
    for i in range(0, len(data), size):
        yield {k: data[k] for k in islice(it, size)}


ANNOTATION_CONSORTIUMS = {"refseq": "RefSeq", "ensembl": "Ensembl"}
ANNOTATION_CONSORTIUM_COUNTS = {k: 0 for k in ANNOTATION_CONSORTIUMS.keys()}


@click.command()
@click.argument("directory", type=click.Path(exists=True))
def load_cdot_transcript_files(directory):
    """Load CDOT transcript files from a directory into Redis."""

    r = redis.Redis(**REDIS_KWARGS)

    files = os.listdir(directory)

    if not files:
        logger.warning("No files found in the specified directory.")
        return

    for filename in files:
        if not filename.endswith(".json.gz"):
            logger.warning(f"Skipping non-CDOT file: {filename}")
            continue

        with gzip.open(os.path.join(directory, filename), "rt") as f:
            logger.info(f"Reading cdot JSON {filename}...")

            transcripts_data = {}

            def transcripts_iter():
                for transcript_id, transcript in ijson.kvitems(f, "transcripts"):
                    transcript["cdot_data_version"] = __version__
                    transcripts_data[transcript_id] = json.dumps(transcript)
                    yield transcript_id, transcript

            tx_by_gene, tx_intervals = LocalDataProvider._get_tx_by_gene_and_intervals(
                transcripts_iter()
            )

            logger.info("Inserting into Redis...")
            for td in chunks(transcripts_data):
                r.mset(td)

            # Increment counts for the annotation consortium
            matched_consortium = re.search(r"(refseq|ensembl)", filename, re.IGNORECASE)
            if matched_consortium:
                matched_consortium = matched_consortium.group(1).lower()
                inserted_transcripts = len(transcripts_data)
                if matched_consortium in ANNOTATION_CONSORTIUM_COUNTS:
                    ANNOTATION_CONSORTIUM_COUNTS[matched_consortium] += (
                        inserted_transcripts
                    )
                else:
                    ANNOTATION_CONSORTIUM_COUNTS[matched_consortium] = (
                        inserted_transcripts
                    )

                key = f"{matched_consortium}_count"
                r.set(key, ANNOTATION_CONSORTIUM_COUNTS[matched_consortium])
                logger.info(
                    f"File contained {inserted_transcripts} transcripts for {matched_consortium}."
                )

            else:
                logger.warning(
                    f"Unknown consortium '{matched_consortium}' in filename: {filename}"
                )
                logger.warning(
                    f"Inserted {len(transcripts_data)} transcripts, but not counting them."
                )
            del transcripts_data

            logger.info("Adding gene data...")
            f.seek(0)
            genes_data = {}
            for gene_id, gene in ijson.kvitems(f, "genes"):
                if gene_symbol := gene.get("gene_symbol"):
                    genes_data[gene_symbol] = json.dumps(gene)
            r.mset(genes_data)
            del genes_data

            logger.info("Adding transcripts for gene names...")
            for gene_name, transcript_set in tx_by_gene.items():
                r.sadd(f"transcripts:{gene_name}", *tuple(transcript_set))

            logger.info("Adding transcript interval treees...")
            for contig, iv_tree in tx_intervals.items():
                # Will need to combine interval trees from different imports
                if existing_iv_tree_pickle := r.get(contig):
                    existing_iv_tree = pickle.loads(existing_iv_tree_pickle)
                    iv_tree = iv_tree | existing_iv_tree
                iv_tree_pickle = pickle.dumps(iv_tree)
                r.set(contig, iv_tree_pickle)

            logger.info(f"Finished processing {filename}.")

    logger.info(
        f"All files processed. Processed counts: {', '.join(f'{k}: {v}' for k, v in ANNOTATION_CONSORTIUM_COUNTS.items())}."
    )


if __name__ == "__main__":
    load_cdot_transcript_files()
