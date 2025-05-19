#!/usr/bin/env python3
"""
Launcher script for pack_gen_gui.py with comprehensive error handling.
This script will run the GUI and capture any errors that might cause it to disappear.
"""
import os
import sys
import subprocess
import traceback
import time
from datetime import datetime

# Configure logging
LOG_FILE = "gui_launcher.log"

def log_message(message):
    """Write a message to the log file with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] {message}\n")

# Log startup information
log_message("\n\n========== NEW LAUNCHER SESSION ==========")
log_message(f"Python version: {sys.version}")
log_message(f"Python executable: {sys.executable}")
log_message(f"Current directory: {os.getcwd()}")
log_message(f"Script path: {os.path.abspath(__file__)}")

# Get the directory of this script
script_dir = os.path.dirname(os.path.abspath(__file__))
log_message(f"Script directory: {script_dir}")

# Path to the main GUI script
gui_script = os.path.join(script_dir, "pack_gen_gui.py")
log_message(f"GUI script path: {gui_script}")

# Function to check if a module can be imported
def check_module(module_name):
    try:
        __import__(module_name)
        log_message(f"Module {module_name} is available")
        return True
    except ImportError as e:
        log_message(f"Module {module_name} is NOT available: {str(e)}")
        return False

# Check critical modules
log_message("Checking required modules...")
tkinter_available = check_module("tkinter")
if not tkinter_available:
    log_message("Tkinter is not available. GUI will fall back to CLI mode.")
else:
    try:
        import tkinter as tk
        log_message(f"Tkinter version: {tk.TkVersion}")
    except Exception as e:
        log_message(f"Error getting Tkinter version: {str(e)}")

# Check if the GUI script exists
if not os.path.exists(gui_script):
    error_msg = f"ERROR: GUI script not found at {gui_script}"
    log_message(error_msg)
    print(error_msg)
    input("Press Enter to exit...")
    sys.exit(1)

# Try to run the GUI application
log_message("Attempting to run GUI application...")
print("Launching OTA Package Generator...")
print(f"Logging to {os.path.abspath(LOG_FILE)}")

try:
    # Method 1: Import and run directly (preferred)
    log_message("Method 1: Trying to import and run directly")
    
    # Add script directory to path
    sys.path.insert(0, script_dir)
    
    try:
        # Try to change directory to script directory to ensure relative paths work
        original_dir = os.getcwd()
        os.chdir(script_dir)
        log_message(f"Changed directory to: {os.getcwd()}")
        
        # Now try to import and run the script
        import pack_gen_gui
        log_message("Successfully imported pack_gen_gui module")
        
        # Run the main function
        try:
            log_message("Running main() function...")
            pack_gen_gui.main()
            log_message("main() function completed normally")
        except Exception as e:
            error_msg = f"Error in main() function: {str(e)}\n{traceback.format_exc()}"
            log_message(error_msg)
            print(f"Error running application: {str(e)}")
            print(f"See {os.path.abspath(LOG_FILE)} for details")
            
        # Change back to original directory
        os.chdir(original_dir)
        
    except ImportError as e:
        log_message(f"Import failed: {str(e)}\n{traceback.format_exc()}")
        
        # Method 2: Try running as subprocess
        log_message("Method 2: Trying to run as subprocess")
        try:
            result = subprocess.run([sys.executable, gui_script], 
                                   stderr=subprocess.PIPE,
                                   text=True)
            
            if result.returncode != 0:
                log_message(f"Subprocess error (code {result.returncode}): {result.stderr}")
                print(f"Error: {result.stderr}")
            else:
                log_message("Subprocess completed successfully")
        except Exception as e:
            error_msg = f"Subprocess error: {str(e)}\n{traceback.format_exc()}"
            log_message(error_msg)
            print(f"Error launching application: {str(e)}")
            
except Exception as e:
    error_msg = f"Critical error: {str(e)}\n{traceback.format_exc()}"
    log_message(error_msg)
    print(f"Critical error: {str(e)}")
    print(f"Check {os.path.abspath(LOG_FILE)} for detailed error information")

# Final message
log_message("Launcher script completed")
print("\nApplication has exited.")
print(f"Check {os.path.abspath(LOG_FILE)} for detailed logs.")
input("Press Enter to exit...") 