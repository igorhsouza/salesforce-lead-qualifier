import logging

from src.qualifier import LeadInput, qualify_lead
from src.salesforce_client import SalesforceClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("lead_qualifier_runner")

SEPARATOR = "\n\n---\nPrevious Description:\n"


def extract_original_description(raw_description: str | None) -> str | None:
    if not raw_description:
        return None
    if SEPARATOR in raw_description:
        return raw_description.split(SEPARATOR, 1)[1].strip() or None
    if raw_description.startswith("[Auto-Qualification]"):
        return None
    return raw_description.strip() or None


def run() -> None:
    client = SalesforceClient()
    leads = client.query_leads(limit=10)

    if not leads:
        logger.info("No leads found to qualify.")
        return

    for raw_lead in leads:
        current_description = raw_lead.get("Description")
        original_description = extract_original_description(current_description)

        lead_input = LeadInput(
            id=raw_lead["Id"],
            name=raw_lead.get("Name") or "Unknown Lead",
            company=raw_lead.get("Company"),
            email=raw_lead.get("Email"),
            description=original_description,
        )

        qualification = qualify_lead(lead_input, use_ai=True)

        updated_description = qualification.summary
        if original_description:
            updated_description = f"{qualification.summary}{SEPARATOR}{original_description}"

        if (
            raw_lead.get("Rating") == qualification.rating
            and (current_description or "").strip() == updated_description.strip()
        ):
            logger.info("Lead %s already up to date. Skipping PATCH.", qualification.lead_id)
            continue

        client.update_lead(
            lead_id=qualification.lead_id,
            rating=qualification.rating,
            description=updated_description,
        )


if __name__ == "__main__":
    run()
