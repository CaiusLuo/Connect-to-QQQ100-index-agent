import os
from crewai.tools import tool
from tavily import TavilyClient


@tool("search_news_tool")
def search_news_tool(query: str) -> str:
    """Search for news articles related to the NASDAQ 100 index (QQQ)"""

    search_depth = "advanced"
    include_domains = [
        "reuters.com",
        "bloomberg.com",
        "cnbc.com",
        "wsj.com",
    ]

    client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

    try:
        response = client.search(
            query=query,
            search_depth=search_depth,
            include_domains=include_domains,
            topic="news",
        )

        results = []
        if "results" in response:
            for item in response["results"]:
                title = item.get("title", "No Title")
                url = item.get("url", "#")
                content = item.get("content", "No Content")
                results.append(f"Title: {title}\nLink: {url}\nSnippet: {content}\n---")

        return "\n".join(results) if results else "No relevant news found."

    except Exception as e:
        return f"Error performing news search: {str(e)}"
