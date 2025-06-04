import os
import requests

import click

from cdot.data_release import get_latest_data_release, get_latest_combo_file_urls


@click.command()
@click.option(
    "--output-dir",
    default=".",
    show_default=True,
    help="Directory to save downloaded files.",
)
def download_latest_cdot_transcript_files(output_dir):
    """Download latest CDOT transcript files for specified sources and genomes."""
    release = get_latest_data_release()
    os.makedirs(output_dir, exist_ok=True)

    if not release:
        click.echo("No files found for the specified sources and genomes.")
        return

    download_urls = [asset["browser_download_url"] for asset in release.get("assets", []) if asset["browser_download_url"].endswith(".json.gz")]
    download_urls = get_latest_combo_file_urls(["refseq", "ensembl"], ["grch38", "grch37"])

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
