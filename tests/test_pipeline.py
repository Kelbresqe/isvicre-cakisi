"""Tests for pipeline module (v0.8.0)"""

import os
import tempfile
import time
from pathlib import Path

import pytest

from app.core.pipeline import (
    cleanup_expired_pipeline_files,
    create_pipeline_file,
    get_pipeline_stats,
    resolve_pipeline_file,
)


@pytest.fixture
def sample_file():
    """Create a temporary sample file for testing"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("Test pipeline content")
        temp_path = f.name

    yield temp_path

    # Cleanup
    if os.path.exists(temp_path):
        os.remove(temp_path)


def test_create_pipeline_file(sample_file):
    """Test creating a pipeline file"""
    pipeline_id = create_pipeline_file(
        source_tool_slug="test-tool", input_file_path=sample_file, mime_type="text/plain", original_name="test.txt"
    )

    # Should return a pipeline ID
    assert pipeline_id is not None
    assert len(pipeline_id) > 20  # Secure random string

    # Should be resolvable
    metadata = resolve_pipeline_file(pipeline_id)
    assert metadata is not None
    assert metadata["source_tool"] == "test-tool"
    assert metadata["mime_type"] == "text/plain"
    assert metadata["original_name"] == "test.txt"

    # Cleanup
    cleanup_expired_pipeline_files()


def test_resolve_pipeline_file_not_found():
    """Test resolving non-existent pipeline file"""
    result = resolve_pipeline_file("nonexistent-id-12345")
    assert result is None


def test_pipeline_file_ttl_expiry(sample_file):
    """Test that pipeline files expire after TTL"""
    # Create with 1 second TTL
    pipeline_id = create_pipeline_file(
        source_tool_slug="test-tool", input_file_path=sample_file, mime_type="text/plain", ttl_seconds=1
    )

    # Should be resolvable immediately
    metadata = resolve_pipeline_file(pipeline_id)
    assert metadata is not None

    # Wait for expiry
    time.sleep(1.5)

    # Should now return None (expired)
    metadata = resolve_pipeline_file(pipeline_id)
    assert metadata is None


def test_cleanup_expired_files(sample_file):
    """Test cleanup of expired pipeline files"""
    # Create file with short TTL
    pipeline_id = create_pipeline_file(
        source_tool_slug="test-tool", input_file_path=sample_file, mime_type="text/plain", ttl_seconds=1
    )

    # Wait for expiry
    time.sleep(1.5)

    # Run cleanup
    cleaned = cleanup_expired_pipeline_files()

    # Should have cleaned at least 1 file
    assert cleaned >= 1

    # File should no longer be resolvable
    metadata = resolve_pipeline_file(pipeline_id)
    assert metadata is None


def test_pipeline_stats(sample_file):
    """Test pipeline statistics"""
    # Create a file
    pipeline_id = create_pipeline_file(
        source_tool_slug="test-tool", input_file_path=sample_file, mime_type="text/plain"
    )

    stats = get_pipeline_stats()

    # Check stats structure
    assert "total_files" in stats
    assert "active_files" in stats
    assert "expired_files" in stats
    assert "storage_dir" in stats

    # Should have at least 1 file
    assert stats["total_files"] >= 1

    # Cleanup
    cleanup_expired_pipeline_files()


def test_pipeline_file_security_no_path_traversal(sample_file):
    """Test that pipeline IDs don't expose file paths"""
    pipeline_id = create_pipeline_file(
        source_tool_slug="test-tool", input_file_path=sample_file, mime_type="text/plain"
    )

    # Pipeline ID should not contain path separators
    assert "/" not in pipeline_id
    assert "\\" not in pipeline_id
    assert ".." not in pipeline_id

    # Cleanup
    cleanup_expired_pipeline_files()


def test_pipeline_file_copy_not_move(sample_file):
    """Test that original file is preserved (copy, not move)"""
    original_exists_before = os.path.exists(sample_file)

    pipeline_id = create_pipeline_file(
        source_tool_slug="test-tool", input_file_path=sample_file, mime_type="text/plain"
    )

    # Original file should still exist
    original_exists_after = os.path.exists(sample_file)

    assert original_exists_before
    assert original_exists_after

    # Cleanup
    cleanup_expired_pipeline_files()
