from datetime import datetime
import re
import sys
import pywikibot
import logging

from .data.results import Result
from .data.extra_property import ExtraProperty, ExtraQualifier
from .data.smart_precision_time import SmartPrecisionTime

from .constants import Demographics, Genres, site, genre_prop, demographic_prop, start_prop, retrieved_prop, stated_at_prop, url_prop, archive_date_prop, archive_url_prop, official_site_prop, volume_item, num_parts_prop, deprecated_reason_prop, link_rot_item, automated_properties
from .data.reference import Reference
from .pywikibot_stub_types import WikidataReference
from .abc.provider import Provider
from .providers import providers

logger = logging.getLogger(__name__)

def add_or_update_references(provider: Provider, id: str, claim: pywikibot.Claim, new_reference: Reference, automated_hash: str = ""):
    if automated_hash:
        automated_hash_text = f" ([[:toolforge:editgroups/b/CB/{automated_hash}|details]])"
    else:
        automated_hash_text = ""
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
    logger_extra = {"provider": provider.name, "itemId": None}
    logger.info("Adding reference to claim %s: %s", claim.getID(), claim.getTarget(), extra=logger_extra)
    claim.addSources([retrieved_ref, stated_in_ref, url_ref], summary=f"Adding reference for data imported from {provider.name}.{automated_hash_text}")
    
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
        prop.qualifiers[archive_url_prop].append(ExtraQualifier(archive_url, skip_if_conflicting_exists=True))
        archive_date = pywikibot.Claim(site, archive_date_prop)
        archive_date.setTarget(SmartPrecisionTime(year=timestamp.year, month=timestamp.month, day=timestamp.day))
        prop.qualifiers[archive_date_prop].append(ExtraQualifier(archive_date, skip_if_conflicting_exists=True))
        depreicated_reason = pywikibot.Claim(site, deprecated_reason_prop)
        depreicated_reason.setTarget(link_rot_item)
        prop.qualifiers[deprecated_reason_prop].append(ExtraQualifier(depreicated_reason, skip_if_conflicting_exists=True))
    

# Returns bool to signal a re-cycle.
def act_on_property(item: pywikibot.ItemPage, claims: list[pywikibot.Claim], provider: Provider, automated_hash: str = "") -> bool:
    # claims is the claims containing provider IDs.
    re_cycle = False
    logger_extra = {"provider": provider.name, "itemId": item.getID()}
    if automated_hash:
        automated_hash_text = f" ([[:toolforge:editgroups/b/CB/{automated_hash}|details]])"
    else:
        automated_hash_text = ""
    for claim in claims:
        provider_id: str = claim.getTarget() # type: ignore
        try:
            result: Result = provider.get(provider_id, item)
        except Exception as e:
            logger.error("Error while getting data.", extra=logger_extra, exc_info=e)
            return False
        reference = provider.get_reference(provider_id)
        if not automated_hash:
            existing_genres = item.claims.get(genre_prop, [])
            for genre in set(result.genres):
                if not enum_item_in_item_list(genre, existing_genres):
                    # No longer adding genres, only adding refs to existing claims
                    continue
                    # genre_claim = pywikibot.Claim(site, genre_prop)
                    # genre_claim.setTarget(genre.value)
                    # item.addClaim(genre_claim, summary=f"Adding genre from {provider.name}.{automated_hash_text}")
                else:
                    genre_claim = next(filter(lambda x: x.getTarget().id == genre.value.id, existing_genres))
                add_or_update_references(provider, provider_id, genre_claim, reference)
            for demographic in set(result.demographics):
                if not enum_item_in_item_list(demographic, item.claims.get(demographic_prop, [])):
                    demographic_claim = pywikibot.Claim(site, demographic_prop)
                    demographic_claim.setTarget(demographic.value)
                    logger.info("Adding demographic: %s", demographic_claim, extra=logger_extra)
                    item.addClaim(demographic_claim, summary=f"Adding demographic from {provider.name}.{automated_hash_text}")
                else:
                    demographic_claim = next(filter(lambda x: x.getTarget().id == demographic.value.id, item.claims.get(demographic_prop, [])))
                add_or_update_references(provider, provider_id, demographic_claim, reference)
            if result.start_date is not None:
                if isinstance(result.start_date, datetime):
                    time_obj = SmartPrecisionTime(year=result.start_date.year, month=result.start_date.month, day=result.start_date.day)
                else:
                    time_obj = result.start_date
                if start_prop not in item.claims:
                    start_claim = pywikibot.Claim(site, start_prop)
                    start_claim.setTarget(time_obj)
                    logger.info("Adding start date: %s", time_obj.toTimestr(), extra=logger_extra)
                    item.addClaim(start_claim, summary=f"Adding start date from {provider.name}.{automated_hash_text}")
                    add_or_update_references(provider, provider_id, start_claim, reference)
                else:
                    start_claims: list[pywikibot.Claim] = item.claims[start_prop]
                    for start_claim in start_claims:
                        target: pywikibot.WbTime = start_claim.getTarget() # type: ignore
                        if target.year != result.start_date.year:
                            # # We add a duplicate statement and leave it to a human to remove the wrong one.
                            # start_claim = pywikibot.Claim(site, start_prop)
                            # start_claim.setTarget(time_obj)
                            # item.addClaim(start_claim, summary=f"Adding start date from {provider.name}.{automated_hash_text}")
                            # New plan: If we see a conflicting statement trust it.
                            break
                        elif target.year == result.start_date.year and target.precision < time_obj.precision:
                            # We could match month too but it seems redundant at this point.
                            logger.info("Changing start date from %s to %s", target.toTimestr(), time_obj.toTimestr(), extra=logger_extra)
                            start_claim.changeTarget(time_obj, summary=f"Updating start date from {provider.name}.{automated_hash_text}")
                            add_or_update_references(provider, provider_id, start_claim, reference)
            if result.volumes:
                quantity = pywikibot.WbQuantity(result.volumes, volume_item, site=site)
                if num_parts_prop not in item.claims:
                    num_parts_claim = pywikibot.Claim(site, num_parts_prop)
                    num_parts_claim.setTarget(quantity)
                    item.addClaim(num_parts_claim, summary=f"Adding number of volumes from {provider.name}.{automated_hash_text}")
                else:
                    for num_parts_possible_claim in item.claims[num_parts_prop]:
                        if num_parts_possible_claim.getTarget() == quantity:
                            num_parts_claim = num_parts_possible_claim
                            break
                    else:
                        num_parts_claim = pywikibot.Claim(site, num_parts_prop)
                        num_parts_claim.setTarget(quantity)
                        logger.info("Adding number of volumes: %s", quantity, extra=logger_extra)
                        item.addClaim(num_parts_claim, summary=f"Adding number of volumes from {provider.name}.{automated_hash_text}")
                add_or_update_references(provider, provider_id, num_parts_claim, reference)
        for prop, extra_props in result.other_properties.items():
            if automated_hash:
                if prop not in automated_properties:
                    continue
            for extra_prop_data in extra_props:
                if prop == official_site_prop:
                    de_archivify_url_property(extra_prop_data)
                new_claim = extra_prop_data.claim
                if prop not in item.claims:
                    if extra_prop_data.reference_only:
                        continue
                    logger.info("Adding %s: %s", prop, new_claim.getTarget(), extra=logger_extra)
                    item.addClaim(new_claim, summary=f"Adding {new_claim.getID()} from {provider.name}.{automated_hash_text}")
                    if extra_prop_data.re_cycle_able:
                        logger.warning("Re-cycling enabled.", extra=logger_extra)
                        re_cycle = True
                else:
                    for existing_claim in item.claims[prop]:
                        existing_claim: pywikibot.Claim
                        if existing_claim.getTarget() == new_claim.getTarget():
                            new_claim = existing_claim
                            if new_claim.getRank() != existing_claim.getRank():
                                logger.info("Changing rank of [%s: %s] from %s to %s", prop, existing_claim.getTarget(), existing_claim.getRank(), new_claim.getRank(), extra=logger_extra)
                                existing_claim.changeRank(new_claim.getRank())
                            break
                    else:
                        if extra_prop_data.skip_if_conflicting_language_exists and prop in item.claims: # type: ignore
                            for existing_claim in item.claims[prop]: # type: ignore
                                existing_claim: pywikibot.Claim
                                if isinstance(existing_claim.getTarget(), pywikibot.WbMonolingualText):
                                    lang_target: pywikibot.WbMonolingualText = existing_claim.getTarget() # type: ignore
                                    if lang_target.language == new_claim.getTarget().language: # type: ignore
                                        break
                                else:
                                    continue
                            else:
                                if extra_prop_data.reference_only:
                                    continue
                                logger.info("Adding %s: %s", prop, new_claim.getTarget(), extra=logger_extra)
                                item.addClaim(new_claim, summary=f"Adding {new_claim.getID()} from {provider.name}.{automated_hash_text}")
                                if extra_prop_data.re_cycle_able:
                                    logger.warning("Re-cycling enabled.", extra=logger_extra)
                                    re_cycle = True   
                        elif extra_prop_data.skip_if_conflicting_exists:
                            continue
                        try:
                            if extra_prop_data.reference_only:
                                continue
                            logger.info("Adding %s: %s", prop, new_claim.getTarget(), extra=logger_extra)
                            item.addClaim(new_claim, summary=f"Adding {new_claim.getID()} from {provider.name}.{automated_hash_text}")
                        except ValueError:
                            logger.error(f"ERROR: Could not add claim {prop}: {new_claim.getTarget()}.", exc_info=True, extra=logger_extra)
                            sys.exit(1)
                        if extra_prop_data.re_cycle_able:
                            logger.warning("Re-cycling enabled.", extra=logger_extra)
                            re_cycle = True
                for qualifier_prop, qualifiers in extra_prop_data.qualifiers.items():
                    for qualifier_data in qualifiers:
                        qualifier = qualifier_data.claim
                        if qualifier not in new_claim.qualifiers.get(qualifier_prop, []):
                            logger.info("Adding qualifier %s: %s to [%s:, %s]", qualifier_prop, qualifier.getTarget(), prop, new_claim.getTarget(), extra=logger_extra)
                            new_claim.addQualifier(qualifier, summary=f"Adding {qualifier.getID()} to claim with property {prop} from {provider.name}.{automated_hash_text}")
                        else:
                            for existing_qualifier in new_claim.qualifiers[qualifier_prop]:
                                if existing_qualifier.getTarget() == qualifier.getTarget():
                                    break
                            else:
                                if qualifier_data.skip_if_conflicting_exists:
                                    continue
                                logger.info("Adding qualifier %s: %s to [%s:, %s]", qualifier_prop, qualifier.getTarget(), prop, new_claim.getTarget(), extra=logger_extra)
                                new_claim.addQualifier(qualifier, summary=f"Adding {qualifier.getID()} to claim with property {prop} from {provider.name}.{automated_hash_text}")
                for extra_reference in extra_prop_data.extra_references:
                    compatible = False
                    for existing_reference in new_claim.getSources():
                        if extra_reference.is_compatible_reference(existing_reference):
                            compatible = True
                            break
                    if compatible:
                        continue
                    else:
                        logger.info("Adding reference to [%s: %s]", prop, new_claim.getTarget(), extra=logger_extra)
                        new_claim.addSources(list(extra_reference.new_reference_props.values()), summary=f"Adding reference to claim with property {prop} from {provider.name}.{automated_hash_text}")
                add_or_update_references(provider, provider_id, new_claim, reference)
    return re_cycle

def act_on_item(item: pywikibot.ItemPage, automated_hash: str = ""):
    claims = item.claims
    for prop, provider in providers.items():
        if prop in claims:
            if act_on_property(item, claims[prop], provider, automated_hash=automated_hash):
                return act_on_item(item, automated_hash=automated_hash)