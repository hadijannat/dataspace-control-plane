"""Canonical procedure visibility keys and search-attribute definitions."""
from dataclasses import dataclass
from enum import Enum


class SearchAttributeType(str, Enum):
    TEXT = "Text"
    KEYWORD = "Keyword"
    INT = "Int"
    BOOL = "Bool"
    FLOAT = "Float"
    DATETIME = "Datetime"
    KEYWORD_LIST = "KeywordList"


@dataclass(frozen=True)
class SearchAttribute:
    name: str
    sa_type: SearchAttributeType


TENANT_ID = SearchAttribute("tenant_id", SearchAttributeType.KEYWORD)
LEGAL_ENTITY_ID = SearchAttribute("legal_entity_id", SearchAttributeType.KEYWORD)
PROCEDURE_TYPE = SearchAttribute("procedure_type", SearchAttributeType.KEYWORD)
AGREEMENT_ID = SearchAttribute("agreement_id", SearchAttributeType.KEYWORD)
ASSET_ID = SearchAttribute("asset_id", SearchAttributeType.KEYWORD)
PACK_ID = SearchAttribute("pack_id", SearchAttributeType.KEYWORD)
PACK_IDS = SearchAttribute("pack_ids", SearchAttributeType.KEYWORD_LIST)
TAGS = SearchAttribute("tags", SearchAttributeType.KEYWORD_LIST)
MANUAL_REVIEW_REQUIRED = SearchAttribute("manual_review_required", SearchAttributeType.BOOL)
DUE_AT = SearchAttribute("due_at", SearchAttributeType.DATETIME)
EXPIRES_AT = SearchAttribute("expires_at", SearchAttributeType.DATETIME)
STATUS = SearchAttribute("status", SearchAttributeType.KEYWORD)
EXTERNAL_REFERENCE = SearchAttribute("external_reference", SearchAttributeType.TEXT)


DATASPACE_SEARCH_ATTRIBUTES: tuple[SearchAttribute, ...] = (
    TENANT_ID,
    LEGAL_ENTITY_ID,
    PROCEDURE_TYPE,
    AGREEMENT_ID,
    ASSET_ID,
    PACK_ID,
    PACK_IDS,
    TAGS,
    MANUAL_REVIEW_REQUIRED,
    DUE_AT,
    EXPIRES_AT,
    STATUS,
    EXTERNAL_REFERENCE,
)
