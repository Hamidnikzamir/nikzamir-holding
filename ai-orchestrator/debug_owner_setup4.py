#!/usr/bin/env python3
"""
Debug script to wait for owner setup form elements.
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
            
            # Wait for form elements to appear
            print("Waiting for form to render...")
            
            # Try to wait for input elements
            try:
                await page.wait_for_selector('input[type="email"]', timeout=30000)
                print("Found email input!")
            except:
                print("No email input found")
            
            try:
                await page.wait_for_selector('input[type="password"]', timeout=10000)
                print("Found password input!")
            except:
                print("No password input found")
            
            try:
                await page.wait_for_selector('button[type="submit"]', timeout=10000)
                print("Found submit button!")
            except:
                print("No submit button found")
                
            # Get final content
            content = await page.content()
            print("\n=== PAGE CONTENT (first 30000 chars) ===")
            print(content[:30000])
            
            # Check for specific text
            if "owner" in content.lower() or "setup" in content.lower() or "create" in content.lower():
                print("\n=== Owner/Setup related text found ===")
                
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_page())