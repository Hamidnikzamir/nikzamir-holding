#!/usr/bin/env python3
"""
Debug script to see owner setup page with longer wait.
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
            print("Navigating to n8n owner setup...")
            await page.goto("http://localhost:5678/owner/setup", wait_until="networkidle", timeout=60000)
            
            # Wait longer for React to render
            print("Waiting for React to render...")
            await page.wait_for_timeout(15000)
            
            # Get page content
            content = await page.content()
            print("=== PAGE TITLE ===")
            print(await page.title())
            print("\n=== PAGE URL ===")
            print(page.url)
            print("\n=== FULL CONTENT (first 20000 chars) ===")
            print(content[:20000])
            
            # Check for form elements
            import re
            inputs = re.findall(r'<input[^>]*>', content)
            print("\n=== INPUT ELEMENTS ===")
            for inp in inputs:
                print(f"  {inp}")
                
            buttons = re.findall(r'<button[^>]*>[^<]*</button>', content)
            print("\n=== BUTTON ELEMENTS ===")
            for btn in buttons:
                print(f"  {btn}")
                
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_page())