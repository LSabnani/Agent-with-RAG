import os
import csv
from typing import Dict, Any, List, Optional, Union, Iterable

DATA_DIR = os.environ.get("DATA_DIR", os.path.join(os.path.dirname(os.path.dirname(__file__)), "data"))
CSV_PATH = os.path.join(DATA_DIR, "employee_database.csv")
VALID_FIELDS = ["name", "city", "country", "job_title"]

SAMPLE_EMPLOYEES = [
    {"name": "Lucas Dubois", "city": "Paris", "country": "France", "job_title": "Senior AI Engineer"},
    {"name": "Elena Rostova", "city": "Berlin", "country": "Germany", "job_title": "Data Scientist"},
    {"name": "Kenji Takahashi", "city": "Tokyo", "country": "Japan", "job_title": "Machine Learning Architect"},
    {"name": "Sarah Jenkins", "city": "London", "country": "United Kingdom", "job_title": "Product Manager"},
    {"name": "Mateo Silva", "city": "Madrid", "country": "Spain", "job_title": "DevOps Engineer"},
    {"name": "Chloe Martin", "city": "Montreal", "country": "Canada", "job_title": "Frontend Developer"},
    {"name": "Liam O'Connor", "city": "Dublin", "country": "Ireland", "job_title": "Backend Developer"},
    {"name": "Priya Sharma", "city": "Bengaluru", "country": "India", "job_title": "Full Stack Engineer"},
    {"name": "Carlos Mendez", "city": "Mexico City", "country": "Mexico", "job_title": "Cloud Solutions Architect"},
    {"name": "Ananya Patel", "city": "Mumbai", "country": "India", "job_title": "QA Automation Engineer"},
    {"name": "Oliver Hansen", "city": "Copenhagen", "country": "Denmark", "job_title": "Site Reliability Engineer"},
    {"name": "Fatima Al-Mansoor", "city": "Dubai", "country": "United Arab Emirates", "job_title": "AI Ethics Officer"},
    {"name": "Dmitri Volkov", "city": "Warsaw", "country": "Poland", "job_title": "Security Analyst"},
    {"name": "Isabella Rossi", "city": "Rome", "country": "Italy", "job_title": "UX/UI Designer"},
    {"name": "Lars Lindqvist", "city": "Stockholm", "country": "Sweden", "job_title": "Infrastructure Architect"},
    {"name": "Hana Tanaka", "city": "Osaka", "country": "Japan", "job_title": "NLP Researcher"},
    {"name": "Benjamin Scott", "city": "Sydney", "country": "Australia", "job_title": "Engineering Manager"},
    {"name": "Camila Rodriguez", "city": "Buenos Aires", "country": "Argentina", "job_title": "Data Engineer"},
    {"name": "Noah Kim", "city": "Seoul", "country": "South Korea", "job_title": "Computer Vision Engineer"},
    {"name": "Mia De Vries", "city": "Amsterdam", "country": "Netherlands", "job_title": "Technical Writer"},
    {"name": "Gabriel Santos", "city": "Sao Paulo", "country": "Brazil", "job_title": "Database Administrator"},
    {"name": "Ingrid Berg", "city": "Oslo", "country": "Norway", "job_title": "Systems Analyst"},
    {"name": "Tariq Haddad", "city": "Cairo", "country": "Egypt", "job_title": "Research Scientist"},
    {"name": "Zoe Chen", "city": "Singapore", "country": "Singapore", "job_title": "Scrum Master"},
    {"name": "Alexander Weber", "city": "Zurich", "country": "Switzerland", "job_title": "Distributed Systems Engineer"},
    {"name": "Sophie Moreau", "city": "Lyon", "country": "France", "job_title": "Business Intelligence Lead"},
    {"name": "Marcus Aurelius Vance", "city": "Austin", "country": "United States", "job_title": "Principal Architect"},
    {"name": "Yuki Sato", "city": "Kyoto", "country": "Japan", "job_title": "Platform Engineer"},
    {"name": "Grace Hopper Nguyen", "city": "Hanoi", "country": "Vietnam", "job_title": "Compilers & Runtimes Engineer"},
    {"name": "David Alaba", "city": "Vienna", "country": "Austria", "job_title": "Mobile App Engineer"}
]

def seed_employee_data(csv_path: str = CSV_PATH, overwrite: bool = False) -> int:
    """Seed 30 employee records in employee_database.csv if not exists."""
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    if os.path.exists(csv_path) and not overwrite:
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            rows = list(reader)
            if len(rows) >= 31: # header + 30 records
                return len(rows) - 1

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=VALID_FIELDS)
        writer.writeheader()
        for emp in SAMPLE_EMPLOYEES[:30]:
            writer.writerow(emp)
    return len(SAMPLE_EMPLOYEES[:30])


def normalize_search_terms(keywords: Optional[Union[str, List[str], Iterable[str]]]) -> List[str]:
    """Normalize input search terms into a clean list of lowercased non-empty strings.
    
    Supports:
        - List or tuple of strings: ['Lucas Dubois', 'Paris']
        - Single string: 'Lucas Dubois'
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
    
    # Otherwise search across all fields
    return any(term in (v or "").lower() for v in row.values())


def filter_records(
    records: Iterable[Dict[str, str]],
    search_terms: List[str],
    field: str = ""
) -> List[Dict[str, str]]:
    """Filter records matching search terms.
    
    Searches for all the items in the text and returns a deduplicated list of
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


def search_employees(
    keywords: Optional[Union[str, List[str]]] = None,
    field: str = "",
    csv_path: str = CSV_PATH,
    keyword: Optional[Union[str, List[str]]] = None
) -> List[Dict[str, str]]:
    """Search employee records by a list of texts (or single text) across name, city, country, or job title.
    
    Args:
        keywords: List of texts or single text string to search for.
        field: Optional specific field ('name', 'city', 'country', 'job_title').
        csv_path: Path to employee CSV file.
        keyword: Backward-compatibility alias for keywords.
        
    Returns:
        List of deduplicated matching employee dictionaries.
    """
    if not os.path.exists(csv_path):
        seed_employee_data(csv_path)

    query_input = keywords if keywords is not None else keyword
    terms = normalize_search_terms(query_input)

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return filter_records(reader, terms, field=field)


def query_employees(
    keywords: Optional[Union[str, List[str]]] = None,
    field: str = "",
    csv_path: str = CSV_PATH,
    keyword: Optional[Union[str, List[str]]] = None
) -> Dict[str, Any]:
    """Execute search and return full structured response dictionary."""
    results = search_employees(keywords=keywords, field=field, csv_path=csv_path, keyword=keyword)
    query_input = keywords if keywords is not None else keyword
    return {
        "query": query_input,
        "field": (field or "all").strip().lower(),
        "count": len(results),
        "total_matches": len(results),
        "results": results,
        "status": "success"
    }


if __name__ == "__main__":
    count = seed_employee_data(overwrite=True)
    print(f"Seeded {count} employees into {CSV_PATH}")
    # Quick self-test with list of search terms
    test_terms = ["Lucas Dubois", "Berlin", "QA"]
    matches = search_employees(keywords=test_terms)
    print(f"Search for {test_terms} returned {len(matches)} results:")
    for m in matches:
        print(f" - {m['name']} ({m['job_title']}) in {m['city']}, {m['country']}")
