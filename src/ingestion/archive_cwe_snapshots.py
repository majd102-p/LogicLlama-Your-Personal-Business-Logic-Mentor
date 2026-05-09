#!/usr/bin/env python3
"""Utility to fetch and archive historical CWE snapshots from MITRE."""

import os
import json
from pathlib import Path
from datetime import datetime
import requests
from requests import Session

# Known CWE versions with their URLs (based on MITRE historical availability)
CWE_VERSIONS = {
    "4.20": {
        "url": "https://cwe.mitre.org/data/xml/cwec_v4.20.xml.zip",
        "date": "2024-12-15",
        "description": "Latest stable release (v4.20)"
    },
    "4.19": {
        "url": "https://cwe.mitre.org/data/xml/cwec_v4.19.xml.zip",
        "date": "2024-06-15",
        "description": "Previous stable release (v4.19)"
    },
    "4.14": {
        "url": "https://cwe.mitre.org/data/xml/cwec_v4.14.xml.zip",
        "date": "2024-01-30",
        "description": "CWE v4.14 release"
    },
    "4.13": {
        "url": "https://cwe.mitre.org/data/xml/cwec_v4.13.xml.zip",
        "date": "2023-12-22",
        "description": "CWE v4.13 release"
    },
    "4.12": {
        "url": "https://cwe.mitre.org/data/xml/cwec_v4.12.xml.zip",
        "date": "2023-10-26",
        "description": "CWE v4.12 release"
    },
    "4.11": {
        "url": "https://cwe.mitre.org/data/xml/cwec_v4.11.xml.zip",
        "date": "2023-06-29",
        "description": "CWE v4.11 release"
    },
    "4.10": {
        "url": "https://cwe.mitre.org/data/xml/cwec_v4.10.xml.zip",
        "date": "2023-04-06",
        "description": "CWE v4.10 release"
    },
    "4.9": {
        "url": "https://cwe.mitre.org/data/xml/cwec_v4.9.xml.zip",
        "date": "2023-01-31",
        "description": "CWE v4.9 release"
    },
}

def download_cwe_snapshot(version: str, output_dir: Path) -> bool:
    """Download a specific CWE version snapshot."""
    if version not in CWE_VERSIONS:
        print(f"❌ Version {version} not found in known versions.")
        return False
    
    metadata = CWE_VERSIONS[version]
    url = metadata["url"]
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"cwec_v{version}.xml.zip"
    
    if output_file.exists():
        print(f"✅ {version} already exists at {output_file}")
        return True
    
    try:
        print(f"⏳ Downloading CWE v{version} from {url}...")
        response = requests.get(url, timeout=120, allow_redirects=True)
        response.raise_for_status()
        
        with open(output_file, "wb") as f:
            f.write(response.content)
        
        file_size = output_file.stat().st_size / (1024 * 1024)  # MB
        print(f"✅ Downloaded CWE v{version}: {file_size:.1f} MB → {output_file}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to download CWE v{version}: {e}")
        return False

def download_all_snapshots(output_dir: Path) -> dict:
    """Download all known CWE snapshots."""
    results = {}
    for version in sorted(CWE_VERSIONS.keys(), reverse=True):
        success = download_cwe_snapshot(version, output_dir)
        results[version] = {
            "downloaded": success,
            "metadata": CWE_VERSIONS[version]
        }
    return results

def create_manifest(output_dir: Path) -> None:
    """Create a manifest of archived CWE snapshots."""
    manifest = {
        "archive_date": datetime.now().isoformat(),
        "source": "MITRE CWE",
        "snapshots": []
    }
    
    for version, metadata in sorted(CWE_VERSIONS.items(), reverse=True):
        file_path = output_dir / f"cwec_v{version}.xml.zip"
        if file_path.exists():
            manifest["snapshots"].append({
                "version": version,
                "filename": file_path.name,
                "url": metadata["url"],
                "date": metadata["date"],
                "description": metadata["description"],
                "size_bytes": file_path.stat().st_size,
                "archived": True
            })
    
    manifest_file = output_dir / "CWE_SNAPSHOTS_MANIFEST.json"
    with open(manifest_file, "w") as f:
        json.dump(manifest, f, indent=2)
    
    print(f"\n📋 Manifest created: {manifest_file}")


def run_archive(output_dir: Path | None = None) -> dict[str, int]:
    target_dir = output_dir or Path("data/fixtures/cwe_snapshots")

    print("🔄 Starting CWE historical snapshot archive...\n")
    results = download_all_snapshots(target_dir)

    successful = sum(1 for v in results.values() if v["downloaded"])
    print(f"\n📊 Downloaded {successful}/{len(results)} CWE versions")

    create_manifest(target_dir)
    print("✅ CWE archival complete!")
    return {"downloaded": successful, "total": len(results)}

if __name__ == "__main__":
    run_archive()
