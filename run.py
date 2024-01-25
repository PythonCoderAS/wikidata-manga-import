#!/usr/bin/env python3
import argparse
from typing import Union

import pywikibot
from pywikibot.pagegenerators import WikidataSPARQLPageGenerator
from wikidata_bot_framework import get_random_hex

from src.constants import automated_scan_properties, session, site
from src.copy_labels import copy_labels
from src.main import MangaImportBot

parser = argparse.ArgumentParser("wikidata-manga-import")
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
    bot: MangaImportBot,
    item_string: str,
    copy_from_item_string: Union[str, None] = None,
):
    item = pywikibot.ItemPage(site, item_string)
    bot.act_on_item(item)
    if copy_from_item_string:
        copy_from_item = pywikibot.ItemPage(site, copy_from_item_string)
        copy_labels(copy_from_item, item)


def main(argv=None):
    bot = MangaImportBot()
    args = parser.parse_args(argv)
    if args.automatic:
        bot.set_hash(get_random_hex())
        if args.input_file is not None or args.item is not None:
            pass
        elif args.copy_from is not None:
            parser.error("Automatic mode cannot be used with copy-from.")
        else:
            props_sparql = " UNION ".join(
                [
                    "{ ?item p:%s ?_. }" % property
                    for property in automated_scan_properties
                ]
            )
            complete_sparql = "SELECT DISTINCT ?item WHERE { %s }" % props_sparql
            items = sorted(
                [
                    item
                    for item in WikidataSPARQLPageGenerator(complete_sparql, site=site)
                ],
                key=lambda item: item.getID(numeric=True),
                reverse=True,
            )
            for item in items:
                bot.act_on_item(item)
                session.remove_expired_responses()

    if args.input_file is None and args.item is None:
        parser.error("You must specify either an input file or an item.")
    if args.input_file is not None and args.item is not None:
        parser.error("You must specify either an input file or an item, not both.")
    if args.input_file is not None:
        if args.copy_from is not None:
            parser.error("You cannot specify both an input file and a copy-from item.")
        with open(args.input_file, "r") as f:
            for line in f:
                act_on_item_string(bot, line.strip())
    else:
        act_on_item_string(
            bot,
            args.item.strip(),
            copy_from_item_string=args.copy_from,
        )


if __name__ == "__main__":
    main()
