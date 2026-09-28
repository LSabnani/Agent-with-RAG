import os
import csv
import random

DATA_DIR = os.environ.get("DATA_DIR", os.path.join(os.path.dirname(os.path.dirname(__file__)), "data"))
CSV_PATH = os.path.join(DATA_DIR, "employee_database.csv")

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

def seed_employee_data(csv_path=CSV_PATH, overwrite=False):
    """Seed 30 employee records in employee_database.csv if not exists."""
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    if os.path.exists(csv_path) and not overwrite:
        # Check if already populated
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            rows = list(reader)
            if len(rows) >= 31: # header + 30 records
                return len(rows) - 1

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["name", "city", "country", "job_title"])
        writer.writeheader()
        for emp in SAMPLE_EMPLOYEES[:30]:
            writer.writerow(emp)
    return len(SAMPLE_EMPLOYEES[:30])

def search_employees(keyword="", field="", csv_path=CSV_PATH):
    """Search employee records by name, city, country, or job title."""
    if not os.path.exists(csv_path):
        seed_employee_data(csv_path)

    results = []
    clean_kw = (keyword or "").strip().lower()
    clean_field = (field or "").strip().lower()

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if not clean_kw:
                results.append(row)
                continue
            if clean_field in ["name", "city", "country", "job_title"]:
                if clean_kw in row.get(clean_field, "").lower():
                    results.append(row)
            else:
                # Search all fields
                if (clean_kw in row.get("name", "").lower() or
                    clean_kw in row.get("city", "").lower() or
                    clean_kw in row.get("country", "").lower() or
                    clean_kw in row.get("job_title", "").lower()):
                    results.append(row)
    return results

if __name__ == "__main__":
    count = seed_employee_data(overwrite=True)
    print(f"Seeded {count} employees into {CSV_PATH}")
