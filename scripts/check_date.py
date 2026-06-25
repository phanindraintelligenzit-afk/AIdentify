#!/usr/bin/env python3
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))
from datetime import datetime
date_str = datetime.now().strftime("%Y-%m-%d")
print(f"Date: {date_str}")
print(f"Exists: {os.path.exists(f'marketplace/opportunities/{date_str}.json')}")
print(f"CWD: {os.getcwd()}")
