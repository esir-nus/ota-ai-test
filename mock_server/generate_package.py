"""
Script to generate test update packages for the OTA mock server.
"""
import os
import zipfile
import json
import hashlib
import argparse
from datetime import datetime
from config import PACKAGE_DIRECTORY

def calculate_checksum(file_path):
    """Calculate SHA256 checksum for a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read and update hash in chunks of 4K
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def create_package(version, severity="normal", files=None, notes="Test release"):
    """Create a test update package with specified content."""
    # Ensure package directory exists
    os.makedirs(PACKAGE_DIRECTORY, exist_ok=True)
    
    # Create a temporary directory for package contents
    temp_dir = os.path.join(PACKAGE_DIRECTORY, f"temp_{version}")
    os.makedirs(temp_dir, exist_ok=True)
    
    # If no files are specified, create a default test file
    if not files:
        files = [
            {
                "name": "test_file.txt",
                "content": f"This is a test file for version {version}",
                "executable": False,
                "destination": "/opt/robot-ai/test_file.txt"
            }
        ]
    
    # Create the manifest
    manifest = {
        "version": version,
        "release_date": datetime.now().isoformat(),
        "severity": severity,
        "release_notes": notes,
        "files": []
    }
    
    # Create package files
    for file_info in files:
        file_path = os.path.join(temp_dir, file_info["name"])
        
        # Write content to file
        with open(file_path, "w") as f:
            f.write(file_info["content"])
        
        # Calculate checksum
        checksum = calculate_checksum(file_path)
        
        # Add file info to manifest
        manifest["files"].append({
            "name": file_info["name"],
            "destination": file_info["destination"],
            "checksum": checksum,
            "executable": file_info.get("executable", False)
        })
    
    # Write manifest to file
    manifest_path = os.path.join(temp_dir, "manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    
    # Create a zip file
    package_name = f"update_package_{version}.zip"
    package_path = os.path.join(PACKAGE_DIRECTORY, package_name)
    
    with zipfile.ZipFile(package_path, "w") as zipf:
        # Add all files in temp_dir to the zip
        for root, _, files in os.walk(temp_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, temp_dir)
                zipf.write(file_path, arcname)
    
    # Calculate package checksum
    package_checksum = calculate_checksum(package_path)
    
    # Clean up temp directory
    for file_name in os.listdir(temp_dir):
        os.remove(os.path.join(temp_dir, file_name))
    os.rmdir(temp_dir)
    
    print(f"Created package: {package_name}")
    print(f"Version: {version}")
    print(f"Severity: {severity}")
    print(f"Checksum: {package_checksum}")
    print(f"Path: {package_path}")
    
    return {
        "package_path": package_path,
        "version": version,
        "severity": severity,
        "checksum": package_checksum,
        "release_notes": notes
    }

def upload_to_server(package_info, server_url="http://localhost:5000"):
    """Upload the package to the mock server."""
    import requests
    
    with open(package_info["package_path"], "rb") as f:
        files = {"file": f}
        data = {
            "version": package_info["version"],
            "severity": package_info["severity"],
            "checksum": package_info["checksum"],
            "release_notes": package_info["release_notes"]
        }
        
        response = requests.post(f"{server_url}/upload", files=files, data=data)
        
        if response.status_code == 200:
            print("Upload successful!")
            print(json.dumps(response.json(), indent=2))
            return True
        else:
            print(f"Upload failed with status {response.status_code}")
            print(response.text)
            return False

def main():
    """Main function to parse args and generate packages."""
    parser = argparse.ArgumentParser(description="Generate test update packages")
    parser.add_argument("--version", required=True, help="Version of the package")
    parser.add_argument("--severity", choices=["critical", "normal", "low"], default="normal",
                        help="Severity level of the update")
    parser.add_argument("--notes", default="Test release", help="Release notes")
    parser.add_argument("--upload", action="store_true", help="Upload to local server after creation")
    
    args = parser.parse_args()
    
    package_info = create_package(args.version, args.severity, notes=args.notes)
    
    if args.upload:
        upload_to_server(package_info)

if __name__ == "__main__":
    main()