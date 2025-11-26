"""
Pipeline module for secure inter-tool file transfer (v0.8.0).

Enables tools to pass output files to other tools via a secure,
time-limited pipeline mechanism with cryptographic IDs.
"""

import os
import secrets
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict


@dataclass
class PipelineFile:
    """Metadata for a pipeline file"""

    pipeline_id: str
    file_path: str
    source_tool_slug: str
    mime_type: str
    created_at: float  # Unix timestamp
    ttl_seconds: int
    original_name: str = ""


# In-memory pipeline store
_pipeline_store: Dict[str, PipelineFile] = {}

# Pipeline storage directory
_PIPELINE_DIR: Path | None = None


def _get_pipeline_dir() -> Path:
    """Get or create the pipeline storage directory"""
    global _PIPELINE_DIR

    if _PIPELINE_DIR is None:
        # Use system temp directory + our subdirectory
        import tempfile

        base_temp = Path(tempfile.gettempdir())
        _PIPELINE_DIR = base_temp / "isvicre-cakisi-pipeline"
        _PIPELINE_DIR.mkdir(parents=True, exist_ok=True)

    return _PIPELINE_DIR


def _generate_pipeline_id() -> str:
    """Generate a cryptographically secure pipeline ID"""
    return secrets.token_urlsafe(32)


def _is_expired(metadata: PipelineFile) -> bool:
    """Check if a pipeline file has expired based on TTL"""
    age = time.time() - metadata.created_at
    return age > metadata.ttl_seconds


def create_pipeline_file(
    source_tool_slug: str,
    input_file_path: str,
    mime_type: str,
    ttl_seconds: int = 600,
    original_name: str = "",
) -> str:
    """
    Create a pipeline file for inter-tool transfer.

    Args:
        source_tool_slug: Slug of the tool that created this file
        input_file_path: Path to the file to pipeline
        mime_type: MIME type of the file
        ttl_seconds: Time-to-live in seconds (default: 10 minutes)
        original_name: Original filename (optional)

    Returns:
        pipeline_id: Unique identifier for retrieving this file

    Security:
        - Uses cryptographically secure random IDs
        - Files are stored in a dedicated temp directory
        - TTL enforced on every resolve
    """
    import shutil

    # Generate secure ID
    pipeline_id = _generate_pipeline_id()

    # Determine file extension from original path
    ext = Path(input_file_path).suffix

    # Create pipeline file path
    pipeline_dir = _get_pipeline_dir()
    pipeline_file_path = pipeline_dir / f"{pipeline_id}{ext}"

    # Copy file to pipeline storage
    shutil.copy2(input_file_path, pipeline_file_path)

    # Store metadata
    metadata = PipelineFile(
        pipeline_id=pipeline_id,
        file_path=str(pipeline_file_path),
        source_tool_slug=source_tool_slug,
        mime_type=mime_type,
        created_at=time.time(),
        ttl_seconds=ttl_seconds,
        original_name=original_name or Path(input_file_path).name,
    )

    _pipeline_store[pipeline_id] = metadata

    return pipeline_id


def resolve_pipeline_file(pipeline_id: str) -> Dict[str, any] | None:
    """
    Resolve a pipeline file by ID.

    Args:
        pipeline_id: The pipeline identifier

    Returns:
        Dictionary with file metadata, or None if not found/expired

    Note:
        Expired files are automatically cleaned up during resolve.
    """
    # Check if exists in store
    if pipeline_id not in _pipeline_store:
        return None

    metadata = _pipeline_store[pipeline_id]

    # Check if expired
    if _is_expired(metadata):
        # Cleanup expired file
        _cleanup_pipeline_file(pipeline_id, metadata)
        return None

    # Check if file still exists
    if not os.path.exists(metadata.file_path):
        # File was deleted externally, cleanup metadata
        del _pipeline_store[pipeline_id]
        return None

    # Return metadata as dict
    return {
        "pipeline_id": metadata.pipeline_id,
        "file_path": metadata.file_path,
        "source_tool": metadata.source_tool_slug,
        "mime_type": metadata.mime_type,
        "original_name": metadata.original_name,
        "created_at": datetime.fromtimestamp(metadata.created_at).isoformat(),
        "ttl_seconds": metadata.ttl_seconds,
    }


def _cleanup_pipeline_file(pipeline_id: str, metadata: PipelineFile) -> None:
    """Internal helper to cleanup a single pipeline file"""
    # Remove file if exists
    if os.path.exists(metadata.file_path):
        try:
            os.remove(metadata.file_path)
        except OSError:
            pass  # File might be in use, will be caught next cleanup

    # Remove from store
    if pipeline_id in _pipeline_store:
        del _pipeline_store[pipeline_id]


def cleanup_expired_pipeline_files() -> int:
    """
    Clean up all expired pipeline files.

    Returns:
        Number of files cleaned up

    Note:
        This can be called periodically or on-demand.
        Currently called during app shutdown or manually.
    """
    expired_ids = []

    # Find expired files
    for pipeline_id, metadata in _pipeline_store.items():
        if _is_expired(metadata):
            expired_ids.append((pipeline_id, metadata))

    # Cleanup
    for pipeline_id, metadata in expired_ids:
        _cleanup_pipeline_file(pipeline_id, metadata)

    return len(expired_ids)


def get_pipeline_stats() -> Dict[str, any]:
    """
    Get statistics about current pipeline usage.

    Returns:
        Dictionary with stats (for debugging/monitoring)
    """
    total = len(_pipeline_store)
    expired = sum(1 for m in _pipeline_store.values() if _is_expired(m))

    return {
        "total_files": total,
        "active_files": total - expired,
        "expired_files": expired,
        "storage_dir": str(_get_pipeline_dir()),
    }
