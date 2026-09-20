import sys

backend_dir = r"c:\Users\sharv\Downloads\hackthon\ja-assure-marketing-agent\backend"
sys.path.append(backend_dir)

from app.agents.research import run_competitor_digest
from app.core.db import SessionLocal
from app.models.research import CompetitorDigestEntry


def prove_research():
    db = SessionLocal()
    urls = [
        "https://www.fwd.com.sg/",
        "https://www.income.com.sg/"
    ]

    print("\n--- RUNNING DIGEST (1ST PASS) ---")
    results_pass1 = run_competitor_digest(db, urls)
    for res in results_pass1:
        print(f"URL: {res.competitor_url}")
        print(f"Hash: {res.last_snapshot_hash}")
        print(f"Action: {res.suggested_action}")
        print("-" * 60)

    print("\n--- MUTATING DB TO SIMULATE COMPETITOR WEBSITE UPDATE ---")
    entry_to_mutate = db.query(CompetitorDigestEntry).filter(CompetitorDigestEntry.competitor_url == urls[0]).first()
    if entry_to_mutate:
        entry_to_mutate.last_snapshot_hash = "FAKE_OLD_HASH_123"
        db.commit()
        print(f"Changed hash for {urls[0]} to 'FAKE_OLD_HASH_123'")

    print("\n--- RUNNING DIGEST (2ND PASS) ---")
    print("Should generate exactly 1 new entry for the mutated URL.")
    results_pass2 = run_competitor_digest(db, urls)
    if len(results_pass2) == 1 and results_pass2[0].competitor_url == urls[0]:
        print(f"Success! Detected change for {urls[0]} and generated new insight:")
        print(f"New Action: {results_pass2[0].suggested_action}")
    else:
        print(f"Failed. Generated {len(results_pass2)} new entries unexpectedly.")

if __name__ == "__main__":
    prove_research()
