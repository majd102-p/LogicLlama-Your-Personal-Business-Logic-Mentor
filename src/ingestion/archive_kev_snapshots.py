#!/usr/bin/env python3
"""Utility to fetch and archive historical CISA KEV (Known Exploited Vulnerabilities) snapshots."""

import os
import json
from pathlib import Path
from datetime import datetime
import requests
from typing import Optional

# CISA KEV feed URLs (current and documented historical endpoints)
KEV_SOURCES = {
    "current": {
        "url": "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json",
        "date": "2026-05-03",
        "description": "Current CISA KEV catalog (live feed)"
    },
    "archive_2024_12": {
        "url": "https://web.archive.org/web/20241201000000*/cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json",
        "date": "2024-12-01",
        "description": "CISA KEV snapshot from December 2024 (via Wayback Machine)",
        "wayback": True
    },
    "archive_2024_06": {
        "url": "https://web.archive.org/web/20240601000000*/cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json",
        "date": "2024-06-01",
        "description": "CISA KEV snapshot from June 2024 (via Wayback Machine)",
        "wayback": True
    },
    "archive_2023_12": {
        "url": "https://web.archive.org/web/20231201000000*/cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json",
        "date": "2023-12-01",
        "description": "CISA KEV snapshot from December 2023 (via Wayback Machine)",
        "wayback": True
    },
    "archive_2023_06": {
        "url": "https://web.archive.org/web/20230601000000*/cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json",
        "date": "2023-06-01",
        "description": "CISA KEV snapshot from June 2023 (via Wayback Machine)",
        "wayback": True
    },
}

def get_latest_wayback_url(calendar_url: str) -> Optional[str]:
    """Get the latest available snapshot from Wayback Machine calendar API."""
    try:
        response = requests.get(calendar_url, timeout=30)
        if response.status_code == 200:
            data = response.json()
            if data.get("archived_snapshots"):
                latest = data["archived_snapshots"]["closest"]
                if latest.get("available"):
                    timestamp = latest.get("timestamp")
                    return f"https://web.archive.org/web/{timestamp}/{calendar_url.split('/')[-1]}"
    except Exception as e:
        print(f"⚠️  Wayback calendar fetch failed: {e}")
    return None

def download_kev_snapshot(key: str, source_info: dict, output_dir: Path) -> bool:
    """Download a specific KEV snapshot."""
    url = source_info["url"]
    is_wayback = source_info.get("wayback", False)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Sanitize filename
    filename = f"kev_{key}.json"
    output_file = output_dir / filename
    
    if output_file.exists():
        print(f"✅ {key} already exists at {output_file}")
        return True
    
    try:
        print(f"⏳ Fetching KEV snapshot: {key}...")
        
        # If Wayback URL pattern, resolve to actual snapshot
        if is_wayback and "*/cisa.gov" in url:
            # Try to find latest snapshot for this date pattern
            calendar_url = url.replace("*/", "")
            wayback_url = get_latest_wayback_url(calendar_url)
            if wayback_url:
                url = wayback_url
            else:
                print(f"⚠️  Could not resolve Wayback snapshot for {key}, skipping...")
                return False
        
        response = requests.get(url, timeout=60, allow_redirects=True)
        response.raise_for_status()
        
        # Verify it's valid JSON
        data = response.json()
        
        with open(output_file, "w") as f:
            json.dump(data, f, indent=2)
        
        entry_count = len(data.get("vulnerabilities", []))
        file_size = output_file.stat().st_size / 1024  # KB
        print(f"✅ Downloaded KEV {key}: {entry_count} entries, {file_size:.0f} KB → {output_file}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to download KEV {key}: {e}")
        return False
    except json.JSONDecodeError:
        print(f"❌ Invalid JSON for KEV {key}")
        return False
    except Exception as e:
        print(f"❌ Error processing KEV {key}: {e}")
        return False

def download_all_snapshots(output_dir: Path) -> dict:
    """Download all known KEV snapshots."""
    results = {}
    
    # Prioritize current snapshot
    if "current" in KEV_SOURCES:
        success = download_kev_snapshot("current", KEV_SOURCES["current"], output_dir)
        results["current"] = {
            "downloaded": success,
            "metadata": KEV_SOURCES["current"]
        }
    
    # Then archive snapshots
    for key in sorted(KEV_SOURCES.keys()):
        if key != "current":
            success = download_kev_snapshot(key, KEV_SOURCES[key], output_dir)
            results[key] = {
                "downloaded": success,
                "metadata": KEV_SOURCES[key]
            }
    
    return results

def create_manifest(output_dir: Path) -> None:
    """Create a manifest of archived KEV snapshots."""
    manifest = {
        "archive_date": datetime.now().isoformat(),
        "source": "CISA Known Exploited Vulnerabilities (KEV)",
        "snapshots": []
    }
    
    # Add successfully downloaded snapshots
    for key in sorted(KEV_SOURCES.keys(), reverse=True):
        file_path = output_dir / f"kev_{key}.json"
        if file_path.exists():
            try:
                with open(file_path) as f:
                    data = json.load(f)
                
                manifest["snapshots"].append({
                    "key": key,
                    "filename": file_path.name,
                    "url": KEV_SOURCES[key]["url"],
                    "date": KEV_SOURCES[key]["date"],
                    "description": KEV_SOURCES[key]["description"],
                    "size_bytes": file_path.stat().st_size,
                    "vulnerability_count": len(data.get("vulnerabilities", [])),
                    "archived": True
                })
            except Exception as e:
                print(f"⚠️  Could not read {file_path}: {e}")
    
    manifest_file = output_dir / "KEV_SNAPSHOTS_MANIFEST.json"
    with open(manifest_file, "w") as f:
        json.dump(manifest, f, indent=2)
    
    print(f"\n📋 Manifest created: {manifest_file}")


def run_archive(output_dir: Path | None = None) -> dict[str, int]:
    target_dir = output_dir or Path("data/fixtures/kev_snapshots")

    print("🔄 Starting CISA KEV historical snapshot archive...\n")
    results = download_all_snapshots(target_dir)

    successful = sum(1 for v in results.values() if v["downloaded"])
    print(f"\n📊 Downloaded {successful}/{len(results)} KEV snapshots")

    create_manifest(target_dir)
    print("✅ KEV archival complete!")
    return {"downloaded": successful, "total": len(results)}

if __name__ == "__main__":
    run_archive()
