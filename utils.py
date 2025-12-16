import re


def clean_query(query: str) -> str:
    """
    Cleans the AI-generated SQL query by removing code block markers and extra whitespace.
    """
    # Remove code block markers if present
    query = re.sub(r"^```sql\s*|^```", "", query, flags=re.IGNORECASE)
    query = re.sub(r"```$", "", query)
    # Remove leading/trailing whitespace
    return query.strip()