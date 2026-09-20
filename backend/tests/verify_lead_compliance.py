import sys
from pathlib import Path

backend_dir = r"c:\Users\sharv\Downloads\hackthon\ja-assure-marketing-agent\backend"
sys.path.append(backend_dir)

from app.core.db import SessionLocal
from app.models.lead import Lead, LeadStatus
from app.agents.compliance import check_lead_compliance

def prove_lead_compliance():
    db = SessionLocal()
    try:
        print("\n--- PHASE 1: SUBMITTING ILLEGAL OUTREACH DRAFT ---")
        
        lead = Lead(
            business_name="Test Business",
            niche="jewelry",
            region="Singapore",
            draft_outreach="Hello Test Business, if you buy insurance from us today, we will secretly refund 20% of your premium in cash as a kickback.",
            status=LeadStatus.draft
        )
        db.add(lead)
        db.commit()
        db.refresh(lead)
        
        print(f"Draft Outreach:\n\"{lead.draft_outreach}\"")
        print("\n--- PHASE 2: RUNNING LEAD COMPLIANCE CHECK ---")
        
        passed = check_lead_compliance(db, lead.id)
        
        print(f"Passed: {passed}")
        
        # Reload lead to check status
        db.refresh(lead)
        print(f"Lead Status After Check: {lead.status}")
        
        if not passed and lead.status == LeadStatus.draft:
            print("\nSuccess! The lead outreach compliance gate correctly caught the illegal offer and prevented the lead from advancing.")
        else:
            print("\nFailed! The compliance gate let the illegal outreach through.")

    finally:
        db.close()

if __name__ == "__main__":
    prove_lead_compliance()
