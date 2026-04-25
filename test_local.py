import asyncio
import os
import sys

# Add backend dir to path
sys.path.append(os.path.abspath('backend'))

from backend.mcp_server import run_weekly_pulse, WeeklyPulseRequest

async def main():
    req = WeeklyPulseRequest(app_name="Kuvera", weeks=8)
    try:
        res = await run_weekly_pulse(req)
        print("Success:", res)
    except Exception as e:
        print("Error:", e)

asyncio.run(main())
