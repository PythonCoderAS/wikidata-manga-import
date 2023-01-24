from wikidata_bot_framework import EntityPage


def copy_labels(from_item: EntityPage, to_item: EntityPage):
    data = from_item.get()
    to_item.editLabels(
        data["labels"], summary=f"Copy labels from [[{from_item.getID()}]].", bot=True
    )
    to_item.editAliases(
        data["aliases"], summary=f"Copy aliases from [[{from_item.getID()}]].", bot=True
    )
