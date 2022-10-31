#!/usr/bin/env python3
import argparse
import pywikibot

from src.constants import site
from src.main import act_on_item
from src.copy_labels import copy_labels

parser = argparse.ArgumentParser("wikidata-anime-import")
parser.add_argument("-f", "--input-file", type=str, help="The file of items to read from.")
parser.add_argument("-i", "--item", type=str, help="The item to import data for.")
parser.add_argument("--copy-from", type=str, help="The item to copy labels from.")

def act_on_item_string(item_string: str, copy_from_item_string: str | None = None):
    item = pywikibot.ItemPage(site, item_string)
    act_on_item(item)
    if copy_from_item_string:
        copy_from_item = pywikibot.ItemPage(site, copy_from_item_string)
        copy_labels(copy_from_item, item)

def main(argv=None):
    args = parser.parse_args(argv)
    if args.input_file is None and args.item is None:
        parser.error("You must specify either an input file or an item.")
    if args.input_file is not None and args.item is not None:
        parser.error("You must specify either an input file or an item, not both.")
    if args.input_file is not None:
        with open(args.input_file, "r") as f:
            for line in f:
                act_on_item_string(line.strip())
    else:
        act_on_item_string(args.item.strip(), copy_from_item_string=args.copy_from)

if __name__ == "__main__":
    main()
