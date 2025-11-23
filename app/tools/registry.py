from dataclasses import dataclass
from enum import Enum
from typing import List

from fastapi import APIRouter


class Category(str, Enum):
    IMAGE = "Görüntü Araçları"
    OFFICE = "Ofis Araçları"
    DEV = "Geliştirici Araçları"
    GAME = "Oyun & Eğlence"
    SECURITY = "Güvenlik Araçları"
    OTHER = "Diğer Araçlar"


@dataclass
class ToolRelation:
    """
    Defines a relationship between tools for the tool graph (v0.8.0).

    Used to suggest next logical steps in a workflow and enable
    pipeline-based tool chaining.
    """

    slug: str  # Target tool's slug
    relation_type: str  # "next", "alternative", or "advanced"
    label: str  # UI display label (e.g., "Metadata Temizle")
    description: str = ""  # Why this suggestion makes sense


@dataclass
class ToolInfo:
    slug: str
    title: str
    category: Category
    icon: str  # SVG icon string or class
    description: str
    image_url: str = ""  # Path to the tool's cover image
    short_description: str = ""  # For card display
    detailed_description: str = ""  # For tooltip/info
    seo_title: str = ""
    seo_description: str = ""
    keywords: str = ""

    # v0.7.0: Rich content for programmatic SEO
    long_description: str = ""  # 2-4 paragraphs of detailed explanation
    use_cases: list[str] = None  # 3-5 realistic usage scenarios
    faq: list[dict[str, str]] = None  # Q&A pairs with "question" and "answer" keys

    # Tool capabilities and limits (v0.5.0)
    accepts_files: bool = False  # Whether tool accepts file uploads
    accepts_text: bool = False  # Whether tool accepts text input
    max_upload_mb: int | None = None  # Maximum upload size in MB (None = use global default)

    # v0.8.0: Tool Graph & Pipeline capabilities
    suggested_next: list[ToolRelation] = None  # Next logical tools in workflow
    accepts_pipeline_files: bool = False  # Can consume files from pipeline
    produces_pipeline_files: bool = False  # Can produce files for pipeline

    def __post_init__(self):
        """Initialize mutable default values"""
        if self.use_cases is None:
            self.use_cases = []
        if self.faq is None:
            self.faq = []
        if self.suggested_next is None:
            self.suggested_next = []


class ToolRegistry:
    _tools: List[ToolInfo] = []
    _routers: List[APIRouter] = []

    @classmethod
    def register(cls, info: ToolInfo, router: APIRouter):
        """Registers a new tool with its metadata and router."""
        cls._tools.append(info)
        cls._routers.append(router)
        print(f"Tool registered: {info.title} ({info.slug})")

    @classmethod
    def get_tools(cls) -> List[ToolInfo]:
        return cls._tools

    @classmethod
    def get_routers(cls) -> List[APIRouter]:
        return cls._routers
