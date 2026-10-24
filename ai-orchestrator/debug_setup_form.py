#!/usr/bin/env python3
"""
Debug script to inspect the setup page form structure
"""

import asyncio
import sys
from pathlib import Path

# Fix encoding for Windows
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer)
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer)

async def debug_setup_form():
    from playwright.async_api import async_playwright
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            print("Navigating to /setup page...")
            await page.goto("http://localhost:5678/setup", wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(3000)
            
            print(f"Current URL: {page.url}")
            
            # Get all form elements
            print("\n=== All input elements ===")
            inputs = await page.query_selector_all('input')
            for i, inp in enumerate(inputs):
                name = await inp.get_attribute('name')
                type_attr = await inp.get_attribute('type')
                placeholder = await inp.get_attribute('placeholder')
                id_attr = await inp.get_attribute('id')
                print(f"  Input {i}: name={name}, type={type_attr}, placeholder={placeholder}, id={id_attr}")
            
            print("\n=== All button elements ===")
            buttons = await page.query_selector_all('button')
            for i, btn in enumerate(buttons):
                text = await btn.inner_text()
                type_attr = await btn.get_attribute('type')
                class_attr = await btn.get_attribute('class')
                print(f"  Button {i}: text='{text[:50]}', type={type_attr}, class={class_attr}")
            
            print("\n=== All link elements ===")
            links = await page.query_selector_all('a')
            for i, link in enumerate(links):
                text = await link.inner_text()
                href = await link.get_attribute('href')
                print(f"  Link {i}: text='{text[:50]}', href={href}")
            
            print("\n=== All form elements ===")
            forms = await page.query_selector_all('form')
            for i, form in enumerate(forms):
                action = await form.get_attribute('action')
                method = await form.get_attribute('method')
                print(f"  Form {i}: action={action}, method={method}")
            
            # Save page content for analysis
            content = await page.content()
            with open("setup_page_debug.html", "w", encoding="utf-8") as f:
                f.write(content)
            print("\nSaved setup page content to setup_page_debug.html")
            
            # Keep browser open for inspection
            await page.wait_for_timeout(5000)
            
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_setup_form())