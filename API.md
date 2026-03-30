# KonText API Technical Reference

This document provides a detailed overview of the KonText corpus query engine API as discovered during the development of this MCP agent. KonText is based on NoSketch Engine but has specific LINDAT extensions and unique behaviors.

## Base URL
The API base URL used for all endpoints is:
`https://lindat.mff.cuni.cz/services/kontext`

---

## Core Concepts

### 1. Persistence ID (`q`)
Most analytical operations in KonText (frequency, collocations, filtering) do not take search parameters directly. Instead, they require a **persistence ID** (query ID or cache key), typically passed via the `q` parameter.
- **Format**: Often starts with a tilde, e.g., `~xt4TX5dCVJ16`.
- **Source**: Obtained from the `Q` field (list) or `conc_persistence_op_id` (string) in the response of a search operation (`/first`).
- **Persistence**: These IDs are temporary and expire after a period of inactivity on the server.

### 2. Format Parameter
For programmatic access, almost every endpoint requires:
`format=json`

---

## Primary Endpoints

### 1. Corpora Discovery
- **`corpora/ajax_list_corpora`**: Returns a paginated list of available corpora.
  - `query`: Use `+current` for latest versions, `+parallel` for parallel corpora.
  - `sortBySize`: Can be set to `name` or `size`.
- **`corpora/ajax_get_corp_details`**: Returns metadata about a specific corpus.
  - `corpname`: The internal ID (e.g., `czeng_10_en_a`).
  - **Returns**: Available attributes (`word`, `lemma`, `tag`), structures (`s`, `doc`), and description.

### 2. Search & Concordance
- **`/first`**: Initial search entry point.
  - `corpname`: Target corpus.
  - `queryselector`: `iqueryrow` (basic/regex) or `cqlrow` (CQL).
  - `iquery` / `cql`: The actual search string.
- **`/view`**: Used to paginate or change the view mode of an existing search.
  - `q`: The persistence ID.
  - `fromp`: Page number (1-based).
  - `pagesize`: Lines per page.

### 3. Parallel Corpora (Alignment)
**CRITICAL DISCOVERY**: Initializing a parallel search with alignment parameters (`align=CORPUS_ID&viewmode=align`) directly via a JSON `/first` request often fails with a "Failed to process your request" error.

**Reliable Flow**:
1. Call `/first` with the primary corpus and query only (to get the `q`).
2. Call `/view` using the `q` and adding the alignment parameters:
   - `align=CORPUS_ID`
   - `viewmode=align`
   - Language-specific filters (optional): `pcq_pos_neg_CORPUS_ID=pos&include_empty_CORPUS_ID=0`.

### 4. Analytical Tools
All these require a valid `q` from a previous search.
- **`/freqs`**: Frequency distribution.
  - `ml1attr`: The attribute to group by (e.g., `lemma`).
  - `ml1ctx`: Context (usually `0` for the hit itself).
- **`/coll`**: Collocation analysis.
  - `cattr`: Attribute to analyze.
  - `cfromw` / `ctow`: Window size (e.g., `-5` to `5`).
  - `csortfn`: Statistical measure (`d` for log-Dice, `t` for T-score, `m` for MI).
- **`/filter`**: Sub-filtering an existing concordance.
  - `pnfilter`: `p` (positive/keep) or `n` (negative/remove).
  - `query`: The filter expression.

### 5. Utilities
- **`/fullref`**: Get hit metadata.
  - `pos`: The `toknum` (token number) of the hit.
- **`/save`**: Generate export files.
  - `saveformat`: `text`, `csv`, `xml`, `xlsx`.
  - Generates a file download stream.

---

## Response Structure (Common Fields)

- `Lines`: Array of concordance lines. Each contains:
  - `Left`: Array of tokens before the hit.
  - `Kwic`: Array of tokens comprising the hit itself.
  - `Right`: Array of tokens after the hit.
  - `toknum`: Unique token identifier for `get_hit_details`.
  - `ref`: Citation/source ID for that line.
- `concsize`: Total number of occurrences found.
- `fullsize`: Total size of the corpus.
- `Pagination`: Object containing `lastPage`, `nextPage`, etc.

---

## Error Handling
- **Status Codes**: Usually returns `200 OK` even for errors, with the error message inside the JSON.
- **`messages`**: An array of `[type, text]` pairs. Look for `["error", "..."]`.
- **Common Errors**:
  - `Failed to process your request`: Often caused by illegal parameter combinations (like `align` in `/first` JSON) or an expired `q`.
  - `No such corpus`: Invalid `corpname`.
