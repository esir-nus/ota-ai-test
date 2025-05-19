# OTA Package Generator GUI

A simple graphical user interface for creating and managing OTA update packages for testing.

## Features

- Generate OTA update packages with custom version, severity, and release notes
- Automatically calculate checksums
- One-click upload to the mock update server
- View existing packages in the packages directory
- Command-line fallback mode if Tkinter is not available

## Requirements

- Python 3.6 or higher
- Tkinter (optional, for GUI mode)
- Running mock update server (for package uploading)

## Usage

1. Make sure the mock update server is running if you want to upload packages
2. Run the application:

```bash
python pack_gen_gui.py
```

3. If Tkinter is available, the GUI will open:
   - Fill in the package details:
     - Version: The version number of the package (e.g., "1.0.0")
     - Severity: Choose from "critical", "normal", or "low"
     - Release Notes: Brief description of the update
     - Upload option: Check to upload to the server after creation
   - Click "Generate Package" to create the package
   - The output area will display the results, including package information and upload status
   - Use "View Existing Packages" to see all packages in the packages directory

4. If Tkinter is not available, the script will automatically fall back to command-line mode:
   - Follow the on-screen prompts to select options
   - Enter the required information when prompted
   - The application will display results in the terminal

## Connection with OTA Mock Server

This tool uses the underlying functions from `generate_package.py` to create and upload packages to the mock server. It requires the mock update server to be running for upload functionality to work.

## Troubleshooting

If the GUI window disappears immediately, we've provided several troubleshooting tools:

### 1. Use the Launcher Script (Recommended)

The simplest way to troubleshoot is to use the launcher script:

```bash
# For Windows users:
launch_gui.bat

# For other platforms:
python launch_gui.py
```

This will:
- Log all activities to `gui_launcher.log`
- Display any errors in the console
- Keep the console window open even if errors occur
- Try multiple methods to launch the application

### 2. Test Tkinter Installation

We've provided a dedicated Tkinter test script:

```bash
python tkinter_test.py
```

This will:
- Perform a basic test of your Tkinter installation
- Create a simple window to verify display functionality
- Log detailed diagnostic information to `tkinter_test_log.txt`
- Show the exact point of failure if there are issues

### 3. Manual Troubleshooting Steps

If the above tools don't help, try these steps:

1. Run from command line to see error messages:
   ```
   python pack_gen_gui.py
   ```

2. Check if Tkinter is installed:
   ```
   python -c "import tkinter; print('Tkinter is installed')"
   ```
   
3. Install Tkinter if missing:
   - Windows: Usually included with Python, reinstall Python if missing
   - Linux: `sudo apt-get install python3-tk` (Ubuntu/Debian)
   - macOS: `brew install python-tk` (with Homebrew)

4. Check for conflicts with virtual environments:
   - Try running with your system Python instead of a virtual environment
   - Make sure the virtual environment has Tkinter installed

5. Review the logs:
   - `gui_launcher.log` - For launcher script diagnostics
   - `tkinter_test_log.txt` - For Tkinter test diagnostics 