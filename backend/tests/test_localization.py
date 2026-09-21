"""
Offline unit tests for localization wiring (master plan 3E).

No LLM/network access: the shared llm_client singleton is monkeypatched and
an in-memory SQLite database stands in for the real one.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.agents.localization as localization_module
from app.agents.localization import localize_content, resolve_target_languages
from app.graphs.content_pipeline import content_graph, localize_node
from app.models.base import BaseModel
from app.models.brand import Brand
from app.models.content import ComplianceReview, ContentAsset, ContentStatus, ContentVersion


@pytest.fixture()
def db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    BaseModel.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()
    engine.dispose()


@pytest.fixture()
def fake_llm(monkeypatch):
    """Patch the shared llm_client singleton used by localization + compliance."""
    from app.services.llm_client import llm_client

    monkeypatch.setattr(llm_client, "generate_text", lambda **kwargs: "Kandungan dalam Bahasa Melayu")
    monkeypatch.setattr(
        llm_client,
        "generate_json",
        lambda **kwargs: {"passed": True, "flagged_phrases": [], "reasons": []},
    )


@pytest.fixture()
def seed_asset(db):
    brand = Brand(name="Jade", voice_description="Warm, understated luxury")
    db.add(brand)
    db.commit()
    asset = ContentAsset(
        brand_id=brand.id, platform="linkedin", language="en", status=ContentStatus.pending_review
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    db.add(ContentVersion(content_asset_id=asset.id, content_text="Protect your jewellery stock."))
    db.commit()
    return asset


def test_localize_creates_linked_asset_and_compliance(db, fake_llm, seed_asset):
    new_asset = localize_content(db, seed_asset.id, "ms")

    assert new_asset.id != seed_asset.id
    assert new_asset.source_asset_id == seed_asset.id
    assert new_asset.language == "ms"
    assert new_asset.platform == seed_asset.platform
    # Independent compliance check passed -> ready for human review.
    assert new_asset.status == ContentStatus.pending_review

    latest = (
        db.query(ContentVersion)
        .filter(ContentVersion.content_asset_id == new_asset.id)
        .order_by(ContentVersion.created_at.desc())
        .first()
    )
    assert latest is not None
    assert latest.content_text == "Kandungan dalam Bahasa Melayu"

    review = (
        db.query(ComplianceReview).filter(ComplianceReview.content_asset_id == new_asset.id).one()
    )
    assert review.passed is True


def test_localized_asset_failing_compliance_stays_draft(db, monkeypatch, fake_llm, seed_asset):
    from app.services.llm_client import llm_client

    monkeypatch.setattr(
        llm_client,
        "generate_json",
        lambda **kwargs: {"passed": False, "flagged_phrases": ["garansi 100%"], "reasons": ["Rule 1"]},
    )
    new_asset = localize_content(db, seed_asset.id, "th")
    # Failed localized versions never reach the review queue.
    assert new_asset.status == ContentStatus.draft


def test_unsupported_language_raises(db, fake_llm, seed_asset):
    with pytest.raises(ValueError, match="Unsupported language"):
        localize_content(db, seed_asset.id, "fr")


def test_missing_asset_raises(db, fake_llm):
    with pytest.raises(ValueError, match="not found"):
        localize_content(db, 9999, "ms")


def test_resolve_target_languages():
    assert resolve_target_languages(None) == list(localization_module.SUPPORTED_LANGUAGES.keys())
    assert resolve_target_languages([]) == list(localization_module.SUPPORTED_LANGUAGES.keys())
    assert resolve_target_languages(["ms", "xx"]) == ["ms"]  # unknown codes dropped
    assert resolve_target_languages(["xx", "yy"]) == []  # nothing valid -> localize nothing


def test_content_graph_has_localize_stage():
    nodes = set(content_graph.get_graph().nodes)
    assert {"generate", "compliance", "localize"} <= nodes


def test_localize_node_is_fail_soft(db, monkeypatch, fake_llm, seed_asset):
    # Route the node's sessions to the in-memory test database.
    monkeypatch.setattr(
        "app.graphs.content_pipeline.SessionLocal", sessionmaker(bind=db.get_bind())
    )

    # seed_asset localizes fine; the missing asset 9999 is skipped without aborting.
    result = localize_node(
        {"passed_asset_ids": [seed_asset.id, 9999], "localize": True, "target_languages": ["ms"]}
    )
    assert len(result["localized_asset_ids"]) == 1
    assert result["localized_failed_ids"] == []
