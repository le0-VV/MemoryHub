"""Knowledge graph schema exports.

This module exports all schema classes to simplify imports.
Rather than importing from individual schema files, you can
import everything from memoryhub.schemas.
"""

# Base types and models
from memoryhub.schemas.base import (
    Observation,
    NoteType,
    RelationType,
    Relation,
    Entity,
)

# Delete operation models
from memoryhub.schemas.delete import (
    DeleteEntitiesRequest,
)

# Request models
from memoryhub.schemas.request import (
    SearchNodesRequest,
    GetEntitiesRequest,
    CreateRelationsRequest,
)

# Response models
from memoryhub.schemas.response import (
    SQLAlchemyModel,
    ObservationResponse,
    RelationResponse,
    EntityResponse,
    EntityListResponse,
    SearchNodesResponse,
    DeleteEntitiesResponse,
)

from memoryhub.schemas.project_info import (
    ProjectStatistics,
    ActivityMetrics,
    SystemStatus,
    EmbeddingStatus,
    ProjectInfoResponse,
)

from memoryhub.schemas.directory import (
    DirectoryNode,
)

from memoryhub.schemas.sync_report import (
    SyncReportResponse,
)

# For convenient imports, export all models
__all__ = [
    # Base
    "Observation",
    "NoteType",
    "RelationType",
    "Relation",
    "Entity",
    # Requests
    "SearchNodesRequest",
    "GetEntitiesRequest",
    "CreateRelationsRequest",
    # Responses
    "SQLAlchemyModel",
    "ObservationResponse",
    "RelationResponse",
    "EntityResponse",
    "EntityListResponse",
    "SearchNodesResponse",
    "DeleteEntitiesResponse",
    # Delete Operations
    "DeleteEntitiesRequest",
    # Project Info
    "ProjectStatistics",
    "ActivityMetrics",
    "SystemStatus",
    "EmbeddingStatus",
    "ProjectInfoResponse",
    # Directory
    "DirectoryNode",
    # Sync
    "SyncReportResponse",
]
