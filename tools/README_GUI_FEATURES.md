# OTA GUI Features Documentation

## Introduction

This document describes the new features added to the OTA GUI for displaying manifest data and performing connectivity tests. These features are designed to help with testing and debugging the OTA update system, especially during development and simulation.

## Manifest Display Feature

The OTA daemon now returns the complete manifest when the GUI requests an update check. This allows the GUI to display detailed information about available updates.

### How It Works:

1. When the GUI sends the `check_now` command, the daemon returns:
   - The full manifest data as a JSON object
   - Update availability status
   - Current and available version information

2. The GUI can then display this information in a structured way, allowing users to see:
   - Package version details
   - Release notes
   - Update severity
   - File lists and sizes
   - Checksums and verification data

### Implementation Example:

See `tools/gui_example.py` for a demonstration of how to implement these features in a Tkinter GUI.

```python
# Example command to check for updates and get manifest data
response = send_command("check_now", {})

if response and response.get("status") == "success":
    data = response.get("data", {})
    manifest = data.get("manifest")
    
    # Display manifest data
    if manifest:
        # Format and display manifest data in your GUI
        print(json.dumps(manifest, indent=2))
```

## Connectivity Test Feature

The OTA daemon now provides a comprehensive connectivity test to verify all aspects of the update process can function correctly.

### How It Works:

The connectivity test performs three essential checks:

1. **Network Connectivity**: Tests if the system can reach the update server
2. **Manifest Fetch**: Verifies that manifest data can be successfully downloaded
3. **Download Capability**: Tests if update packages can be downloaded correctly

### Implementation Example:

See `tools/gui_example.py` for a demonstration implementation. The basic flow is:

```python
# Example command to run connectivity test
response = send_command("connectivity_check", {})

if response and response.get("status") == "success":
    data = response.get("data", {})
    
    # Access test results
    network_status = data.get("network_status", False)
    manifest_status = data.get("manifest_status", False)
    download_status = data.get("download_status", False)
    
    # Display results in your GUI
    print(f"Network: {'Success' if network_status else 'Failed'}")
    print(f"Manifest: {'Success' if manifest_status else 'Failed'}")
    print(f"Download: {'Success' if download_status else 'Failed'}")
```

## Testing in Ubuntu Linux

To test these features in Ubuntu Linux:

1. Start the OTA daemon (if not already running):
   ```
   cd /path/to/OTA/daemon
   python3 main.py
   ```

2. Run the example GUI:
   ```
   cd /path/to/OTA/tools
   python3 gui_example.py
   ```

3. Use the GUI to:
   - View current status information
   - Check for updates and view manifest data
   - Run connectivity tests
   - Trigger update installation

## Error Handling

If you encounter errors:

1. Check that the OTA daemon is running
2. Verify the socket path (`/tmp/robot-ai-ota.sock`) exists and has appropriate permissions
3. Check the OTA daemon logs in `robot-ai-ota.log` for error messages
4. Ensure your mock server is running if testing in simulation mode

## Integrating into Your Own GUI

To integrate these features into your own GUI:

1. Add a tab or section for displaying manifest data
2. Add controls for connectivity testing
3. Use the socket communication interface as shown in the example
4. Format and display the returned data according to your GUI's design

For more detailed implementation, refer to `tools/gui_example.py`, which provides a complete working example. 