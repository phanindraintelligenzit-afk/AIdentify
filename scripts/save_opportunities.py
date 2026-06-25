#!/usr/bin/env python3
"""Save opportunities to JSON file after scanning."""
import json
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))
from opportunity_scanner import run_scan

def main():
    opportunities, briefing = run_scan()
    
    # Filter scored >= 30
    scored = [d for d in opportunities if d.get('opportunity_score', 0) >= 30]
    scored.sort(key=lambda x: x.get('opportunity_score', 0), reverse=True)
    
    date_str = datetime.now().strftime('%Y-%m-%d')
    os.makedirs('marketplace/opportunities', exist_ok=True)
    out_path = f'marketplace/opportunities/{date_str}.json'
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(scored[:15], f, indent=2, ensure_ascii=False)
    
    print(f"Total scanned: {len(opportunities)}")
    print(f"Scored >= 30: {len(scored)}")
    print(f"Saved to: {out_path}")
    print(f"\nTop 5:")
    for i, s in enumerate(scored[:5], 1):
        print(f"  {i}. [{s.get('opportunity_score', 0)}] {s.get('title', '?')[:70]}")

if __name__ == "__main__":
    main()
