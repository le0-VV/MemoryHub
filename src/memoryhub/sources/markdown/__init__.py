"""Markdown source adapter for MemoryHub."""

from memoryhub.sources.markdown.parser import parse_markdown, read_markdown_file
from memoryhub.sources.markdown.schema import MarkdownDocument
from memoryhub.sources.markdown.serializer import (
    new_markdown_document,
    serialize_markdown,
    write_markdown_file,
)
from memoryhub.sources.markdown.sync import (
    iter_markdown_files,
    resolve_document_path,
    safe_relative_markdown_path,
)

__all__ = [
    "MarkdownDocument",
    "iter_markdown_files",
    "new_markdown_document",
    "parse_markdown",
    "read_markdown_file",
    "resolve_document_path",
    "safe_relative_markdown_path",
    "serialize_markdown",
    "write_markdown_file",
]
