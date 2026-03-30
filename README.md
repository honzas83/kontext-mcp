# KonText MCP Server

An implementation of the [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) that provides a structured, LLM-optimized interface to the [KonText](https://lindat.mff.cuni.cz/services/kontext/) corpus query engine.

This server allows AI agents (like Claude) to perform sophisticated linguistic research, corpus queries, and collocation analysis across hundreds of corpora maintained by LINDAT/CLARIAH-CZ.

## Features

- **Corpus Discovery**: List and filter available corpora (including parallel ones).
- **Advanced Search**: Support for basic keyword searches and complex [Corpus Query Language (CQL)](https://www.sketchengine.eu/documentation/corpus-query-language/) expressions.
- **Parallel Corpora (Alignment)**: Full support for searching across aligned corpora (e.g., English-Czech) with specific logic to handle API alignment constraints.
- **Analytical Tools**:
    - **Frequency Distribution**: Group results by word, lemma, tag, or document metadata.
    - **Collocations**: Identify statistically significant word pairings around search hits.
- **Direct Web Integration**: Every search result includes a `web_url` that opens the exact search state in a browser for human review.
- **LLM-Optimized**: Tools use detailed `Annotated` type hints and docstrings to guide the model through multi-step linguistic workflows.

## Installation

### Prerequisites
- Python 3.10+
- A LINDAT/KonText account (optional for public corpora, required for some restricted ones).

### Setup
1. Clone this repository:
   ```bash
   git clone https://github.com/honzas83/kontext-mcp.git
   cd kontext-mcp
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

## Configuration

### Claude Desktop
To use this server with Claude Desktop, add the following to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "kontext": {
      "command": "/path/to/your/kontext-mcp/.venv/bin/python",
      "args": ["/path/to/your/kontext-mcp/kontext_mcp.py"]
    }
  }
}
```

## Tools Overview

- `list_corpora`: Find corpora IDs (e.g., `bnc`, `czeng_20`).
- `get_corpus_details`: Explore available attributes (lemma, tag) and metadata.
- `search_concordance`: Perform initial searches. Supports the `align` parameter for parallel results.
- `view_concordance`: Paginate through results.
- `get_frequency`: Generate frequency tables.
- `get_collocations`: Perform collocation analysis.
- `filter_concordance`: Refine results (positive/negative filters).
- `get_hit_details`: Get metadata for a specific occurrence (author, date, etc.).

## Technical Note: Parallel Searches
The KonText API requires a two-step process to initialize parallel (aligned) searches correctly when requested via JSON. This MCP server automatically handles this by:
1. Initializing the search on the primary corpus.
2. Immediately calling the view endpoint with alignment parameters.
This ensures that the LLM always receives the correctly aligned data and a working browser link.

## Contact
**Jan Švec** <honzas@fav.zcu.cz>  
Department of Cybernetics  
University of West Bohemia in Pilsen  

## Credits & License
This project is an independent MCP implementation. The underlying service is provided by [LINDAT/CLARIAH-CZ](https://lindat.cz/). Please respect their [Terms of Service](https://lindat.mff.cuni.cz/en/terms-of-use) when using the API.

License: MIT
