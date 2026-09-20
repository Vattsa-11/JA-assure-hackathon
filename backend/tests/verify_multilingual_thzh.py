import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from pathlib import Path

backend_dir = r"c:\Users\sharv\Downloads\hackthon\ja-assure-marketing-agent\backend"
sys.path.append(backend_dir)

from app.core.db import SessionLocal
from app.models.content import ContentAsset, ContentVersion, ContentStatus
from app.agents.localization import localize_content

def prove_multilingual_extended():
    db = SessionLocal()
    try:
        english_text = "As a small business owner, unexpected events can disrupt your cash flow. Jade's tailored insurance ensures you are covered, giving you peace of mind."
        
        for lang_code, expected_script in [("th", "Thai script"), ("zh", "Chinese characters")]:
            print(f"\n{'='*60}")
            print(f"LOCALIZING TO: {lang_code.upper()}")
            asset = ContentAsset(brand_id=1, platform="linkedin", status=ContentStatus.approved)
            db.add(asset)
            db.commit()
            db.refresh(asset)
            
            version = ContentVersion(content_asset_id=asset.id, content_text=english_text)
            db.add(version)
            db.commit()

            localized_asset = localize_content(db, asset.id, lang_code)
            loc_version = db.query(ContentVersion).filter(ContentVersion.content_asset_id == localized_asset.id).first()

            print(f"Original (EN): {english_text}")
            print(f"Localized ({lang_code}): {loc_version.content_text}")

            # Verify the output actually contains the expected script
            if lang_code == "th":
                # Thai Unicode block: U+0E00–U+0E7F
                has_correct_script = any('\u0e00' <= c <= '\u0e7f' for c in loc_version.content_text)
            elif lang_code == "zh":
                # CJK Unified Ideographs: U+4E00–U+9FFF
                has_correct_script = any('\u4e00' <= c <= '\u9fff' for c in loc_version.content_text)
            
            if has_correct_script:
                print(f"PASS: Output contains actual {expected_script} characters (not Latin/romanization)")
            else:
                print(f"FAIL: Output does NOT contain {expected_script} characters")

    finally:
        db.close()

if __name__ == "__main__":
    prove_multilingual_extended()
