import os
import re

import click
import requests

from cdot.data_release import get_latest_data_release

# One file per annotation consortium, holding every genome build's alignment in each transcript record.
# The per-build files repeat a transcript once per build, and loading them in turn would keep only the
# last build's record while the earlier build's interval tree still lists the transcript.
ALL_BUILDS_FILE = re.compile(r"cdot-\d+\.\d+\.\d+\.all-builds-(ensembl|refseq)-.+\.json\.gz")


@click.command()
@click.option(
    "--output-dir",
    default=".",
    show_default=True,
    help="Directory to save downloaded files.",
)
def download_latest_cdot_transcript_files(output_dir):
    """Download the latest cdot all-builds transcript files for RefSeq and Ensembl."""
    release = get_latest_data_release()
    if not release:
        raise click.ClickException("No cdot data release found.")

    download_urls = [
        asset["browser_download_url"] for asset in release["assets"] if ALL_BUILDS_FILE.fullmatch(asset["name"])
    ]
    if len(download_urls) != 2:
        raise click.ClickException(
            f"Expected 2 all-builds files in {release['tag_name']}, found {len(download_urls)}."
        )

    os.makedirs(output_dir, exist_ok=True)
    for url in download_urls:
        filename = os.path.join(output_dir, os.path.basename(url))
        click.echo(f"Downloading {url} to {filename}...")

        response = requests.get(url)
        response.raise_for_status()
        with open(filename, "wb") as f:
            f.write(response.content)

        click.echo(f"Saved {filename}")


if __name__ == "__main__":
    download_latest_cdot_transcript_files()
