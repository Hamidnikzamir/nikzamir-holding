#!/usr/bin/env python3
"""
Debug script to check the /setup page after owner creation.
"""

import asyncio
import sys

if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer)
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer)

async def debug_page():
    from playwright.async_api import async_playwright
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            print("Navigating to n8n setup page...")
            await page.goto("http://localhost:5678/setup", wait_until="networkidle", timeout=60000)
            await page.wait_for_timeout(5000)
            
            print(f"Page URL: {page.url}")
            print(f"Page title: {await page.title()}")
            
            content = await page.content()
            print(f"\nContent length: {len(content)}")
            
            # Check for form elements
            import re
            inputs = re.findall(r'<input[^>]*>', content)
            print(f"\n=== INPUT ELEMENTS ({len(inputs)}) ===")
            for inp in inputs[:20]:
                print(f"  {inp}")
                
            buttons = re.findall(r'<button[^>]*>[^<]*</button>', content)
            print(f"\n=== BUTTON ELEMENTS ({len(buttons)}) ===")
            for btn in buttons[:20]:
                print(f"  {btn}")
                
            # Check for links
            links = re.findall(r'<a[^>]*>[^<]*</a>', content)
            print(f"\n=== LINK ELEMENTS ({len(links)}) ===")
            for link in links[:30]:
                print(f"  {link}")
                
            # Check for specific text
            if "API" in content:
                print("\n=== Found 'API' in content ===")
            if "Key" in content:
                print("=== Found 'Key' in content ===")
            if "Workflows" in content:
                print("=== Found 'Workflows' in content ===")
            if "Settings" in content:
                print("=== Found 'Settings' in content ===")
                
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_page())