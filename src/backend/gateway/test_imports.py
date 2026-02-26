#!/usr/bin/env python
import sys
import traceback

try:
    # Test imports
    print("Testing imports...")
    from fastapi import FastAPI
    print("✓ fastapi imported")
    from fastapi.middleware.cors import CORSMiddleware
    print("✓ fastapi.middleware.cors imported")
    from config.config import config
    print("✓ config loaded")
    from common.user import authenticate_user
    print("✓ authenticate_user imported")
    from util.captcha import generate_captcha
    print("✓ captcha imported")
    
    print("\n✅ All imports successful!")
    print(f"\nConfig origins: {config['origins']}")
    
except Exception as e:
    print(f"\n❌ Import Error: {e}")
    traceback.print_exc()
    sys.exit(1)
