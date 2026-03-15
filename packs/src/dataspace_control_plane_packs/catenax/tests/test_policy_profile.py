from __future__ import annotations

from dataspace_control_plane_packs._shared.provenance import PROVENANCE_KEY
from dataspace_control_plane_packs.catenax.credential_profiles import CatenaxCredentialProfileProvider
from dataspace_control_plane_packs.catenax.evidence import CatenaxEvidenceAugmenter
from dataspace_control_plane_packs.catenax.policy_profile.compiler import CatenaxPolicyDialectProvider


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
    assert any(
        constraint["odrl:leftOperand"] == "cx-policy:UnknownOperand"
        for constraint in compiled["odrl:permission"][0]["odrl:constraint"]
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
