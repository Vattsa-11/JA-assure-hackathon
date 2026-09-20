import sys

backend_dir = r"c:\Users\sharv\Downloads\hackthon\ja-assure-marketing-agent\backend"
sys.path.append(backend_dir)

from app.agents.compliance import check_compliance
from app.core.db import SessionLocal
from app.models.content import ContentAsset, ContentStatus, ContentVersion


def prove_compliance():
    db = SessionLocal()
    try:
        print("\n--- PHASE 1: SUBMITTING ILLEGAL CLAIM TO COMPLIANCE GATE ---")

        # Create a dummy asset
        asset = ContentAsset(brand_id=1, platform="linkedin", status=ContentStatus.draft)
        db.add(asset)
        db.commit()
        db.refresh(asset)

        bad_text = "Rest assured, our clients always receive their full claim amount, no exceptions."
        version = ContentVersion(content_asset_id=asset.id, content_text=bad_text)
        db.add(version)
        db.commit()

        print(f"Content:\n\"{bad_text}\"")
        print("\n--- PHASE 2: RUNNING COMPLIANCE CHECK ---")

        review = check_compliance(db, asset.id)

        print(f"Passed: {review.passed}")
        if not review.passed:
            print("Flagged Phrases:")
            for p in review.flagged_phrases:
                print(f" - {p}")
            print("Reasons:")
            for r in review.reasons:
                print(f" - {r}")

        if not review.passed:
            print("\nSuccess! The compliance gate correctly blocked the illegal claim.")
        else:
            print("\nFailed! The compliance gate let the illegal claim through.")

    finally:
        db.close()

if __name__ == "__main__":
    prove_compliance()
