import json
import re
from importlib.resources import files


def search_knowledge(query: str, limit: int = 3) -> dict:
    """Search the bundled sample corpus with transparent keyword matching."""
    documents = json.loads(
        files("agent_app").joinpath("data/knowledge.json").read_text(encoding="utf-8")
    )
    terms = set(re.findall(r"\w+", query.casefold()))
    scored = []
    for document in documents:
        searchable = f"{document['title']} {document['text']} {' '.join(document['keywords'])}"
        words = set(re.findall(r"\w+", searchable.casefold()))
        score = len(terms & words)
        if score:
            scored.append((score, document))
    scored.sort(key=lambda item: (-item[0], item[1]["id"]))
    return {"matches": [doc for _, doc in scored[:limit]], "source": "bundled_demo_corpus"}
