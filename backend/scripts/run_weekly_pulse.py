import httpx
import asyncio
import sys
import logging

# Configure basic logging for the script
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("run_weekly_pulse")

async def trigger_pipeline():
    url = "http://localhost:8000/mcp/run-weekly-pulse"
    payload = {
        "app_name": "Kuvera",
        "weeks": 8
    }
    
    logger.info(f"Triggering Kuvera Weekly Pulse via MCP Server at {url}...")
    
    async with httpx.AsyncClient(timeout=600.0) as client:
        try:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            result = response.json()
            logger.info("Success! Pipeline execution result:")
            logger.info(result)
        except httpx.HTTPStatusError as e:
            logger.error(f"Server returned an error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            logger.error(f"Failed to connect to MCP Server: {e}")
            logger.info("Make sure the MCP server is running (python mcp_server.py)")

if __name__ == "__main__":
    asyncio.run(trigger_pipeline())
