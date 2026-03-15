from temporalio.common import SearchAttributeKey

TENANT_ID = SearchAttributeKey.for_keyword("tenant_id")
LEGAL_ENTITY_ID = SearchAttributeKey.for_keyword("legal_entity_id")
PROCEDURE_TYPE = SearchAttributeKey.for_keyword("procedure_type")
EXTERNAL_REFERENCE = SearchAttributeKey.for_text("external_reference")
AGREEMENT_ID = SearchAttributeKey.for_keyword("agreement_id")
ASSET_ID = SearchAttributeKey.for_keyword("asset_id")
STATUS = SearchAttributeKey.for_keyword("status")
PACK_ID = SearchAttributeKey.for_keyword("pack_id")

ALL_SA_KEYS: tuple[SearchAttributeKey, ...] = (
    TENANT_ID, LEGAL_ENTITY_ID, PROCEDURE_TYPE, EXTERNAL_REFERENCE,
    AGREEMENT_ID, ASSET_ID, STATUS, PACK_ID,
)
