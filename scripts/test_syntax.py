#!/usr/bin/env python3
"""Quick syntax test for run_scraper.py"""

import sys
import os

# Add path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

try:
    # Test import
    from scripts.run_scraper import main, load_sources_config
    print("✅ Syntax check passed - all imports successful")
    print("✅ Main function and load_sources_config imported successfully")
except SyntaxError as e:
    print(f"❌ Syntax Error: {e}")
except ImportError as e:
    print(f"⚠️ Import Error (expected): {e}")
except Exception as e:
    print(f"❌ Unexpected Error: {e}")

print("🎯 run_scraper.py syntax validation complete")