from unittest.mock import patch

from src.qualifier import (
    AILeadInsights,
    LeadInput,
    is_corporate_email,
    qualify_lead,
    qualify_lead_deterministic,
)


def test_corporate_email_detection() -> None:
    assert is_corporate_email("ana@acmeautomacoes.com.br") is True
    assert is_corporate_email("joao@gmail.com") is False
    assert is_corporate_email("maria@outlook.com") is False
    assert is_corporate_email(None) is False
    assert is_corporate_email("invalid-email") is False


def test_qualify_hot_lead() -> None:
    lead = LeadInput(
        id="00Q000000000001AAA",
        name="Ana Silva",
        company="Acme Automations",
        email="ana@acmeautomations.com",
        description="We need urgent API integration and workflow automation for our team.",
    )

    result = qualify_lead_deterministic(lead)

    assert result.lead_id == "00Q000000000001AAA"
    assert result.is_corporate_email is True
    assert result.score >= 70
    assert result.rating == "Hot"


def test_qualify_cold_lead() -> None:
    lead = LeadInput(
        id="00Q000000000002AAA",
        name="John Doe",
        company=None,
        email="john@gmail.com",
        description="Hi",
    )

    result = qualify_lead_deterministic(lead)

    assert result.is_corporate_email is False
    assert result.score < 45
    assert result.rating == "Cold"


def test_qualify_warm_lead() -> None:
    lead = LeadInput(
        id="00Q000000000003AAA",
        name="Lucas Costa",
        company="Costa Retail",
        email="lucas@gmail.com",
        description="Looking for basic info about your product.",
    )

    result = qualify_lead_deterministic(lead)

    assert result.is_corporate_email is False
    assert 45 <= result.score < 70
    assert result.rating == "Warm"


@patch("src.qualifier.analyze_with_gemini")
def test_qualify_lead_with_ai_enrichment(mock_gemini) -> None:
    mock_gemini.return_value = AILeadInsights(
        score_delta=20,
        pain_point="Manual sales pipeline bottlenecks",
        urgency="High",
        executive_summary="High-fit B2B prospect looking to automate CRM workflows urgently.",
    )

    lead = LeadInput(
        id="00Q000000000004AAA",
        name="Carlos Mendes",
        company="Mendes Logistica",
        email="carlos@mendeslogistica.com.br",
        description="We want to migrate our manual sales process before quarter end.",
    )

    result = qualify_lead(lead, use_ai=True)

    assert result.score == 95
    assert result.rating == "Hot"
    assert result.ai_insights is not None
    assert "[AI Insights]" in result.summary


@patch("src.qualifier.analyze_with_gemini", return_value=None)
def test_qualify_lead_ai_fallback(mock_gemini) -> None:
    lead = LeadInput(
        id="00Q000000000005AAA",
        name="Lucas Costa",
        company="Costa Retail",
        email="lucas@gmail.com",
        description="Looking for basic info about your product.",
    )

    result = qualify_lead(lead, use_ai=True)

    assert result.ai_insights is None
    assert result.rating == "Warm"
