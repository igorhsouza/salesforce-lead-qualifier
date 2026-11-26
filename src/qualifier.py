import logging
from typing import Literal

from google import genai
from google.genai import types
from pydantic import BaseModel, Field

from src.config import settings

logger = logging.getLogger("lead_qualifier")

FREE_EMAIL_DOMAINS = {
    "gmail.com",
    "googlemail.com",
    "hotmail.com",
    "outlook.com",
    "live.com",
    "yahoo.com",
    "icloud.com",
    "bol.com.br",
    "uol.com.br",
}

HIGH_INTENT_KEYWORDS = {
    "api",
    "automation",
    "automacao",
    "automação",
    "integration",
    "integracao",
    "integração",
    "erp",
    "crm",
    "webhook",
    "urgent",
    "urgente",
    "budget",
    "orcamento",
    "orçamento",
    "contract",
    "contrato",
    "enterprise",
    "team",
    "equipe",
}


class LeadInput(BaseModel):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    company: str | None = None
    email: str | None = None
    description: str | None = None


class AILeadInsights(BaseModel):
    score_delta: int = Field(
        ge=-15,
        le=20,
        description="Score adjustment from -15 to +20 based on buying intent, email domain legitimacy, and context.",
    )
    pain_point: str = Field(
        description="Core business problem, technical need, or company profile identified."
    )
    urgency: Literal["High", "Medium", "Low"]
    executive_summary: str = Field(
        description="One-sentence English summary for the sales rep."
    )


class LeadQualification(BaseModel):
    lead_id: str
    score: int = Field(ge=0, le=100)
    rating: Literal["Hot", "Warm", "Cold"]
    is_corporate_email: bool
    reasons: list[str]
    ai_insights: AILeadInsights | None = None
    summary: str


def is_corporate_email(email: str | None) -> bool:
    if not email or "@" not in email:
        return False
    domain = email.strip().lower().split("@", 1)[1]
    return domain not in FREE_EMAIL_DOMAINS and "." in domain


def _score_to_rating(score: int) -> Literal["Hot", "Warm", "Cold"]:
    if score >= 70:
        return "Hot"
    if score >= 45:
        return "Warm"
    return "Cold"


def _build_summary(
    lead: LeadInput,
    rating: Literal["Hot", "Warm", "Cold"],
    score: int,
    reasons: list[str],
    ai_insights: AILeadInsights | None,
) -> str:
    base = (
        f"[Auto-Qualification] {lead.name} ({lead.company or 'No Company'}) -> "
        f"{rating} ({score}/100). Reasons: {'; '.join(reasons)}."
    )
    if not ai_insights:
        return base

    return (
        f"{base}\n"
        f"[AI Insights] Urgency: {ai_insights.urgency} | "
        f"Pain Point: {ai_insights.pain_point} | "
        f"Summary: {ai_insights.executive_summary}"
    )


def qualify_lead_deterministic(lead: LeadInput) -> LeadQualification:
    score = 20
    reasons: list[str] = []

    corp_email = is_corporate_email(lead.email)
    if corp_email:
        score += 25
        reasons.append("Corporate email detected")
    else:
        reasons.append("No valid corporate email")

    if lead.company and lead.company.strip():
        score += 15
        reasons.append(f"Company provided ({lead.company.strip()})")
    else:
        reasons.append("Company missing")

    desc = (lead.description or "").strip()
    desc_lower = desc.lower()

    if len(desc) >= 25:
        score += 15
        reasons.append("Detailed context in description")

    matched_keywords = sorted(kw for kw in HIGH_INTENT_KEYWORDS if kw in desc_lower)
    if matched_keywords:
        keyword_bonus = min(len(matched_keywords) * 10, 25)
        score += keyword_bonus
        reasons.append(f"High-intent keywords found: {', '.join(matched_keywords)}")

    final_score = max(0, min(100, score))
    rating = _score_to_rating(final_score)
    summary = _build_summary(lead, rating, final_score, reasons, ai_insights=None)

    logger.info("Lead %s qualified deterministically as %s (score=%d).", lead.id, rating, final_score)

    return LeadQualification(
        lead_id=lead.id,
        score=final_score,
        rating=rating,
        is_corporate_email=corp_email,
        reasons=reasons,
        ai_insights=None,
        summary=summary,
    )


def analyze_with_gemini(lead: LeadInput) -> AILeadInsights | None:
    if not settings.gemini_api_key:
        logger.info("GEMINI_API_KEY not set. Skipping AI enrichment.")
        return None

    has_context = any(
        [
            lead.description and lead.description.strip(),
            lead.company and lead.company.strip(),
            is_corporate_email(lead.email),
        ]
    )
    if not has_context:
        logger.info("Lead %s has insufficient context. Skipping AI enrichment.", lead.id)
        return None

    prompt = (
        "You are a B2B Sales Operations analyst. Analyze the inbound lead below and "
        "return structured qualification insights in English.\n\n"
        "Evaluation rules:\n"
        "1. Assess buying intent, technical need, and urgency from the description (if provided).\n"
        "2. Evaluate the email domain and company alignment: reward legitimate custom corporate "
        "domains that match the stated company, treat generic role emails (e.g. info@, contact@) "
        "conservatively, and penalize disposable, fake, or clearly mismatched domains.\n\n"
        f"Name: {lead.name}\n"
        f"Company: {lead.company or 'Unknown'}\n"
        f"Email: {lead.email or 'Unknown'}\n"
        f"Description: {(lead.description or '').strip() or 'No description provided'}"
    )

    try:
        client = genai.Client(api_key=settings.gemini_api_key)
        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=AILeadInsights,
                temperature=0.1,
            ),
        )
        if not response.text:
            return None
        return AILeadInsights.model_validate_json(response.text)
    except Exception as exc:
        logger.warning("Gemini analysis failed for Lead %s: %s", lead.id, exc)
        return None


def qualify_lead(lead: LeadInput, use_ai: bool = True) -> LeadQualification:
    base = qualify_lead_deterministic(lead)
    if not use_ai:
        return base

    ai_insights = analyze_with_gemini(lead)
    if not ai_insights:
        return base

    reasons = [*base.reasons, f"AI score adjustment ({ai_insights.score_delta:+d})"]
    final_score = max(0, min(100, base.score + ai_insights.score_delta))
    rating = _score_to_rating(final_score)
    summary = _build_summary(lead, rating, final_score, reasons, ai_insights)

    logger.info(
        "Lead %s enriched with AI as %s (score=%d, delta=%+d).",
        lead.id,
        rating,
        final_score,
        ai_insights.score_delta,
    )

    return LeadQualification(
        lead_id=lead.id,
        score=final_score,
        rating=rating,
        is_corporate_email=base.is_corporate_email,
        reasons=reasons,
        ai_insights=ai_insights,
        summary=summary,
    )

