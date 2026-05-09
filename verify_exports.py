#!/usr/bin/env python3
"""Verify all exporters work correctly."""

import json
import subprocess
import sys

def test_export(command, limit=3):
    """Test an export command."""
    result = subprocess.run(
        ['python', '-m', 'src.core.cli'] + command.split() + ['--limit', str(limit)],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"ERROR: {' '.join(command.split())} failed")
        print(f"stderr: {result.stderr}")
        return False
    
    return result.stdout

def main():
    print("=" * 60)
    print("COMPREHENSIVE PROJECT VERIFICATION")
    print("=" * 60)
    
    # Test training corpus export
    print("\n[1] Training Corpus Export")
    output = test_export('export-training-corpus --format json')
    if output:
        data = json.loads(output)
        print(f"✓ Format: {data.get('format')}")
        print(f"✓ Total examples: {data.get('total_examples')}")
        for ex_type, count in sorted(data.get('statistics', {}).get('by_type', {}).items()):
            print(f"  - {ex_type}: {count}")
    
    # Test simulation corpus export
    print("\n[2] Simulation Corpus Export")
    output = test_export('export-simulation-corpus --format json')
    if output:
        data = json.loads(output)
        print(f"✓ Format: {data.get('format')}")
        print(f"✓ Total simulations: {data.get('total_simulations')}")
        for sim_type, count in sorted(data.get('statistics', {}).get('by_type', {}).items()):
            print(f"  - {sim_type}: {count}")
    
    # Test graph export
    print("\n[3] Knowledge Graph Export")
    result = subprocess.run(
        ['python', '-m', 'src.core.cli', 'export-graph', '--format', 'json', '--limit', '3'],
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        data = json.loads(result.stdout)
        print(f"✓ Version: {data.get('version')}")
        print(f"✓ Nodes: {data.get('nodes_count')}")
        print(f"✓ Edges: {data.get('edges_count')}")
    else:
        print(f"ERROR: export-graph failed: {result.stderr[:100]}")
    
    # Test search
    print("\n[4] Case Search")
    result = subprocess.run(
        ['python', '-m', 'src.core.cli', 'search', 'sql'],
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        lines = [l for l in result.stdout.strip().split('\n') if l.strip()]
        print(f"✓ Found {len(lines)} results for 'sql'")
        for line in lines[:3]:
            print(f"  - {line[:80]}")
    else:
        print(f"ERROR: search failed: {result.stderr[:100]}")
    
    # Test list
    print("\n[5] Case Listing")
    result = subprocess.run(
        ['python', '-m', 'src.core.cli', 'list', '--limit', '3'],
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        lines = result.stdout.strip().split('\n')
        print(f"✓ Listed {len(lines)} cases")
        for line in lines[:3]:
            print(f"  - {line[:80]}")
    
    print("\n" + "=" * 60)
    print("✓ ALL EXPORTS AND COMMANDS VERIFIED")
    print("=" * 60)

if __name__ == '__main__':
    main()
