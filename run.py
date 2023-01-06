#!/usr/bin/env python3
import argparse
import logging
import os
import random
from typing import Union

import pywikibot
from pywikibot.pagegenerators import WikidataSPARQLPageGenerator

from src import CustomFormatter
from src.constants import automated_scan_properties, session, site
from src.copy_labels import copy_labels
from src.main import act_on_item

parser = argparse.ArgumentParser("wikidata-anime-import")
parser.add_argument(
    "-a",
    "--automatic",
    action="store_true",
    help="Ruins in automatic mode, meaning it will only apply properties in src.constants.automated_properties.",
)
parser.add_argument(
    "-f", "--input-file", type=str, help="The file of items to read from."
)
parser.add_argument("-i", "--item", type=str, help="The item to import data for.")
parser.add_argument("--copy-from", type=str, help="The item to copy labels from.")


def act_on_item_string(
    item_string: str,
    copy_from_item_string: Union[str, None] = None,
    automated_hash: str = "",
):
    item = pywikibot.ItemPage(site, item_string)
    act_on_item(item, automated_hash=automated_hash)
    if copy_from_item_string:
        copy_from_item = pywikibot.ItemPage(site, copy_from_item_string)
        copy_labels(copy_from_item, item)


def main(argv=None):
    automated_hash = ""
    args = parser.parse_args(argv)
    if args.automatic:
        automated_hash = "{:x}".format(random.randrange(0, 2**48))
        if args.input_file is not None or args.item is not None:
            pass
        elif args.copy_from is not None:
            parser.error("Automatic mode cannot be used with copy-from.")
        else:
            # We need to reconfigure logging to write to a file.
            logger = logging.getLogger("src")
            os.makedirs("logs", exist_ok=True)
            handler = logging.FileHandler("logs/automatic.log", mode="a")
            handler.setFormatter(logging.Formatter(CustomFormatter.format_str))
            handler.setLevel(logging.INFO)
            logger.removeHandler(logger.handlers[0])
            logger.addHandler(handler)
            from automatic_ids import (
                add_ids,
                get_ids,
                init_db,
                mark_completed,
                reset_db,
            )

            init_db()
            ids = get_ids()
            if not ids:
                props_sparql = " UNION ".join(
                    [
                        "{ ?item p:%s ?_. }" % property
                        for property in automated_scan_properties
                    ]
                )
                complete_sparql = "SELECT DISTINCT ?item WHERE { %s }" % props_sparql
                items = [
                    item
                    for item in WikidataSPARQLPageGenerator(complete_sparql, site=site)
                ]
                add_ids(item.id for item in items)
            else:
                items = [pywikibot.ItemPage(site, f"Q{id}") for id in ids]
            for item in items:
                act_on_item(item, automated_hash=automated_hash)
                session.remove_expired_responses()
                mark_completed(item.id)
            else:
                reset_db()
            return

    if args.input_file is None and args.item is None:
        parser.error("You must specify either an input file or an item.")
    if args.input_file is not None and args.item is not None:
        parser.error("You must specify either an input file or an item, not both.")
    if args.input_file is not None:
        if args.copy_from is not None:
            parser.error("You cannot specify both an input file and a copy-from item.")
        with open(args.input_file, "r") as f:
            for line in f:
                act_on_item_string(line.strip(), automated_hash=automated_hash)
    else:
        act_on_item_string(
            args.item.strip(),
            copy_from_item_string=args.copy_from,
            automated_hash=automated_hash,
        )


if __name__ == "__main__":
    main()
