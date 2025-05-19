# Testing the OTA Daemon with the Mock Server

This guide explains how to test the OTA daemon with the local mock server to verify integration works properly.

## Prerequisites

- Python 3.8 or higher
- OTA daemon code
- Mock server code

## Step 1: Start the Mock Update Server

First, start the mock update server:

```bash
# From the root of the repository
cd OTA/mock_server
python mock_update_server.py
```

The server will start on port 5000 by default. You should see output indicating that the server is running.

## Step 2: Generate a Test Update Package

To test update functionality, you need to generate a test update package and upload it to the mock server:

```bash
# Using the GUI tool
cd OTA/mock_server
python pack_gen_gui.py

# OR using the command line
cd OTA/mock_server
python generate_package.py --version 1.1.0 --description "Test update" --upload
```

Make sure to check "Upload to server" in the GUI or specify `--upload` in the command line.

## Step 3: Test Connectivity

Before running the full daemon, you can verify connectivity using the test utility:

```bash
# On Windows:
cd OTA/tools
test_connectivity.bat

# On Linux/Mac:
cd OTA/tools
./test_connectivity.py --simulation --config=../daemon/config/test_config.json
```

This will test if the daemon can connect to the mock server, fetch the manifest, and download files.

## Step 4: Run the OTA Daemon in Simulation Mode

Now you can run the OTA daemon in simulation mode:

```bash
# From the root of the repository
cd OTA/daemon
python main.py --simulation --config=config/test_config.json
```

The daemon will connect to the mock server and check for updates.

## Step 5: Test Update Workflow

Once the daemon is running in simulation mode, it will check for updates and notify the GUI if an update is available (which should be the case if you uploaded a package with a version higher than 1.0.0).

You can interact with the daemon through its API to test:

1. Checking for updates
2. Scheduling an update
3. Executing an update
4. Reporting status

## Debugging

If you encounter any issues:

1. Check both the daemon and server logs for error messages
2. Verify that the server is running and accessible (http://localhost:5000/health)
3. Make sure the daemon is configured to use the correct server URL
4. Check that the update package was uploaded successfully

## Common Issues

- **Connection refused**: Make sure the mock server is running
- **Manifest not found**: Check if the manifest endpoint is working correctly
- **Authentication failures**: The mock server may have authentication enabled

## Additional Tools

- **GUI Test Tool**: Use the GUI package generator to create and upload test packages
- **Connectivity Test**: Run the connectivity test script to verify basic communication
- **Manual API Testing**: Use tools like curl or Postman to test the mock server API endpoints directly 