import os
import logging
import httpx
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
load_dotenv()


logger = logging.getLogger(__name__)

# Initialize FastMCP
mcp = FastMCP("tech_news")

# Load API URL and API Key from environment variables
URL = os.getenv("TAVILY_API_URL")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")


@mcp.tool()
async def get_articles(query: str):
    """
    Get articles and summarize them.

    Args:
        query (str): The query to search for articles.

    """
    payload = {
        "query": query,
        "topic": "news",  # "general"
        "search_depth": "advanced",
        "chunks_per_source": 3,
        "max_results": 3,
        "days": 7,
        "include_answer": True,
        "include_raw_content": False,
        "include_images": False,
        "include_image_descriptions": False,
        "include_domains": [
            "https://arstechnica.com",
            "https://techcrunch.com",
        ],
    }
    headers = {
        "Authorization": f"Bearer {TAVILY_API_KEY}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(URL, json=payload, headers=headers, timeout=30.0)
            response.raise_for_status()
            logger.info("Status code: %s", response.status_code)
            return response.text
        except httpx.RequestError as exc:
            logger.error("Request error: %s", exc)
            return None
        except httpx.HTTPStatusError as exc:
            logger.error("HTTP error: %s - %s", exc.response.status_code, exc.response.text)
            return None


if __name__ == "__main__":
    mcp.run(transport="stdio")