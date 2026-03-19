# MCP Server Design - Founder FIRE Knowledge Base

## Overview
This MCP server exposes the collection of PDF and EPUB documents in the `ref/` directory as resources and tools to the AI agent.

## Architecture
- **Language**: Python 3.10+
- **Transport**: Stdio (Standard Input/Output) for local integration.
- **Libraries**:
    - `mcp`: Official Python SDK (if available) or raw JSON-RPC 2.0 implementation.
    - `pypdf`: For extracting text from PDFs.
    - `ebooklib` & `BeautifulSoup`: For extracting text from EPUBs.
    - `rank_bm25` or `whoosh`: For simple local full-text search (optional, but good for "tools").

## Resources
The server will expose each file in `ref/` as a resource.
- **URI Scheme**: `founder-fire://kb/{filename}`
- **MIME Types**: `text/plain` (converted content).

### List Resources
Returns a list of all available books/articles.

### Read Resource
Returns the full text content of a specific document.
- *Note*: Large files might need chunking or lazy loading, but for now we'll return full text or first N chars.

## Tools
To help the agent find relevant info without reading entire books.

### `search_knowledge_base`
- **Arguments**: `query` (string)
- **Returns**: List of relevant snippets with citations (File, Page/Chapter).
- **Implementation**:
    - On startup, index all documents in `ref/`.
    - Use a simple BM25 or TF-IDF index.
    - Return top 5-10 matching chunks.

## Project Structure
```
sup_mcp/
├── main.py           # Entry point
├── server.py         # MCP Protocol handling
├── indexer.py        # Document processing & indexing
├── requirements.txt
└── .env
```

## Implementation Steps
1.  **Setup**: Create `sup_mcp` directory and virtualenv.
2.  **Indexer**: Write functions to read PDF/EPUB and extract text.
3.  **Server**: Implement `list_resources`, `read_resource`, and `call_tool`.
4.  **Integration**: Configure the agent (Claude Desktop or similar) to use this server.
