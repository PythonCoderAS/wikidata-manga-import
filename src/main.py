import re
import sys
import time
from datetime import datetime
from functools import partial
from typing import Union

import pywikibot
from wikidata_bot_framework import (
    Config,
    EntityPage,
    Output,
    OutputHelper,
    PropertyAdderBot,
    report_exception,
    start_span,
)

from .abc.provider import Provider
from .constants import (
    Demographics,
    Genres,
    archive_date_prop,
    archive_url_prop,
    automated_create_properties,
    deprecated_reason_prop,
    kitsu_prop,
    link_rot_item,
    retrieved_prop,
    site,
    stated_at_prop,
    url_prop,
    url_properties,
)
from .data.extra_property import ExtraProperty, ExtraQualifier, ExtraReference
from .data.provider_results import ProviderResults
from .data.reference import Reference
from .data.results import Result
from .providers import providers
from .pywikibot_stub_types import WikidataReference


class MangaImportBot(PropertyAdderBot):
    def __init__(self):
        super().__init__()
        self.automated_hash = None
        self.set_config(Config(create_or_edit_main_property_whitelist_enabled=True))

    def set_hash(self, hash: Union[str, None]):
        self.automated_hash = hash

    def get_edit_group_id(self) -> Union[str, None]:
        return self.automated_hash

    def get_edit_summary(self, page: EntityPage) -> str:
        return "Adding imported data from found providers ([[User:RPI2026F1Bot/Task1|info]])"

    def make_reference(
        self, provider: Provider, provider_id: str, reference: Reference
    ) -> ExtraReference:
        ref = ExtraReference()
        ref.is_compatible_reference = partial(provider.compute_similar_reference, id=provider_id)  # type: ignore
        stated_in_ref = pywikibot.Claim(site, stated_at_prop, is_reference=True)
        stated_in_ref.setTarget(reference.stated_in)
        ref.add_claim(stated_in_ref)
        url_ref = pywikibot.Claim(site, url_prop, is_reference=True)
        url_ref.setTarget(reference.url)
        ref.add_claim(url_ref)
        id_ref = pywikibot.Claim(site, provider.prop, is_reference=True)
        id_ref.setTarget(provider_id)
        ref.add_claim(id_ref)
        return ref

    def run_item(self, item: EntityPage) -> OutputHelper:
        oh = OutputHelper()
        for provider_property, provider in providers.items():
            if provider_property not in item.claims:
                continue
            with start_span(
                op="provider_values",
                description=f"Getting al data from provider {provider.name}",
            ):
                for value in item.claims[provider_property]:
                    if value.getRank() == "deprecated":
                        continue
                    provider_id = value.getTarget()
                    with start_span(
                        op="provider_value",
                        description=f"Getting data from provider {provider.name} for ID {provider_id}",
                    ):
                        try:
                            result: Result = provider.get(provider_id, item)
                        except Exception as e:
                            report_exception(e)
                            continue
                        result.simplify()
                        reference = provider.get_reference(provider_id)
                        for extra_properties in result.other_properties.values():
                            for extra_property in extra_properties:
                                extra_property.add_reference(
                                    self.make_reference(
                                        provider, provider_id, reference
                                    )
                                )
                        oh.update(result.other_properties)
        return oh

    def whitelisted_claim(self, prop: ExtraProperty) -> bool:
        if not self.automated_hash:
            return True
        if prop.claim.getID() in automated_create_properties["*"]:
            return True
        for provider_prop in providers.values():
            for ref in prop.extra_references:
                if provider_prop in ref.new_reference_props:
                    return prop.claim.getID() in automated_create_properties.get(
                        provider_prop.prop, set()
                    )
        return False

    def post_output_process_hook(self, output: Output, item: EntityPage) -> bool:
        edits_made = False
        for provider in providers.values():
            with start_span(
                op="provider_post_process",
                description=f"Running post-process hook for provider {provider.name}",
            ):
                edits_made |= provider.post_process_hook(output, item)
        return edits_made

    def act_on_item(self, item: EntityPage) -> bool:
        edits_made = False
        while super().act_on_item(item):
            edits_made = True
            item.get(force=True)
        return edits_made
