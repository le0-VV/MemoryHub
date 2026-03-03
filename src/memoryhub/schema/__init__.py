"""Schema system for Basic Memory.

Provides Picoschema-based validation for notes using observation/relation mapping.
Schemas are just notes with type: schema — no new data model, no migration.
"""

from memoryhub.schema.parser import (
    SchemaField,
    SchemaDefinition,
    parse_picoschema,
    parse_schema_note,
)
from memoryhub.schema.resolver import resolve_schema
from memoryhub.schema.validator import (
    FieldResult,
    ValidationResult,
    validate_note,
)
from memoryhub.schema.inference import (
    FieldFrequency,
    InferenceResult,
    ObservationData,
    RelationData,
    NoteData,
    infer_schema,
    analyze_observations,
    analyze_relations,
)
from memoryhub.schema.diff import (
    SchemaDrift,
    diff_schema,
)

__all__ = [
    # Parser
    "SchemaField",
    "SchemaDefinition",
    "parse_picoschema",
    "parse_schema_note",
    # Resolver
    "resolve_schema",
    # Validator
    "FieldResult",
    "ValidationResult",
    "validate_note",
    # Inference
    "FieldFrequency",
    "InferenceResult",
    "ObservationData",
    "RelationData",
    "NoteData",
    "infer_schema",
    "analyze_observations",
    "analyze_relations",
    # Diff
    "SchemaDrift",
    "diff_schema",
]
