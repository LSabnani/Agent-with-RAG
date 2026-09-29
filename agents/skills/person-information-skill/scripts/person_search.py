"""Tool to query person registry flat-file CSV."""
import os
import csv
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Iterable

REGISTRY_PATH = Path(__file__).resolve().parent.parent / "data" / "registry.csv"
VALID_FIELDS = ["name", "city", "country", "job_title"]


def normalize_search_terms(keywords: Optional[Union[str, List[str], Iterable[str]]]) -> List[str]:
    """Normalize input search terms into a clean list of lowercased non-empty strings.
    
    Accepts:
        - List of texts/strings: ['Lucas Dubois', 'Berlin']
        - Single text/string: 'Lucas Dubois'
        - None or empty string: []
    """
    if keywords is None:
        return []
    if isinstance(keywords, str):
        term = keywords.strip().lower()
        return [term] if term else []

    terms = []
    for item in keywords:
        if item is not None:
            clean = str(item).strip().lower()
            if clean and clean not in terms:
                terms.append(clean)
    return terms


def record_matches_term(row: Dict[str, str], term: str, field: str = "") -> bool:
    """Check if a single row matches a search term."""
    if not term:
        return True

    clean_field = (field or "").strip().lower()
    if clean_field in VALID_FIELDS:
        val = (row.get(clean_field) or "").lower()
        return term in val

    # Default: search across all fields
    return any(term in (v or "").lower() for v in row.values())


def filter_person_records(
    records: Iterable[Dict[str, str]],
    search_terms: List[str],
    field: str = ""
) -> List[Dict[str, str]]:
    """Filter records matching search terms.
    
    Searches for all items in the text and returns a deduplicated list of
    matching entries while preserving insertion order.
    """
    record_list = list(records)
    if not search_terms:
        return record_list

    matched_records: List[Dict[str, str]] = []
    seen_identities = set()

    for term in search_terms:
        for row in record_list:
            identity = (row.get("name", "").strip().lower(), row.get("job_title", "").strip().lower())
            if identity not in seen_identities and record_matches_term(row, term, field):
                seen_identities.add(identity)
                matched_records.append(row)

    return matched_records


def query_person_registry(
    keywords: Optional[Union[List[str], str]] = None,
    field: Optional[str] = None,
    keyword: Optional[Union[List[str], str]] = None,
    registry_path: Optional[Path] = None,
    **kwargs
) -> Dict[str, Any]:
    """Search person information in the CSV registry using a list of texts (or single text).
    
    Args:
        keywords: Search term or list of search terms (e.g. ['Lucas Dubois', 'Paris', 'Security Engineer']).
        field: Optional specific field ('name', 'city', 'country', 'job_title').
               If None or 'all', searches across all fields.
        keyword: Backward-compatible alias for keywords.
        registry_path: Optional override path to registry CSV.
               
    Returns:
        Dictionary with count, total_matches, results list, and status.
    """
    csv_file = registry_path or REGISTRY_PATH
    if not csv_file.exists():
        return {
            "error": f"Registry file not found at {csv_file}",
            "status": "error",
            "count": 0,
            "total_matches": 0,
            "results": []
        }

    query_input = keywords if keywords is not None else keyword
    clean_field = str(field).strip().lower() if field else "all"
    terms = normalize_search_terms(query_input)

    try:
        with open(csv_file, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            matches = filter_person_records(reader, terms, field=clean_field)

        return {
            "query": query_input,
            "field": clean_field,
            "count": len(matches),
            "total_matches": len(matches),
            "results": matches,
            "status": "success"
        }
    except Exception as e:
        return {
            "error": str(e),
            "status": "error",
            "count": 0,
            "total_matches": 0,
            "results": []
        }


# Direct alias
search_person = query_person_registry


if __name__ == "__main__":
    search_args = sys.argv[1:] if len(sys.argv) > 1 else ["Lucas Dubois", "Berlin"]
    print(f"Running person_search with terms: {search_args}")
    res = query_person_registry(keywords=search_args)
    print(f"Status: {res.get('status')}, Matches: {res.get('total_matches')}")
    for item in res.get("results", []):
        print(f" - {item.get('name')}: {item.get('job_title')}, {item.get('city')}, {item.get('country')}")
