#!/usr/bin/env python3
"""
Script to create n8n owner account and generate API key.
"""

import asyncio
import os
import json
import sys
from pathlib import Path

# Fix encoding for Windows
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer)
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer)

async def create_owner_and_api_key():
    from playwright.async_api import async_playwright
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            # Step 1: Create owner account
            print("Step 1: Creating owner account...")
            await page.goto("http://localhost:5678/setup", wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(3000)
            
            email = "admin@test.com"
            password = "testpassword123"
            
            # Step 1a: Fill email and click Next
            print("  Step 1a: Filling email...")
            await page.fill('input[name="email"]', email)
            await page.click('button:has-text("Next")')
            await page.wait_for_timeout(3000)
            print(f"  URL after email step: {page.url}")
            
            # Step 1b: Fill first name, last name, password
            print("  Step 1b: Filling name and password...")
            await page.fill('input[name="firstName"]', "Admin")
            await page.fill('input[name="lastName"]', "User")
            await page.fill('input[name="password"]', password)
            
            # Click Next/Create button
            await page.click('button:has-text("Next")')
            await page.wait_for_timeout(5000)
            print(f"  URL after name/password step: {page.url}")
            
            # Step 1c: Check if there's another step (template selection)
            if "setup" in page.url:
                print("  Step 1c: Skipping template selection...")
                # Try to click skip or next
                try:
                    await page.click('button:has-text("Skip")', timeout=3000)
                except:
                    try:
                        await page.click('button:has-text("Next")', timeout=3000)
                    except:
                        pass
                await page.wait_for_timeout(3000)
                print(f"  URL after template step: {page.url}")
            
            # Step 2: Navigate to settings to create API key
            print("\nStep 2: Creating API key...")
            await page.goto("http://localhost:5678/settings", wait_until="networkidle", timeout=60000)
            await page.wait_for_timeout(5000)
            
            print(f"Settings page URL: {page.url}")
            
            # Check if we need to login
            if "signin" in page.url:
                print("Redirected to signin, logging in...")
                await page.fill('input[type="email"]', email)
                await page.fill('input[type="password"]', password)
                await page.press('input[type="password"]', 'Enter')
                await page.wait_for_timeout(5000)
                await page.goto("http://localhost:5678/settings", wait_until="networkidle", timeout=60000)
                await page.wait_for_timeout(5000)
            
            print(f"Settings page URL after potential login: {page.url}")
            
            # Navigate to API keys tab
            print("Looking for API Keys tab...")
            
            # Try various selectors for the API keys section
            api_key_selectors = [
                'a:has-text("API Keys")',
                'button:has-text("API Keys")',
                '[data-test-id="api-keys"]',
                'a[href*="api-key"]',
                'text=API Keys',
            ]
            
            api_key_clicked = False
            for selector in api_key_selectors:
                try:
                    await page.click(selector, timeout=5000)
                    print(f"Clicked API Keys with selector: {selector}")
                    api_key_clicked = True
                    await page.wait_for_timeout(3000)
                    break
                except:
                    continue
            
            if not api_key_clicked:
                print("Could not find API Keys tab, checking page content...")
                content = await page.content()
                # Look for API key related text
                if "API" in content:
                    print("Found 'API' in content")
                if "Key" in content:
                    print("Found 'Key' in content")
            
            # Try to find and click "Create API Key" button
            print("Looking for Create API Key button...")
            create_selectors = [
                'button:has-text("Create API Key")',
                'button:has-text("Create Key")',
                'button:has-text("Add API Key")',
                'button:has-text("Generate")',
                '[data-test-id="create-api-key"]',
            ]
            
            created = False
            for selector in create_selectors:
                try:
                    await page.click(selector, timeout=5000)
                    print(f"Clicked Create API Key with selector: {selector}")
                    created = True
                    await page.wait_for_timeout(3000)
                    break
                except:
                    continue
            
            if not created:
                print("Could not find Create API Key button")
                content = await page.content()
                # Save content for debugging
                with open("settings_page.html", "w", encoding="utf-8") as f:
                    f.write(content)
                print("Saved settings page content to settings_page.html")
            
            # Get the API key if displayed
            print("Looking for API key in page...")
            content = await page.content()
            
            # Try to find the API key - it might be in an input or displayed
            api_key = None
            import re
            
            # Look for API key patterns
            api_key_matches = re.findall(r'[a-f0-9]{64}', content)
            if api_key_matches:
                api_key = api_key_matches[0]
                print(f"Found API key: {api_key}")
            
            # Also check for shorter keys
            if not api_key:
                api_key_matches = re.findall(r'n8n_[a-zA-Z0-9]{32,}', content)
                if api_key_matches:
                    api_key = api_key_matches[0]
                    print(f"Found API key (n8n_ format): {api_key}")
            
            # Check input fields
            if not api_key:
                inputs = await page.query_selector_all('input')
                for inp in inputs:
                    value = await inp.get_attribute('value')
                    if value and len(value) > 20:
                        api_key = value
                        print(f"Found API key in input: {api_key}")
                        break
            
            if api_key:
                # Save to .env file
                env_path = Path(".env")
                env_content = f"N8N_API_KEY={api_key}\n"
                env_path.write_text(env_content)
                print(f"\nSUCCESS: API Key saved to .env: {api_key}")
                return api_key
            else:
                print("\nFAILED: Could not find API key")
                return None
                
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            return None
        finally:
            await browser.close()

if __name__ == "__main__":
    api_key = asyncio.run(create_owner_and_api_key())
    if api_key:
        print("\nSUCCESS: Owner created and API key generated!")
    else:
        print("\nFAILED: Could not create API key")