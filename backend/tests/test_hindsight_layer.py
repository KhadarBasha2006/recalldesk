from __future__ import annotations

from app.hindsight_layer import HindsightLayer
from tests.conftest import FakeHindsightClient


def test_retain_includes_customer_metadata():
    client = FakeHindsightClient()
    layer = HindsightLayer()
    layer._client = client

    layer.retain_interaction("p@x.y", "customer", "router drops nightly", document_id="chat-1")

    assert len(client.retained) == 1
    r = client.retained[0]
    assert r["metadata"]["customer_email"] == "p@x.y"
    assert r["document_id"] == "chat-1"
    assert "router drops nightly" in r["content"]


def test_retain_failure_never_raises():
    class Exploding(FakeHindsightClient):
        def retain(self, *a, **k):
            raise RuntimeError("hindsight down")

    layer = HindsightLayer()
    layer._client = Exploding()
    layer.retain_interaction("p@x.y", "customer", "hello")  # must not raise


def test_recall_failure_returns_empty():
    class Exploding(FakeHindsightClient):
        def recall(self, *a, **k):
            raise RuntimeError("hindsight down")

    layer = HindsightLayer()
    layer._client = Exploding()
    assert layer.recall("anything") == []


def test_bank_stats_counts_observations():
    client = FakeHindsightClient()
    layer = HindsightLayer()
    layer._client = client
    stats = layer.bank_stats()
    assert stats["memories"] == 4
    assert stats["observations"] == 1
    assert stats["mental_models"] == 0
