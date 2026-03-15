from __future__ import annotations

from dataspace_control_plane_packs.espr_dpp.delegated_acts import template


def test_delegated_act_template_is_effective_dated() -> None:
    assert template.DELEGATED_ACT_ID == "template"
    assert template.EFFECTIVE_FROM
    assert template.RULES == []
