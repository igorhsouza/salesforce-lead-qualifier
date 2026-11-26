import logging
from typing import Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from src.main import SEPARATOR, extract_original_description
from src.qualifier import LeadInput, LeadQualification, qualify_lead
from src.salesforce_client import SalesforceClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("lead_qualifier_api")

app = FastAPI(
    title="Salesforce Lead Qualifier API",
    version="0.2.0",
    description="Hybrid deterministic + Gemini lead qualification service for Salesforce.",
)


class QualifyLeadRequest(BaseModel):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    company: str | None = None
    email: str | None = None
    description: str | None = None
    use_ai: bool = True
    sync_to_salesforce: bool = True


class QualifyLeadResponse(BaseModel):
    qualification: LeadQualification
    synced_to_salesforce: bool
    sync_status: Literal["updated", "skipped_idempotent", "not_requested"]


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/qualify-lead", response_model=QualifyLeadResponse)
def qualify_lead_endpoint(payload: QualifyLeadRequest) -> QualifyLeadResponse:
    original_description = extract_original_description(payload.description)

    lead_input = LeadInput(
        id=payload.id,
        name=payload.name,
        company=payload.company,
        email=payload.email,
        description=original_description,
    )

    qualification = qualify_lead(lead_input, use_ai=payload.use_ai)

    if not payload.sync_to_salesforce:
        return QualifyLeadResponse(
            qualification=qualification,
            synced_to_salesforce=False,
            sync_status="not_requested",
        )

    updated_description = qualification.summary
    if original_description:
        updated_description = f"{qualification.summary}{SEPARATOR}{original_description}"

    try:
        client = SalesforceClient()
        if (payload.description or "").strip() == updated_description.strip():
            logger.info("Lead %s already up to date via API. Skipping PATCH.", qualification.lead_id)
            return QualifyLeadResponse(
                qualification=qualification,
                synced_to_salesforce=False,
                sync_status="skipped_idempotent",
            )

        client.update_lead(
            lead_id=qualification.lead_id,
            rating=qualification.rating,
            description=updated_description,
        )
        return QualifyLeadResponse(
            qualification=qualification,
            synced_to_salesforce=True,
            sync_status="updated",
        )
    except Exception as exc:
        logger.exception("Failed to sync Lead %s with Salesforce.", qualification.lead_id)
        raise HTTPException(status_code=502, detail=f"Salesforce sync failed: {exc}") from exc
