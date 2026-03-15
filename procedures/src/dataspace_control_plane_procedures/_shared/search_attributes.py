from typing import Any, Mapping

from temporalio.common import SearchAttributeKey, SearchAttributeUpdate

TENANT_ID = SearchAttributeKey.for_keyword("tenant_id")
LEGAL_ENTITY_ID = SearchAttributeKey.for_keyword("legal_entity_id")
PROCEDURE_TYPE = SearchAttributeKey.for_keyword("procedure_type")
EXTERNAL_REFERENCE = SearchAttributeKey.for_keyword("external_reference")
AGREEMENT_ID = SearchAttributeKey.for_keyword("agreement_id")
ASSET_ID = SearchAttributeKey.for_keyword("asset_id")
STATUS = SearchAttributeKey.for_keyword("status")
PACK_ID = SearchAttributeKey.for_keyword("pack_id")

ALL_SA_KEYS: tuple[SearchAttributeKey, ...] = (
    TENANT_ID, LEGAL_ENTITY_ID, PROCEDURE_TYPE, EXTERNAL_REFERENCE,
    AGREEMENT_ID, ASSET_ID, STATUS, PACK_ID,
)


def build_search_attribute_updates(
    values: Mapping[SearchAttributeKey, Any | None],
) -> list[SearchAttributeUpdate]:
    updates: list[SearchAttributeUpdate] = []
    for key, value in values.items():
        if value is None:
            updates.append(key.value_unset())
        else:
            updates.append(key.value_set(value))
    return updates
