#!/usr/bin/env python3
"""
Debug script to see n8n page structure.
"""

import asyncio
import sys

async def debug_page():
    from playwright.async_api import async_playwright
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            print("Navigating to n8n...")
            await page.goto("http://localhost:5678/editor", wait_until="networkidle", timeout=60000)
            
            # Wait a bit for page to load
            await page.wait_for_timeout(5000)
            
            # Get page content
            content = await page.content()
            print("=== PAGE TITLE ===")
            print(await page.title())
            print("\n=== PAGE URL ===")
            print(page.url)
            print("\n=== FIRST 5000 CHARS OF CONTENT ===")
            print(content[:5000])
            
            # Also check for any data-test-id attributes
            import re
            test_ids = re.findall(r'data-test-id="([^"]+)"', content)
            print("\n=== ALL data-test-id ATTRIBUTES ===")
            for tid in sorted(set(test_ids)):
                print(f"  {tid}")
                
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_page())