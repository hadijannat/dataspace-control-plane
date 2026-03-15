from enum import Enum

class PolicySetStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"
    NEEDS_REVIEW = "needs_review"

class ParseOutcome(str, Enum):
    CLEAN = "clean"
    LOSSY = "lossy"
    FAILED = "failed"
