from __future__ import annotations

from dataspace_control_plane_packs._shared.provenance import PROVENANCE_KEY
from dataspace_control_plane_packs.catenax.credential_profiles import CatenaxCredentialProfileProvider
from dataspace_control_plane_packs.catenax.evidence import CatenaxEvidenceAugmenter
from dataspace_control_plane_packs.catenax.policy_profile.compiler import CatenaxPolicyDialectProvider
from dataspace_control_plane_packs.catenax.policy_profile.parser import parse_cx_policy


def test_compile_preserves_review_flags_and_adds_provenance() -> None:
    compiled = CatenaxPolicyDialectProvider().compile(
        {
            "permissions": [
                {
                    "action": "use",
                    "target": "urn:asset:1",
                    "purposes": [
                        "cx-policy:UsagePurpose.core.traceability.dataProvision"
                    ],
                    "unsupported_constraints": [
                        {
                            "odrl:leftOperand": "cx-policy:UnknownOperand",
                            "odrl:rightOperand": "value",
                        }
                    ],
                }
            ]
        },
        activation_scope="tenant:acme",
    )

    assert compiled["review_flags"]
    assert compiled[PROVENANCE_KEY]["records"]["catenax"]["activation_scope"] == "tenant:acme"
    # Unsupported constraints must NOT appear in compiled ODRL output — they
    # are quarantined in review_flags only, never forwarded to ODRL evaluators.
    constraints = compiled["odrl:permission"][0].get("odrl:constraint", [])
    assert not any(
        c.get("odrl:leftOperand") == "cx-policy:UnknownOperand"
        for c in constraints
    )


def test_parse_preserves_unsupported_constraints_for_review() -> None:
    parsed = CatenaxPolicyDialectProvider().parse(
        {
            "odrl:permission": [
                {
                    "odrl:constraint": [
                        {
                            "odrl:leftOperand": "cx-policy:UsagePurpose",
                            "odrl:rightOperand": "cx-policy:UsagePurpose.core.traceability.dataProvision",
                        },
                        {
                            "odrl:leftOperand": "cx-policy:UnknownOperand",
                            "odrl:rightOperand": "value",
                        },
                    ]
                }
            ]
        }
    )

    permission = parsed["permissions"][0]
    assert permission["purposes"] == [
        "cx-policy:UsagePurpose.core.traceability.dataProvision"
    ]
    assert permission["unsupported_constraints"][0]["odrl:leftOperand"] == "cx-policy:UnknownOperand"
    assert parsed["review_flags"]


def test_catenax_outputs_carry_pack_provenance() -> None:
    evidence = CatenaxEvidenceAugmenter().augment(
        {
            "bpnl": "BPNL000000000001",
            "policy_purposes": ["cx-policy:UsagePurpose.core.traceability.dataProvision"],
        },
        activation_scope="tenant:acme",
    )
    vc_payload = CatenaxCredentialProfileProvider().build_vc_payload(
        "BpnCredential",
        {"bpnl": "BPNL000000000001", "bpns": "BPNS000000000001"},
        activation_scope="tenant:acme",
    )

    assert evidence[PROVENANCE_KEY]["records"]["catenax"]["pack_version"] == "4.0.0"
    assert vc_payload[PROVENANCE_KEY]["records"]["catenax"]["pack_version"] == "4.0.0"


# ---------------------------------------------------------------------------
# parse_cx_policy — boundary conditions and error paths
# ---------------------------------------------------------------------------

def test_parse_cx_policy_empty_policy_returns_empty_permissions() -> None:
    parsed = parse_cx_policy({})
    assert parsed["permissions"] == []
    assert parsed["prohibitions"] == []
    assert parsed["obligations"] == []
    assert parsed["purposes"] == []
    assert parsed["review_flags"] == []


def test_parse_cx_policy_single_permission_object_not_list() -> None:
    """odrl:permission may be a single dict rather than a list — must normalise."""
    parsed = parse_cx_policy(
        {
            "odrl:permission": {
                "odrl:constraint": [
                    {
                        "odrl:leftOperand": "cx-policy:UsagePurpose",
                        "odrl:rightOperand": "cx-policy:UsagePurpose.core.traceability.dataProvision",
                    }
                ]
            }
        }
    )
    assert len(parsed["permissions"]) == 1
    assert parsed["purposes"] == [
        "cx-policy:UsagePurpose.core.traceability.dataProvision"
    ]


def test_parse_cx_policy_malformed_usage_purpose_right_operand_triggers_review_flag() -> None:
    """If UsagePurpose rightOperand is not a string, emit an unsupported constraint + review flag."""
    parsed = parse_cx_policy(
        {
            "odrl:permission": [
                {
                    "odrl:constraint": [
                        {
                            "odrl:leftOperand": "cx-policy:UsagePurpose",
                            "odrl:rightOperand": {"@id": "not-a-string"},  # malformed
                        }
                    ]
                }
            ]
        }
    )
    assert parsed["review_flags"], "Expected review flags for malformed UsagePurpose right operand"
    assert parsed["unsupported_constraints"], "Malformed constraint should be in unsupported list"


def test_parse_cx_policy_non_cx_constraints_pass_through_unmodified() -> None:
    """Standard ODRL constraints without cx-policy: prefix must not be flagged."""
    non_cx_constraint = {
        "odrl:leftOperand": "odrl:dateTime",
        "odrl:operator": {"@id": "odrl:lt"},
        "odrl:rightOperand": "2030-01-01",
    }
    parsed = parse_cx_policy(
        {
            "odrl:permission": [
                {"odrl:constraint": [non_cx_constraint]}
            ]
        }
    )
    perm = parsed["permissions"][0]
    # Non-cx constraint must appear in odrl:constraint, not in unsupported_constraints
    assert non_cx_constraint in perm.get("odrl:constraint", [])
    assert parsed["review_flags"] == []


def test_parse_cx_policy_output_carries_provenance() -> None:
    parsed = parse_cx_policy({})
    assert PROVENANCE_KEY in parsed
    records = parsed[PROVENANCE_KEY]["records"]
    assert "catenax" in records
