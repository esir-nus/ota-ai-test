#!/usr/bin/env python3
"""
Simple Tkinter test script to diagnose GUI issues.
This will help identify why the pack_gen_gui.py might be disappearing.
"""
import os
import sys
import traceback

# Function to write to a log file
def log_to_file(message):
    """Write a message to the log file"""
    with open("tkinter_test_log.txt", "a") as f:
        f.write(message + "\n")

# Start diagnostic logging
log_to_file("\n\n=== New Tkinter Test Run ===")
log_to_file(f"Python version: {sys.version}")
log_to_file(f"Python executable: {sys.executable}")
log_to_file(f"Current directory: {os.getcwd()}")

try:
    # Test importing tkinter
    log_to_file("Attempting to import tkinter...")
    import tkinter as tk
    log_to_file(f"Tkinter imported successfully. Version: {tk.TkVersion}")
    
    # Try to create a root window
    log_to_file("Attempting to create Tk root window...")
    root = tk.Tk()
    log_to_file("Root window created successfully")
    
    # Set window properties
    root.title("Tkinter Test")
    root.geometry("400x300")
    log_to_file("Window properties set")
    
    # Add a label
    label = tk.Label(root, text="Tkinter is working correctly!")
    label.pack(pady=20)
    log_to_file("Label created and packed")
    
    # Add a button that will close the window
    def on_button_click():
        log_to_file("Button clicked")
        root.destroy()
    
    button = tk.Button(root, text="Click to close", command=on_button_click)
    button.pack(pady=10)
    log_to_file("Button created and packed")
    
    # Add a note about the log file
    note = tk.Label(root, text="Check tkinter_test_log.txt for diagnostics")
    note.pack(pady=10)
    
    # Before mainloop, add a handler to log when window is closed
    def on_close():
        log_to_file("Window closed by user")
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_close)
    log_to_file("Close handler added")
    
    # Start the main loop with timeout to ensure we can see any errors
    log_to_file("Starting main loop")
    print("Tkinter window should be visible now. Check tkinter_test_log.txt for diagnostics.")
    print("If no window appears, there may be an issue with your display configuration.")
    
    # Make window stay on top to ensure visibility
    root.attributes("-topmost", True)
    root.update()
    root.attributes("-topmost", False)
    
    root.mainloop()
    log_to_file("Main loop ended normally")
    
except Exception as e:
    error_msg = f"ERROR: {str(e)}\n{traceback.format_exc()}"
    log_to_file(error_msg)
    print(f"Error occurred: {str(e)}")
    print("Check tkinter_test_log.txt for detailed error information")

# Add a pause at the end to keep the console window open
print("\nTest completed. Check tkinter_test_log.txt for results.")
input("Press Enter to exit...") 