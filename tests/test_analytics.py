"""Tests for v0.7.0 Analytics functionality"""

import pytest

from app.core.observability import (
    get_analytics_stats,
    record_page_view,
    record_search_query,
    reset_analytics,
)


@pytest.fixture(autouse=True)
def reset_analytics_before_test():
    """Reset analytics before each test"""
    reset_analytics()
    yield
    reset_analytics()


def test_record_page_view():
    """Test page view recording"""
    record_page_view("test-tool")
    record_page_view("test-tool")
    record_page_view("another-tool")

    stats = get_analytics_stats()

    assert stats["total_page_views"] == 3
    assert stats["page_views_by_tool"]["test-tool"] == 2
    assert stats["page_views_by_tool"]["another-tool"] == 1


def test_record_search_query():
    """Test search query recording"""
    record_search_query("resim dönüştür")
    record_search_query("pdf")
    record_search_query("resim dönüştür")  # Duplicate
    record_search_query("a")  # Too short, should be ignored

    stats = get_analytics_stats()

    assert stats["total_searches"] == 3  # Only valid searches
    assert stats["unique_searches"] == 2  # "resim dönüştür" and "pdf"

    # Check top searches
    top_search = stats["top_searches"][0]
    assert top_search["query"] == "resim dönüştür"
    assert top_search["count"] == 2


def test_get_analytics_stats_structure():
    """Test analytics stats return structure"""
    record_page_view("tool1")
    record_search_query("test query")

    stats = get_analytics_stats()

    # Check all required keys
    assert "total_page_views" in stats
    assert "total_searches" in stats
    assert "unique_searches" in stats
    assert "top_viewed_tools" in stats
    assert "top_searches" in stats
    assert "page_views_by_tool" in stats

    # Check types
    assert isinstance(stats["top_viewed_tools"], list)
    assert isinstance(stats["top_searches"], list)
    assert isinstance(stats["page_views_by_tool"], dict)


def test_top_viewed_tools_limit():
    """Test that top_viewed_tools returns max 10 items"""
    # Create 15 different tools
    for i in range(15):
        record_page_view(f"tool-{i}")

    stats = get_analytics_stats()

    # Should only return top 10
    assert len(stats["top_viewed_tools"]) == 10


def test_analytics_with_user_agent_and_referer():
    """Test page view with optional parameters"""
    record_page_view(
        "test-tool", user_agent="Mozilla/5.0", referer="https://google.com"
    )

    stats = get_analytics_stats()
    assert stats["total_page_views"] == 1
