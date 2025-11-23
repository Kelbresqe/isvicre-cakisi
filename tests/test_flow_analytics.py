"""Tests for tool flow analytics (v0.8.0)"""

from app.core.observability import (
    get_analytics_stats,
    get_flow_stats,
    record_tool_flow,
    reset_analytics,
)


def test_record_tool_flow():
    """Test recording tool-to-tool flows"""
    reset_analytics()

    record_tool_flow("image-converter", "image-resizer")
    record_tool_flow("image-converter", "image-resizer")  # Same flow twice
    record_tool_flow("pdf-merger", "pdf-splitter")

    flows = get_flow_stats()

    assert "top_flows" in flows
    assert len(flows["top_flows"]) > 0

    # Most common flow should be image-converter -> image-resizer (2 times)
    top_flow = flows["top_flows"][0]
    assert top_flow["from"] == "image-converter"
    assert top_flow["to"] == "image-resizer"
    assert top_flow["count"] == 2


def test_get_flow_stats():
    """Test flow stats structure"""
    reset_analytics()

    record_tool_flow("tool-a", "tool-b")

    flows = get_flow_stats()

    assert isinstance(flows, dict)
    assert "top_flows" in flows
    assert isinstance(flows["top_flows"], list)

    if flows["top_flows"]:
        flow_item = flows["top_flows"][0]
        assert "from" in flow_item
        assert "to" in flow_item
        assert "count" in flow_item


def test_analytics_stats_includes_flows():
    """Test that get_analytics_stats includes flow data"""
    reset_analytics()

    record_tool_flow("tool-x", "tool-y")

    stats = get_analytics_stats()

    assert "top_flows" in stats
    assert "total_flows" in stats
    assert stats["total_flows"] >= 1


def test_flow_stats_top_10_limit():
    """Test that flow stats respects top 10 limit"""
    reset_analytics()

    # Create 15 unique flows
    for i in range(15):
        record_tool_flow(f"tool-{i}", f"tool-{i + 1}")

    flows = get_flow_stats()

    # Should only return top 10
    assert len(flows["top_flows"]) <= 10
