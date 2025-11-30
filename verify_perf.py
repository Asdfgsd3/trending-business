import asyncio
import time
import os
import sys

# Ensure project root is in path
sys.path.insert(0, os.getcwd())

from app.main import app, refresh_trending, all_trending_scores, on_startup

async def verify_performance():
    # 0. Initialize app state
    print("Initializing app...")
    await on_startup()

    # 1. Trigger a refresh to populate cache
    print("Triggering refresh...")
    start_refresh = time.time()
    await refresh_trending()
    print(f"Refresh took {time.time() - start_refresh:.2f}s")
    
    # 2. Check if cache is populated
    from app.main import all_trending_scores
    print(f"Cache size: {len(all_trending_scores)}")
    if not all_trending_scores:
        print("ERROR: Cache is empty!")
        return

    # 3. Simulate API call to /api/trending/all
    from app.main import get_all_trending
    
    print("Calling get_all_trending...")
    start_req = time.time()
    response = await get_all_trending()
    duration = time.time() - start_req
    print(f"API call took {duration:.4f}s")
    
    if duration > 0.1:
        print("ERROR: API call took too long!")
    else:
        print("SUCCESS: API call was instant.")

if __name__ == "__main__":
    asyncio.run(verify_performance())
