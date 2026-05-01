"""OpenViking-style contracts for MemoryHub."""

from memoryhub.openviking.compatibility import (
    SUPPORTED_CLAIMS,
    UNSUPPORTED_CLAIMS,
    CompatibilityClaim,
    compatibility_report,
)
from memoryhub.openviking.layout import CONTEXT_ROOT, SUPPORTED_CONTEXT_DIRS
from memoryhub.openviking.resources import OpenVikingResource, resource_from_document
from memoryhub.openviking.uris import (
    OpenVikingURI,
    build_openviking_uri,
    parse_openviking_uri,
)

__all__ = [
    "CONTEXT_ROOT",
    "SUPPORTED_CLAIMS",
    "SUPPORTED_CONTEXT_DIRS",
    "UNSUPPORTED_CLAIMS",
    "CompatibilityClaim",
    "OpenVikingResource",
    "OpenVikingURI",
    "build_openviking_uri",
    "compatibility_report",
    "parse_openviking_uri",
    "resource_from_document",
]
