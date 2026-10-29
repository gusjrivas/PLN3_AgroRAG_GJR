from scripts.run_e2_budgeted import can_start_pair


def test_eva_02_pair_requires_worst_case_reserve_for_both_variants() -> None:
    assert can_start_pair(spent_usd=0.39392, cap_usd=0.50) is True
    assert can_start_pair(spent_usd=0.393921, cap_usd=0.50) is False
