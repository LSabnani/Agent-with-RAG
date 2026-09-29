---
name: person-information-skill
description: Search and lookup personal directory records including employee name, city, country, or job title from the company registry CSV file using a list of search texts. Use this skill whenever the user asks about people, personnel, employees, job titles, or someone's location.
triggers:
  - who is [person]
  - where does [person] live
  - what is [person]'s job title
  - find employees in [city]
  - list staff in [country]
  - who works as [job title]
  - lookup person [name]
---

# Person Information Skill

## Description
Provides lookup and search capabilities over the personnel database `registry.csv`. Enables searching records by name, city, country, or job title with exact or partial matching across a list of search texts (or a single search term). Searches for all queried items and returns a combined, deduplicated list of matching entries.

## SOP & Tool Execution
When the user asks about an employee or personnel record:
1. Determine the search `keywords` (a list of texts/strings e.g. names, cities, countries, or job titles) and the optional `field` (choices: `name`, `city`, `country`, `job_title`, or `all` to search across all fields).
2. Invoke `person_search.query_person_registry`:
```json
{
  "tool": "person_search.query_person_registry",
  "arguments": {
    "keywords": ["Lucas Dubois", "Berlin"],
    "field": "all"
  }
}
```
3. Format the returned records clearly showing Name, Job Title, City, and Country for all matched entries.
