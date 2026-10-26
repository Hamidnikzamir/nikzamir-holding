#!/usr/bin/env python3
"""Daily Master Runner - Executes all 5 daily automation scripts"""
import os
import sys
import subprocess

print("=" * 70)
print("NIKZAMIR HOLDING - DAILY AUTOMATION")
print("=" * 70)

scripts = [
    "tools/trader_daily.py",
    "tools/seo_daily.py",
    "tools/leadrescue_daily.py",
    "tools/agencyreport_daily.py",
    "tools/templated_daily.py"
]

success_count = 0
for script in scripts:
    print(f"\n[INFO] Running {script}...")
    if os.path.exists(script):
        try:
            result = subprocess.run([sys.executable, script], capture_output=True, text=True, timeout=120)
            print(result.stdout)
            if result.returncode == 0:
                success_count += 1
                print(f"[OK] {script} completed successfully")
            else:
                print(f"[ERROR] {script} failed with code {result.returncode}")
                print(result.stderr)
        except Exception as e:
            print(f"[ERROR] Failed to run {script}: {e}")
    else:
        print(f"[WARN] Script not found: {script}")

print("\n" + "=" * 70)
print(f"DAILY AUTOMATION COMPLETED: {success_count}/{len(scripts)} scripts succeeded")
print("=" * 70)
