"""Research using AWS AgentCore Web Search, preserving retrieved evidence."""
import os
from urllib.parse import urlsplit
from pydantic import BaseModel, Field
from config import aws_client, positive_int


class SearchSource(BaseModel):
    title: str = Field(description="Title of the source webpage.")
    url: str = Field(description="Actual retrieved webpage URL.")
    finding: str = Field(description="Evidence extracted by AWS Web Search.")


class SearchResult(BaseModel):
    query: str
    findings: list[str]
    sources: list[SearchSource]


class SearchAgent:
    def run(self, query: str) -> SearchResult:
        query = query.strip()
        if not 1 <= len(query) <= 200:
            raise ValueError("AWS web search queries must contain 1 to 200 characters.")
        client = aws_client("bedrock-agentcore", os.getenv("AWS_SEARCH_REGION") or None)
        if not hasattr(client, "invoke_web_search"):
            raise RuntimeError("This Boto3 version does not support AgentCore Web Search. Run uv sync --upgrade-package boto3 --upgrade-package botocore.")
        response = client.invoke_web_search(
            webSearchId="web-search.v1", searchQuery=query,
            maxResults=positive_int("AWS_SEARCH_MAX_RESULTS", 5, 25),
        )
        sources = []
        seen = set()
        for item in response.get("results", []):
            url = (item.get("url") or "").strip()
            text = (item.get("text") or "").strip()
            parsed = urlsplit(url)
            if parsed.scheme not in {"https", "http"} or not parsed.netloc or not text or url in seen:
                continue
            seen.add(url)
            sources.append(SearchSource(title=item.get("title") or url, url=url, finding=text))
        return SearchResult(query=query, findings=[source.finding for source in sources], sources=sources)


def create_search_agent() -> SearchAgent:
    return SearchAgent()
