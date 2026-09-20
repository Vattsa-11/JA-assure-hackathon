import sys

backend_dir = r"c:\Users\sharv\Downloads\hackthon\ja-assure-marketing-agent\backend"
sys.path.append(backend_dir)

from app.agents.localization import SUPPORTED_LANGUAGES, localize_content
from app.core.db import SessionLocal
from app.models.content import ContentAsset, ContentStatus, ContentVersion


def prove_multilingual():
    db = SessionLocal()
    try:
        print("\n--- PHASE 1: CREATING ENGLISH ASSET ---")

        # Create a dummy asset
        asset = ContentAsset(brand_id=1, platform="linkedin", status=ContentStatus.approved)
        db.add(asset)
        db.commit()
        db.refresh(asset)

        english_text = "As a small business owner, unexpected events can disrupt your cash flow. Jade's tailored insurance ensures you are covered, giving you peace of mind."
        version = ContentVersion(content_asset_id=asset.id, content_text=english_text)
        db.add(version)
        db.commit()

        print(f"Original English Text:\n\"{english_text}\"")

        target_lang = "id"  # Bahasa Indonesia
        print(f"\n--- PHASE 2: LOCALIZING TO {SUPPORTED_LANGUAGES[target_lang]} ---")

        localized_asset = localize_content(db, asset.id, target_lang)

        # Get localized text
        loc_version = db.query(ContentVersion).filter(ContentVersion.content_asset_id == localized_asset.id).first()
        print(f"\nLocalized Text:\n\"{loc_version.content_text}\"")

        print("\n--- PHASE 3: VERIFYING INDEPENDENT COMPLIANCE CHECK ---")
        print(f"Localized Asset Status: {localized_asset.status}")

        # If compliance passed, it should be pending_review (the compliance agent sets this)
        # We can also check if a ComplianceReview row was created.
        from app.models.content import ComplianceReview
        review = db.query(ComplianceReview).filter(ComplianceReview.content_asset_id == localized_asset.id).first()

        if review:
            print("Independent Compliance Review Executed: Yes")
            print(f"Compliance Passed: {review.passed}")
            if not review.passed:
                print(f"Flagged Phrases: {review.flagged_phrases}")
        else:
            print("Independent Compliance Review Executed: No (FAILED)")

    finally:
        db.close()

if __name__ == "__main__":
    prove_multilingual()
