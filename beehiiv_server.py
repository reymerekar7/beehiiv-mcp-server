# beehiiv_server.py

from typing import Any, Optional
import os
import httpx
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

load_dotenv()

mcp = FastMCP("beehiiv-mcp-server")

BEEHIIV_API_KEY = os.getenv("BEEHIIV_API_KEY")
BASE_URL = "https://api.beehiiv.com/v2"
publication_id = os.getenv("BEEHIIV_PUBLICATION_ID")

async def beehiiv_request(
    method: str,
    path: str,
    params: Optional[dict[str, Any]] = None,
    json_body: Optional[dict[str, Any]] = None
) -> Optional[dict[str, Any]]:
    """
    Helper to call the beehiiv API v2.

    Args:
        method: HTTP method (GET, POST, etc.)
        path:   API path (e.g. '/publications')
        params: Query parameters
        json_body: Request JSON body
    """
    headers = {
        "Authorization": f"Bearer {BEEHIIV_API_KEY}",
        "Content-Type": "application/json"
    }
    url = f"{BASE_URL}{path}"
    async with httpx.AsyncClient() as client:
        try:
            response = await client.request(
                method, url,
                headers=headers,
                params=params,
                json=json_body,
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            return {"error": str(e)}

@mcp.tool()
async def list_publications() -> str:
    """
    List all publications accessible with this API key.
    """
    data = await beehiiv_request("GET", "/publications")
    if not data or "data" not in data:
        return "Failed to fetch publications."
    pubs = data["data"]
    return "\n".join(f"{p['id']}: {p['name']}" for p in pubs)

@mcp.tool()
async def list_posts(publication_id: str) -> str:
    """
    List all posts for a given publication.

    Args:
        publication_id: e.g. 'pub_00000000-0000-0000-0000-000000000000'
    """
    params = {
        "order_by": "publish_date",
        "direction": "desc",
        "limit": 5,
        "status": "confirmed"
    }
    path = f"/publications/{publication_id}/posts"
    data = await beehiiv_request("GET", path, params=params)
    if not data or "data" not in data:
        return f"API error: {data.get('error', 'Unknown error')}"
    return "\n".join(f"{p['id']}: {p['title']}" for p in data["data"])

@mcp.tool()
async def get_post(publication_id: str, post_id: str) -> str:
    """
    Retrieve a single post by ID.

    Args:
        publication_id: ID of the publication
        post_id:        ID of the post
    """
    path = f"/publications/{publication_id}/posts/{post_id}"
    data = await beehiiv_request("GET", path)
    if not data or "data" not in data:
        return "Failed to fetch the post."
    post = data["data"]
    return (
        f"Title: {post.get('title')}\n"
        f"Subtitle: {post.get('subtitle')}\n"
        f"URL: {post.get('web_url')}\n"
        f"Status: {post.get('status')}\n"
        f"Authors: {post.get('authors')}"
    )

if __name__ == "__main__":
    # Launch the MCP server
    mcp.run()



