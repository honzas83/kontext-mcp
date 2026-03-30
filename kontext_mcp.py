import asyncio
from typing import Annotated, Optional, List, Dict, Any
import httpx
from mcp.server.fastmcp import FastMCP

# Create an MCP server
mcp = FastMCP("KonText")

BASE_URL = "https://lindat.mff.cuni.cz/services/kontext"

class KonTextClient:
    def __init__(self, base_url: str):
        self.base_url = base_url

    async def _get(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        # Filter out None values
        params = {k: v for k, v in params.items() if v is not None}
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{self.base_url}/{endpoint}", params=params)
            response.raise_for_status()
            return response.json()

    def get_web_url(self, endpoint: str, params: Dict[str, Any]) -> str:
        """Constructs a URL for viewing the results in a browser."""
        web_params = {k: v for k, v in params.items() if k != "format" and v is not None}
        query_string = "&".join([f"{k}={v}" for k, v in web_params.items()])
        return f"{self.base_url}/{endpoint}?{query_string}"

client = KonTextClient(BASE_URL)

@mcp.tool()
async def list_corpora(
    query: Annotated[str, "Filter query for corpora (e.g., '+current' for current versions, '+parallel' for parallel corpora)"] = "+current",
    offset: Annotated[int, "Offset for pagination of the corpora list"] = 0
) -> Dict[str, Any]:
    """
    List available linguistic corpora. Use this to find the 'id' (corpname) of a corpus to query.
    """
    params = {
        "query": query,
        "offset": offset,
        "requestable": 1,
        "sortBySize": "name"
    }
    return await client._get("corpora/ajax_list_corpora", params)

@mcp.tool()
async def get_corpus_details(
    corpname: Annotated[str, "The internal ID of the corpus (e.g., 'czeng_10_cs_a')"]
) -> Dict[str, Any]:
    """
    Get detailed information about a corpus, including available attributes (word, lemma, tag), 
    structural levels (document, sentence), and its description.
    """
    return await client._get("corpora/ajax_get_corp_details", {"corpname": corpname})

@mcp.tool()
async def search_concordance(
    corpname: Annotated[str, "Internal ID of the corpus to search in"],
    query: Annotated[str, "The word, phrase, or CQL expression to search for"],
    queryselector: Annotated[str, "Type of search: 'iqueryrow' for basic search, 'cqlrow' for Corpus Query Language"] = "iqueryrow",
    align: Annotated[Optional[str], "Internal ID of the aligned corpus (for parallel corpora, e.g., 'czeng_10_cs_a')"] = None
) -> Dict[str, Any]:
    """
    Perform a search in a corpus and return the first page of occurrences (concordance).
    Returns a 'conc_persistence_op_id' (prefixed with ~) which is required for analytical tools.
    If 'align' is provided, it performs a parallel corpus search.
    """
    # Step 1: Initial search (WITHOUT alignment to avoid API error)
    first_params = {
        "corpname": corpname,
        "queryselector": queryselector,
        "iquery": query if queryselector == "iqueryrow" else None,
        "cql": query if queryselector == "cqlrow" else None,
        "format": "json"
    }
    data = await client._get("first", first_params)
    
    # Get the persistence ID (q)
    q = data.get("Q", [None])[0] or data.get("conc_persistence_op_id")
    
    if align and q:
        # Step 2: If alignment requested, call 'view' with the persistence ID
        view_params = {
            "q": q,
            "corpname": corpname,
            "align": align,
            "viewmode": "align",
            "format": "json"
        }
        data = await client._get("view", view_params)
        data["web_url"] = client.get_web_url("view", view_params)
    else:
        # For single corpus, use the 'first' result and generate appropriate web_url
        data["web_url"] = client.get_web_url("first", first_params)
        
    return data

@mcp.tool()
async def view_concordance(
    q: Annotated[str, "The concordance persistence ID (cache key) starting with ~, obtained from search results"],
    corpname: Annotated[str, "Internal ID of the corpus"],
    page: Annotated[int, "Page number to view (1-based)"] = 1,
    pagesize: Annotated[int, "Number of concordance lines per page"] = 40,
    align: Annotated[Optional[str], "Internal ID of the aligned corpus (for parallel corpora)"] = None
) -> Dict[str, Any]:
    """
    Navigate through pages of an existing concordance result.
    """
    params = {
        "q": q,
        "corpname": corpname,
        "fromp": page,
        "pagesize": pagesize,
        "align": align,
        "viewmode": "align" if align else None,
        "format": "json"
    }
    data = await client._get("view", params)
    data["web_url"] = client.get_web_url("view", params)
    return data

@mcp.tool()
async def get_hit_details(
    corpname: Annotated[str, "Internal ID of the corpus"],
    pos: Annotated[int, "The token position (toknum) of the hit, found in concordance line data"]
) -> Dict[str, Any]:
    """
    Get detailed metadata (e.g., document ID, category, author) for a specific occurrence in the search results.
    """
    return await client._get("fullref", {"corpname": corpname, "pos": pos, "format": "json"})

@mcp.tool()
async def get_frequency(
    q: Annotated[str, "Concordance persistence ID (~ID)"],
    corpname: Annotated[str, "Internal ID of the corpus"],
    attr: Annotated[str, "Attribute to group by (e.g., 'word', 'lemma', 'tag', 'doc.id')"] = "word",
    ctx: Annotated[int, "Context position relative to hit (0 for the hit itself)"] = 0
) -> Dict[str, Any]:
    """
    Calculate the frequency distribution of words/attributes for an existing search result.
    """
    params = {
        "q": q,
        "corpname": corpname,
        "ml1attr": attr,
        "ml1ctx": ctx,
        "format": "json"
    }
    return await client._get("freqs", params)

@mcp.tool()
async def get_collocations(
    q: Annotated[str, "Concordance persistence ID (~ID)"],
    corpname: Annotated[str, "Internal ID of the corpus"],
    attr: Annotated[str, "Attribute to analyze (e.g., 'word', 'lemma')"] = "word",
    cfromw: Annotated[int, "Left boundary of the collocation window (e.g., -5)"] = -5,
    ctow: Annotated[int, "Right boundary of the collocation window (e.g., 5)"] = 5,
    cminfreq: Annotated[int, "Minimum frequency of the collocate in the window"] = 5,
    cminbgr: Annotated[int, "Minimum background frequency/statistical threshold"] = 3
) -> Dict[str, Any]:
    """
    Identify frequently co-occurring words (collocations) around the search hits.
    """
    params = {
        "q": q,
        "corpname": corpname,
        "cattr": attr,
        "cfromw": cfromw,
        "ctow": ctow,
        "cminfreq": cminfreq,
        "cminbgr": cminbgr,
        "format": "json"
    }
    return await client._get("coll", params)

@mcp.tool()
async def filter_concordance(
    q: Annotated[str, "Concordance persistence ID (~ID)"],
    corpname: Annotated[str, "Internal ID of the corpus"],
    query: Annotated[str, "Filter expression (word or CQL)"],
    pnfilter: Annotated[str, "Filter type: 'p' for positive (keep matches), 'n' for negative (remove matches)"] = "p",
    filtpos: Annotated[int, "Starting position of the filter window"] = 0,
    filfpos: Annotated[int, "Ending position of the filter window"] = 0
) -> Dict[str, Any]:
    """
    Refine an existing search by applying an additional filter to the occurrences.
    """
    params = {
        "q": q,
        "corpname": corpname,
        "query": query,
        "pnfilter": pnfilter,
        "filtpos": filtpos,
        "filfpos": filfpos,
        "format": "json"
    }
    return await client._get("filter", params)

@mcp.tool()
async def get_save_url(
    q: Annotated[str, "Concordance persistence ID (~ID)"],
    corpname: Annotated[str, "Internal ID of the corpus"],
    saveformat: Annotated[str, "Export format: 'text', 'csv', 'xml', or 'xlsx'"] = "text"
) -> str:
    """
    Generate a direct download URL to export and save the concordance results.
    """
    params = {"q": q, "corpname": corpname, "saveformat": saveformat}
    return client.get_web_url("save", params)

@mcp.tool()
async def list_published_subcorpora() -> Dict[str, Any]:
    """
    List all publicly available subcorpora. These IDs can be used as 'corpname' in search queries.
    """
    return await client._get("subcorpus/list_published", {"format": "json"})

if __name__ == "__main__":
    mcp.run()
