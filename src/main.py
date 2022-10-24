from datetime import datetime
import re
import pywikibot

from .data.extra_property import ExtraProperty, ExtraQualifier
from .data.smart_precision_time import SmartPrecisionTime

from .constants import Demographics, Genres, site, genre_prop, demographic_prop, start_prop, retrieved_prop, stated_at_prop, url_prop, archive_date_prop, archive_url_prop, official_site_prop, volume_item, num_parts_prop
from .data.reference import Reference
from .pywikibot_stub_types import WikidataReference
from .abc.provider import Provider
from .providers import providers

def add_or_update_references(provider: Provider, id: str, claim: pywikibot.Claim, new_reference: Reference):
    for source in claim.getSources():
        source: WikidataReference
        if provider.compute_similar_reference(source, id):
            return
    retrieved_ref = pywikibot.Claim(site, retrieved_prop, is_reference=True)
    retrieved_ref.setTarget(SmartPrecisionTime(year=new_reference.retrieved.year, month=new_reference.retrieved.month, day=new_reference.retrieved.day))
    stated_in_ref = pywikibot.Claim(site, stated_at_prop, is_reference=True)
    stated_in_ref.setTarget(new_reference.stated_in)
    url_ref = pywikibot.Claim(site, url_prop, is_reference=True)
    url_ref.setTarget(new_reference.url)
    claim.addSources([retrieved_ref, stated_in_ref, url_ref], summary=f"Adding reference for data imported from {provider.name}.")
    
def enum_item_in_item_list(item: Genres | Demographics, existing_item_list: list[pywikibot.Claim]) -> bool:
    for existing_item in existing_item_list:
        if existing_item.getTarget().id == item.value.id: # type: ignore
            return True
    return False

def de_archivify_url_property(prop: ExtraProperty):
    full_url = str(prop.claim.getTarget())
    if match := re.search(r"web.archive.org/web/(\d{14})/", full_url):
        prop.claim.setTarget(full_url.replace(match.group(0), ""))
        prop.claim.setRank("deprecated")
        timestamp = datetime.strptime(match.group(1), "%Y%m%d%H%M%S")
        archive_url = pywikibot.Claim(site, archive_url_prop)
        archive_url.setTarget(full_url)
        prop.qualifiers[archive_url_prop].append(ExtraQualifier(archive_url, skip_if_any_exists=True))
        archive_date = pywikibot.Claim(site, archive_date_prop)
        archive_date.setTarget(SmartPrecisionTime(year=timestamp.year, month=timestamp.month, day=timestamp.day))
        prop.qualifiers[archive_date_prop].append(ExtraQualifier(archive_date, skip_if_any_exists=True))
    

# Returns bool to signal a re-cycle.
def act_on_property(item: pywikibot.ItemPage, claims: list[pywikibot.Claim], provider: Provider) -> bool:
    # claims is the claims containing provider IDs.
    re_cycle = False
    for claim in claims:
        provider_id: str = claim.getTarget() # type: ignore
        result = provider.get(provider_id, item)
        reference = provider.get_reference(provider_id)
        # existing_genres = item.claims.get(genre_prop, [])
        # for genre in set(result.genres):
        #     if not enum_item_in_item_list(genre, existing_genres):
        #         genre_claim = pywikibot.Claim(site, genre_prop)
        #         genre_claim.setTarget(genre.value)
        #         item.addClaim(genre_claim, summary=f"Adding genre from {provider.name}.")
        #     else:
        #         genre_claim = next(filter(lambda x: x.getTarget().id == genre.value.id, existing_genres))
        #     add_or_update_references(provider, provider_id, genre_claim, reference)
        for demographic in set(result.demographics):
            if not enum_item_in_item_list(demographic, item.claims.get(demographic_prop, [])):
                demographic_claim = pywikibot.Claim(site, demographic_prop)
                demographic_claim.setTarget(demographic.value)
                item.addClaim(demographic_claim, summary=f"Adding demographic from {provider.name}.")
            else:
                demographic_claim = next(filter(lambda x: x.getTarget().id == demographic.value.id, item.claims.get(demographic_prop, [])))
            add_or_update_references(provider, provider_id, demographic_claim, reference)
        if result.start_date is not None:
            time_obj = SmartPrecisionTime(year=result.start_date.year, month=result.start_date.month, day=result.start_date.day)
            if start_prop not in item.claims:
                start_claim = pywikibot.Claim(site, start_prop)
                start_claim.setTarget(time_obj)
                item.addClaim(start_claim, summary=f"Adding start date from {provider.name}.")
            else:
                start_claim: pywikibot.Claim = item.claims[start_prop][0]
                target: pywikibot.WbTime = start_claim.getTarget() # type: ignore
                if target.year != result.start_date.year:
                    # We add a duplicate statement and leave it to a human to remove the wrong one.
                    start_claim = pywikibot.Claim(site, start_prop)
                    start_claim.setTarget(time_obj)
                    item.addClaim(start_claim, summary=f"Adding start date from {provider.name}.")
                elif target.year == result.start_date.year and target.precision < time_obj.precision:
                    # We could match month too but it seems redundant at this point.
                    start_claim.changeTarget(time_obj, summary=f"Updating start date from {provider.name}.")
            add_or_update_references(provider, provider_id, start_claim, reference)
        if result.volumes:
            quantity = pywikibot.WbQuantity(result.volumes, volume_item, site=site)
            if num_parts_prop not in item.claims:
                num_parts_claim = pywikibot.Claim(site, num_parts_prop)
                num_parts_claim.setTarget(quantity)
                item.addClaim(num_parts_claim, summary=f"Adding number of volumes from {provider.name}.")
            else:
                for num_parts_possible_claim in item.claims[num_parts_prop]:
                    if num_parts_possible_claim.getTarget() == quantity:
                        num_parts_claim = num_parts_possible_claim
                        break
                else:
                    num_parts_claim = pywikibot.Claim(site, num_parts_prop)
                    num_parts_claim.setTarget(quantity)
                    item.addClaim(num_parts_claim, summary=f"Adding number of volumes from {provider.name}.")
            add_or_update_references(provider, provider_id, num_parts_claim, reference)
        for prop, extra_props in result.other_properties.items():
            for extra_prop_data in extra_props:
                if prop == official_site_prop:
                    de_archivify_url_property(extra_prop_data)
                new_claim = extra_prop_data.claim
                if prop not in item.claims:
                    item.addClaim(new_claim, summary=f"Adding {new_claim.getID()} from {provider.name}.")
                    if extra_prop_data.re_cycle_able:
                        re_cycle = True
                elif extra_prop_data.skip_if_any_exists:
                    continue
                else:
                    for existing_claim in item.claims[prop]:
                        if existing_claim.getTarget() == new_claim.getTarget():
                            new_claim = existing_claim
                            if new_claim.getRank() != existing_claim.getRank():
                                existing_claim.changeRank(new_claim.getRank())
                            break
                    else:
                        item.addClaim(new_claim, summary=f"Adding {new_claim.getID()} from {provider.name}.")
                        if extra_prop_data.re_cycle_able:
                            re_cycle = True
                for qualifier_prop, qualifiers in extra_prop_data.qualifiers.items():
                    for qualifier_data in qualifiers:
                        qualifier = qualifier_data.claim
                        if qualifier not in new_claim.qualifiers.get(qualifier_prop, []):
                            new_claim.addQualifier(qualifier, summary=f"Adding {qualifier.getID()} to claim with property {prop} from {provider.name}.")
                        elif qualifier_data.skip_if_any_exists:
                                continue
                        else:
                            for existing_qualifier in new_claim.qualifiers[qualifier_prop]:
                                if existing_qualifier.getTarget() == qualifier.getTarget():
                                    break
                            else:
                                new_claim.addQualifier(qualifier, summary=f"Adding {qualifier.getID()} to claim with property {prop} from {provider.name}.")
                add_or_update_references(provider, provider_id, new_claim, reference)
    return re_cycle

def act_on_item(item: pywikibot.ItemPage):
    claims = item.claims
    for prop, provider in providers.items():
        if prop in claims:
            if act_on_property(item, claims[prop], provider):
                return act_on_item(item)