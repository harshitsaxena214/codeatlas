"""
GitHub GraphQL API client for fetching Discussions.
Discussions are NOT available via the REST API, so we use GraphQL.
"""
import logging
import httpx
from typing import Any

logger = logging.getLogger(__name__)

GITHUB_GRAPHQL_URL = "https://api.github.com/graphql"

DISCUSSIONS_QUERY = """
query GetDiscussions($owner: String!, $name: String!, $first: Int!, $after: String) {
  repository(owner: $owner, name: $name) {
    discussions(first: $first, after: $after, orderBy: {field: UPDATED_AT, direction: DESC}) {
      pageInfo {
        hasNextPage
        endCursor
      }
      nodes {
        number
        title
        body
        url
        createdAt
        updatedAt
        author {
          login
        }
        category {
          name
        }
        labels(first: 10) {
          nodes {
            name
          }
        }
        comments(first: 20) {
          nodes {
            body
            createdAt
            author {
              login
            }
          }
        }
        answerChosenAt
        answer {
          body
          createdAt
          author {
            login
          }
        }
      }
    }
  }
}
"""


async def fetch_discussions_graphql(
    owner: str,
    name: str,
    token: str,
    limit: int = 200,
) -> list[dict[str, Any]]:
    """
    Fetch GitHub Discussions using the GraphQL API.
    Handles pagination automatically.
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    discussions = []
    cursor = None
    page_size = min(limit, 50)  # GraphQL max per page

    async with httpx.AsyncClient(timeout=30.0) as client:
        while len(discussions) < limit:
            remaining = limit - len(discussions)
            fetch_count = min(page_size, remaining)

            variables = {
                "owner": owner,
                "name": name,
                "first": fetch_count,
                "after": cursor,
            }

            try:
                response = await client.post(
                    GITHUB_GRAPHQL_URL,
                    json={"query": DISCUSSIONS_QUERY, "variables": variables},
                    headers=headers,
                )
                response.raise_for_status()
                data = response.json()

                if "errors" in data:
                    logger.warning(f"GraphQL errors: {data['errors']}")
                    break

                repo_data = data.get("data", {}).get("repository")
                if not repo_data or not repo_data.get("discussions"):
                    logger.info(f"No discussions found for {owner}/{name}")
                    break

                discussions_data = repo_data["discussions"]
                nodes = discussions_data.get("nodes", [])
                page_info = discussions_data.get("pageInfo", {})

                for node in nodes:
                    if node is None:
                        continue
                    discussion = {
                        "number": node["number"],
                        "title": node["title"],
                        "body": node.get("body", ""),
                        "url": node["url"],
                        "author": node["author"]["login"] if node.get("author") else "unknown",
                        "category": node["category"]["name"] if node.get("category") else "general",
                        "labels": [l["name"] for l in node.get("labels", {}).get("nodes", [])],
                        "created_at": node.get("createdAt"),
                        "updated_at": node.get("updatedAt"),
                        "comments": [
                            {
                                "author": c["author"]["login"] if c.get("author") else "unknown",
                                "body": c.get("body", ""),
                                "created_at": c.get("createdAt"),
                            }
                            for c in node.get("comments", {}).get("nodes", [])
                            if c is not None
                        ],
                        "has_answer": node.get("answerChosenAt") is not None,
                        "answer": {
                            "author": node["answer"]["author"]["login"] if node.get("answer", {}).get("author") else "unknown",
                            "body": node["answer"].get("body", ""),
                            "created_at": node["answer"].get("createdAt"),
                        } if node.get("answer") else None,
                    }
                    discussions.append(discussion)

                if not page_info.get("hasNextPage"):
                    break
                cursor = page_info.get("endCursor")

            except httpx.HTTPError as e:
                logger.error(f"Failed to fetch discussions: {e}")
                break

    return discussions
