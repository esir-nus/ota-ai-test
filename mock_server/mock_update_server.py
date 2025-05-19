from flask import Flask, jsonify, request, send_file
import os
import json
from datetime import datetime
import logging
from config import UPDATE_SERVER_PORT, UPDATE_SERVER_LOG, LOG_FORMAT, PACKAGE_DIRECTORY

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    handlers=[
        logging.FileHandler(UPDATE_SERVER_LOG),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('mock_update_server')

app = Flask(__name__)

# Ensure package directory exists
os.makedirs(PACKAGE_DIRECTORY, exist_ok=True)

# In-memory storage for update packages and manifests
packages = {}
manifests = {
    "latest": {
        "version": "1.0.0",
        "release_date": datetime.now().isoformat(),
        "severity": "normal",
        "checksum": "dummy_checksum",
        "download_url": f"http://localhost:{UPDATE_SERVER_PORT}/download/latest",
        "release_notes": "Initial mock release"
    }
}

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    logger.info("Health check endpoint accessed")
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    })

@app.route('/ping', methods=['GET'])
def ping():
    """Simple ping endpoint for connectivity testing"""
    return "OK", 200

@app.route('/manifest/latest', methods=['GET'])
def get_latest_manifest():
    """Get the latest update manifest"""
    logger.info("Latest manifest requested")
    return jsonify(manifests["latest"])

@app.route('/<product_type>/manifest.json', methods=['GET'])
def get_product_manifest(product_type):
    """Get the manifest for a specific product type"""
    logger.info(f"Manifest requested for product type: {product_type}")
    # Use the latest manifest for any product type
    return jsonify(manifests["latest"])

@app.route('/manifest/<version>', methods=['GET'])
def get_manifest(version):
    """Get a specific version manifest"""
    logger.info(f"Manifest requested for version: {version}")
    if version not in manifests:
        return jsonify({"error": "Version not found"}), 404
    return jsonify(manifests[version])

@app.route('/download/<version>', methods=['GET'])
def download_package(version):
    """Download a specific version package"""
    logger.info(f"Download requested for version: {version}")
    
    # Check if version exists
    if version not in packages:
        return jsonify({"error": "Package not found"}), 404
    
    package_path = os.path.join(PACKAGE_DIRECTORY, f"update_package_{version}.zip")
    if not os.path.exists(package_path):
        return jsonify({"error": "Package file not found"}), 404
        
    return send_file(
        package_path,
        as_attachment=True,
        download_name=f"update_package_{version}.zip"
    )

@app.route('/upload', methods=['POST'])
def upload_package():
    """Upload a new update package"""
    logger.info("Package upload endpoint accessed")
    
    # Check if file was uploaded
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
        
    # Get metadata from form data
    version = request.form.get('version')
    if not version:
        return jsonify({"error": "Version is required"}), 400
        
    # Save the file
    package_path = os.path.join(PACKAGE_DIRECTORY, f"update_package_{version}.zip")
    file.save(package_path)
    
    # Update manifests
    manifests[version] = {
        "version": version,
        "release_date": datetime.now().isoformat(),
        "severity": request.form.get('severity', 'normal'),
        "checksum": request.form.get('checksum', 'dummy_checksum'),
        "download_url": f"http://localhost:{UPDATE_SERVER_PORT}/download/{version}",
        "release_notes": request.form.get('release_notes', '')
    }
    
    # Update latest if needed
    if version > manifests["latest"]["version"]:
        manifests["latest"] = manifests[version]
    
    return jsonify({
        "status": "success",
        "version": version,
        "manifest": manifests[version]
    })

def main():
    """Start the mock update server"""
    logger.info(f"Starting mock update server on port {UPDATE_SERVER_PORT}")
    app.run(host='0.0.0.0', port=UPDATE_SERVER_PORT)

if __name__ == '__main__':
    main() 