# Semantic Search

This guide covers MemoryHub's semantic search feature. The fork is SQLite-only, so all supported
semantic search flows run on local SQLite indexes and vector tables.

## Overview

MemoryHub supports both full-text search and semantic retrieval. Semantic search adds vector
embeddings that capture the meaning of your content, enabling:

- **Paraphrase matching**: Find "authentication flow" when searching for "login process"
- **Conceptual queries**: Search for "ways to improve performance" and find notes about caching, indexing, and optimization
- **Hybrid retrieval**: Combine the precision of keyword search with the recall of semantic similarity

Semantic search is enabled by default when semantic dependencies are available at runtime. In this
fork, it works on SQLite only.

## Installation

Semantic search dependencies (`fastembed`, `sqlite-vec`, and optional `openai`) are included in the
default project install.

```bash
pip install -e .
```

You can always override with `BASIC_MEMORY_SEMANTIC_SEARCH_ENABLED=true|false`.

### Platform Compatibility

| Platform | FastEmbed (local) | OpenAI (API) |
|---|---|---|
| macOS ARM64 (Apple Silicon) | Yes | Yes |
| macOS x86_64 (Intel Mac) | No — see workaround below | Yes |
| Linux x86_64 | Yes | Yes |
| Linux ARM64 | Yes | Yes |
| Windows x86_64 | Yes | Yes |

#### Intel Mac Workaround

The default install includes FastEmbed, which depends on ONNX Runtime. ONNX Runtime dropped Intel Mac (x86_64) wheels starting in v1.24, so install with a compatible ONNX Runtime pin first:

```bash
pip install -e . 'onnxruntime<1.24'
```

After installation, Intel Mac users have two runtime options:

**Option 1: Use OpenAI embeddings (recommended)**

```bash
export BASIC_MEMORY_SEMANTIC_SEARCH_ENABLED=true
export BASIC_MEMORY_SEMANTIC_EMBEDDING_PROVIDER=openai
export OPENAI_API_KEY=sk-...
```

**Option 2: Use FastEmbed locally**

Keep the same pinned installation and use FastEmbed (default provider):

```bash
export BASIC_MEMORY_SEMANTIC_SEARCH_ENABLED=true
export BASIC_MEMORY_SEMANTIC_EMBEDDING_PROVIDER=fastembed
```

## Quick Start

1. Install the project:

```bash
uv sync
```

2. (Optional) Explicitly enable semantic search:

```bash
export BASIC_MEMORY_SEMANTIC_SEARCH_ENABLED=true
```

3. Build vector embeddings for your existing content:

```bash
memoryhub reindex --embeddings
```

4. Search using semantic modes:

```python
# Pure vector similarity
search_notes("login process", search_type="vector")

# Hybrid: combines FTS precision with vector recall (recommended)
search_notes("login process", search_type="hybrid")

# Alias for vector search also works
search_notes("login process", search_type="semantic")

# Explicit full-text search
search_notes("login process", search_type="text")
```

## Configuration Reference

All settings are fields on `BasicMemoryConfig` and can be set via environment variables (prefixed with `BASIC_MEMORY_`).

| Config Field | Env Var | Default | Description |
|---|---|---|---|
| `semantic_search_enabled` | `BASIC_MEMORY_SEMANTIC_SEARCH_ENABLED` | Auto (`true` when semantic deps are available) | Enable semantic search. Required before vector/hybrid modes work. |
| `semantic_embedding_provider` | `BASIC_MEMORY_SEMANTIC_EMBEDDING_PROVIDER` | `"fastembed"` | Embedding provider: `"fastembed"` (local) or `"openai"` (API). |
| `semantic_embedding_model` | `BASIC_MEMORY_SEMANTIC_EMBEDDING_MODEL` | `"bge-small-en-v1.5"` | Model identifier. Auto-adjusted per provider if left at default. |
| `semantic_embedding_dimensions` | `BASIC_MEMORY_SEMANTIC_EMBEDDING_DIMENSIONS` | Auto-detected | Vector dimensions. 384 for FastEmbed, 1536 for OpenAI. Override only if using a non-default model. |
| `semantic_embedding_batch_size` | `BASIC_MEMORY_SEMANTIC_EMBEDDING_BATCH_SIZE` | `64` | Number of texts to embed per batch. |
| `semantic_vector_k` | `BASIC_MEMORY_SEMANTIC_VECTOR_K` | `100` | Candidate count for vector nearest-neighbour retrieval. Higher values improve recall at the cost of latency. |

## Embedding Providers

### FastEmbed (default)

FastEmbed runs entirely locally using ONNX models — no API key, no network calls, no cost.

- **Model**: `BAAI/bge-small-en-v1.5`
- **Dimensions**: 384
- **Tradeoff**: Smaller model, fast inference, good quality for most use cases

```bash
# Install project dependencies and enable semantic search
uv sync
export BASIC_MEMORY_SEMANTIC_SEARCH_ENABLED=true
```

### OpenAI

Uses OpenAI's embeddings API for higher-dimensional vectors. Requires an API key.

- **Model**: `text-embedding-3-small`
- **Dimensions**: 1536
- **Tradeoff**: Higher quality embeddings, requires API calls and an OpenAI key

```bash
export BASIC_MEMORY_SEMANTIC_SEARCH_ENABLED=true
export BASIC_MEMORY_SEMANTIC_EMBEDDING_PROVIDER=openai
export OPENAI_API_KEY=sk-...
```

When switching from FastEmbed to OpenAI (or vice versa), you must rebuild embeddings since the vector dimensions differ:

```bash
memoryhub reindex --embeddings
```

## Search Modes

### `text` (default)

Full-text keyword search using SQLite FTS. Supports boolean operators (`AND`, `OR`, `NOT`), phrase
matching, and prefix wildcards.

```python
search_notes("project AND planning", search_type="text")
```

This is the existing default and does not require semantic search to be enabled.

### `vector`

Pure semantic similarity search. Embeds your query and finds the nearest content vectors. Good for conceptual or paraphrase queries where exact keywords may not appear in the content.

```python
search_notes("how to speed up the app", search_type="vector")
```

Returns results ranked by cosine similarity. Individual observations and relations surface as first-class results, not collapsed into parent entities.

### `hybrid`

Combines FTS and vector results using score-based fusion. This is generally the best mode when you want both keyword precision and semantic recall.

```python
search_notes("authentication security", search_type="hybrid")
```

Score-based fusion uses the formula `max(vec, fts) + bonus * min(vec, fts)` to preserve the dominant signal while rewarding results found by both methods.

### When to Use Which

| Mode | Best For |
|---|---|
| `text` | Exact keyword matching, boolean queries, tag/category searches |
| `vector` | Conceptual queries, paraphrase matching, exploratory searches |
| `hybrid` | General-purpose search combining precision and recall |

## The Reindex Command

The reindex flow rebuilds search indexes without dropping the database.

```bash
# Rebuild everything (FTS + embeddings if semantic is enabled)
memoryhub reindex

# Only rebuild vector embeddings
memoryhub reindex --embeddings

# Only rebuild the full-text search index
memoryhub reindex --search

# Target a specific project
memoryhub reindex --project my-project
```

### When You Need to Reindex

- **Upgrade note**: Migration now performs a one-time automatic embedding backfill on upgrade.
- **Manual enable case**: If you explicitly had `semantic_search_enabled=false` and then turn it on
- **Provider change**: After switching between `fastembed` and `openai`
- **Model change**: After changing `semantic_embedding_model`
- **Dimension change**: After changing `semantic_embedding_dimensions`

The reindex command shows progress with embedded/skipped/error counts:

```
Project: main
  Building vector embeddings...
  ✓ Embeddings complete: 142 entities embedded, 0 skipped, 0 errors

Reindex complete!
```

## How It Works

### Chunking

Each entity in the search index is split into semantic chunks before embedding:

- **Headers**: Markdown headers (`#`, `##`, etc.) start new chunks
- **Bullets**: Each bullet item (`-`, `*`) becomes its own chunk for granular fact retrieval
- **Prose sections**: Non-bullet text is merged up to ~900 characters per chunk
- **Long sections**: Oversized content is split with ~120 character overlap to preserve context at boundaries

Each search index item type (entity, observation, relation) is chunked independently, so observations and relations are embeddable as discrete facts.

### Deduplication

Each chunk has a `source_hash` (SHA-256 of the chunk text). On re-sync, unchanged chunks skip re-embedding entirely. This makes incremental updates fast — only modified content triggers API calls or model inference.

### Hybrid Fusion

Hybrid search uses score-based fusion to merge FTS and vector results:

1. Run FTS search to get keyword-ranked results; normalize scores to [0, 1]
2. Run vector search to get similarity-ranked results (already [0, 1])
3. For each result, compute: `fused = max(vec_score, fts_score) + 0.3 * min(vec_score, fts_score)`
4. Sort by fused score

The dominant signal (whichever source scored higher) is preserved, and dual-source agreement adds a bonus. Unlike rank-based fusion, this approach retains score magnitude — a strong vector match stays strong even without an FTS hit.

### Observation-Level Results

Vector and hybrid modes return individual observations and relations as first-class search results, not just parent entities. This means a search for "water temperature for brewing" can surface the specific observation about 205°F without returning the entire "Coffee Brewing Methods" entity.

## Database Backends

## SQLite Backend

- **Vector storage**: [sqlite-vec](https://github.com/asg017/sqlite-vec) virtual table
- **Table creation**: At runtime when semantic search is first used — no migration needed
- **Embedding table**: `search_vector_embeddings` using `vec0(embedding float[N])` where N is the configured dimensions
- **Chunk metadata**: `search_vector_chunks` table stores chunk text, keys, and source hashes

The sqlite-vec extension is loaded per-connection. Vector tables are created lazily on first use.

There is no supported Postgres backend in this fork.

## Practical Notes

- `text` is best for exact keyword queries.
- `vector` and `semantic` are equivalent.
- `hybrid` is a good default when semantic search is enabled.
- `semantic_min_similarity` can be raised when you want fewer, higher-confidence vector matches.
- Rebuild embeddings whenever you change provider, model, or dimensions.
