# File Definition: domainCategories.json

The `domainCategories.json` file is a JSON object that serves as a comprehensive source of truth for classifying different applications and data sources by their primary domain of operation. The file has the following structure:

```json
{
  "[Category Name]": ["Example 1", "Example 2", "Example 3", ...],
  "[Category Name]": ["Example 1", "Example 2", "Example 3", ...],
  ...
}
```

## Key Technical Details:

*   **Data Type:** JSON (JavaScript Object Notation)
*   **Root Element:** JSON object (dictionary)
*   **Keys:** String representing the name of a software category (e.g., "Development", "Social", "Finance"). The keys are alphabetized.
*   **Values:** JSON array (list) of strings. Each string represents an example of a software application or API that falls under the category specified by the key.
*   **Purpose:** To provide a structured and comprehensive list of software categories and examples for use in classifying and analyzing different applications and data sources.
*   **Intended Use:** This file is intended to be used as a source of truth for other agents in the system, providing a consistent and reliable way to categorize software and APIs.