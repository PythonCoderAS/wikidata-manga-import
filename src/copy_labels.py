import pywikibot

def copy_labels(from_item: pywikibot.ItemPage, to_item: pywikibot.ItemPage):
    data = from_item.get()
    to_item.editLabels(data["labels"], summary=f"Copy labels from [[{from_item.getID()}]].")
    to_item.editAliases(data["aliases"], summary=f"Copy aliases from [[{from_item.getID()}]].")