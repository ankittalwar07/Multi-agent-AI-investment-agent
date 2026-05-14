from investment_agent.scoring.moat_rubric import score_company


def test_sole_source_requires_two_citations():
    s = score_company(
        single_source=True,
        independent_citations_for_sole_source=1,
        market_share_bucket=None,
        moat_types=[],
        switching_costs=None,
        demand_signal=None,
    )
    assert s.sole_source_pts == 0
    assert "insufficient" in s.rationale.lower()


def test_sole_source_credited_with_two_citations():
    s = score_company(
        single_source=True,
        independent_citations_for_sole_source=2,
        market_share_bucket="sole",
        moat_types=["ip", "regulatory"],
        switching_costs="very high lock-in",
        demand_signal="exponential growth, backlog",
    )
    assert s.sole_source_pts == 30
    assert s.share_pts == 25
    assert s.ip_pts == 15
    assert s.regulatory_pts == 10
    assert s.switching_pts == 10
    assert s.demand_pts == 10
    assert s.composite == 100


def test_low_score_company():
    s = score_company(
        single_source=False,
        independent_citations_for_sole_source=0,
        market_share_bucket="<10",
        moat_types=[],
        switching_costs=None,
        demand_signal=None,
    )
    assert s.composite == 0
