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


DATASPACE_SEARCH_ATTRIBUTES: tuple[SearchAttribute, ...] = (
    SearchAttribute("tenant_id", SearchAttributeType.KEYWORD),
    SearchAttribute("legal_entity_id", SearchAttributeType.KEYWORD),
    SearchAttribute("procedure_type", SearchAttributeType.KEYWORD),
    SearchAttribute("external_reference", SearchAttributeType.TEXT),
    SearchAttribute("agreement_id", SearchAttributeType.KEYWORD),
    SearchAttribute("asset_id", SearchAttributeType.KEYWORD),
    SearchAttribute("status", SearchAttributeType.KEYWORD),
    SearchAttribute("pack_id", SearchAttributeType.KEYWORD),
)
