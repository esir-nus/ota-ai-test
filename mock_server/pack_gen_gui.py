#!/usr/bin/env python3
"""
GUI application for generating OTA test packages
"""
import os
import sys
import json
import subprocess
from pathlib import Path

def check_tkinter():
    """Check if Tkinter is properly installed"""
    try:
        import tkinter
        return True
    except ImportError:
        return False

# Add the current directory to the path to import generate_package
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from generate_package import create_package, upload_to_server
from config import UPDATE_SERVER_BASE_URL, PACKAGE_DIRECTORY

# Only import Tkinter if it's available
if check_tkinter():
    import tkinter as tk
    from tkinter import ttk, scrolledtext, messagebox

class PackageGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("OTA Package Generator")
        self.root.geometry("800x600")
        self.root.minsize(600, 500)
        
        # Create main frame
        main_frame = ttk.Frame(root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create form frame
        form_frame = ttk.LabelFrame(main_frame, text="Package Configuration", padding="10")
        form_frame.pack(fill=tk.X, pady=5)
        
        # Version input
        ttk.Label(form_frame, text="Version:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.version_var = tk.StringVar(value="1.0.0")
        ttk.Entry(form_frame, textvariable=self.version_var, width=15).grid(row=0, column=1, sticky=tk.W, pady=5)
        
        # Severity selection
        ttk.Label(form_frame, text="Severity:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.severity_var = tk.StringVar(value="normal")
        severity_combo = ttk.Combobox(form_frame, textvariable=self.severity_var, width=15)
        severity_combo['values'] = ('critical', 'normal', 'low')
        severity_combo.grid(row=1, column=1, sticky=tk.W, pady=5)
        
        # Release notes
        ttk.Label(form_frame, text="Release Notes:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.notes_var = tk.StringVar(value="Test release")
        ttk.Entry(form_frame, textvariable=self.notes_var, width=40).grid(row=2, column=1, columnspan=3, sticky=tk.W, pady=5)
        
        # Upload option
        self.upload_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(form_frame, text="Upload to server after creation", variable=self.upload_var).grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # Buttons frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        # Generate button
        self.generate_button = ttk.Button(
            button_frame, 
            text="Generate Package", 
            command=self.generate_package,
            style="Accent.TButton"
        )
        self.generate_button.pack(side=tk.LEFT, padx=5)
        
        # View packages button
        self.view_button = ttk.Button(
            button_frame, 
            text="View Existing Packages", 
            command=self.view_packages
        )
        self.view_button.pack(side=tk.LEFT, padx=5)
        
        # Output frame
        output_frame = ttk.LabelFrame(main_frame, text="Output", padding="10")
        output_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Output text area
        self.output_text = scrolledtext.ScrolledText(output_frame, wrap=tk.WORD, height=10)
        self.output_text.pack(fill=tk.BOTH, expand=True)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_bar = ttk.Label(root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Initialize status
        self.status_var.set("Ready")
        
        # Apply modern theme elements
        self.configure_styles()
    
    def configure_styles(self):
        """Configure styles for a more modern look"""
        style = ttk.Style()
        
        # Check if we can use a more modern theme
        available_themes = style.theme_names()
        if 'clam' in available_themes:
            style.theme_use('clam')
        
        # Configure button styles
        style.configure('TButton', font=('Segoe UI', 10))
        style.configure('Accent.TButton', foreground='white', background='#0078D7')
        
        # Configure frames
        style.configure('TLabelframe', font=('Segoe UI', 10))
        style.configure('TLabelframe.Label', font=('Segoe UI', 10, 'bold'))
    
    def generate_package(self):
        """Generate a package with the specified parameters"""
        try:
            version = self.version_var.get().strip()
            severity = self.severity_var.get()
            notes = self.notes_var.get()
            upload = self.upload_var.get()
            
            if not version:
                messagebox.showerror("Error", "Version is required!")
                return
            
            self.status_var.set("Generating package...")
            self.output_text.delete(1.0, tk.END)
            self.output_text.insert(tk.END, f"Generating package version {version}...\n")
            self.root.update()
            
            # Create the package
            package_info = create_package(version, severity, notes=notes)
            
            # Display package info
            self.output_text.insert(tk.END, f"Created package: {os.path.basename(package_info['package_path'])}\n")
            self.output_text.insert(tk.END, f"Version: {package_info['version']}\n")
            self.output_text.insert(tk.END, f"Severity: {package_info['severity']}\n")
            self.output_text.insert(tk.END, f"Checksum: {package_info['checksum']}\n")
            self.output_text.insert(tk.END, f"Path: {package_info['package_path']}\n\n")
            
            # Upload if requested
            if upload:
                self.output_text.insert(tk.END, "Uploading to server...\n")
                self.root.update()
                
                success = upload_to_server(package_info)
                
                if success:
                    self.output_text.insert(tk.END, "Upload successful!\n")
                    self.status_var.set("Package created and uploaded successfully")
                else:
                    self.output_text.insert(tk.END, "Upload failed. Check if the server is running.\n")
                    self.status_var.set("Package created but upload failed")
            else:
                self.status_var.set("Package created successfully")
                
        except Exception as e:
            self.output_text.insert(tk.END, f"Error: {str(e)}\n")
            self.status_var.set("Error occurred")
            messagebox.showerror("Error", str(e))
    
    def view_packages(self):
        """View existing packages in the packages directory"""
        try:
            package_dir = Path(PACKAGE_DIRECTORY)
            if not package_dir.exists():
                self.output_text.delete(1.0, tk.END)
                self.output_text.insert(tk.END, "No packages directory found.")
                return
                
            packages = list(package_dir.glob("update_package_*.zip"))
            
            self.output_text.delete(1.0, tk.END)
            if not packages:
                self.output_text.insert(tk.END, "No packages found.")
                return
                
            self.output_text.insert(tk.END, "Existing packages:\n\n")
            for package in packages:
                self.output_text.insert(tk.END, f"- {package.name}\n")
                
            self.status_var.set(f"Found {len(packages)} packages")
            
        except Exception as e:
            self.output_text.insert(tk.END, f"Error: {str(e)}\n")
            self.status_var.set("Error occurred")

def run_cli_mode():
    """Run in command-line mode when Tkinter is not available"""
    print("====================================================")
    print("= OTA Package Generator (Command-line fallback mode) =")
    print("====================================================")
    
    try:
        while True:
            print("\nOptions:")
            print("1. Generate new package")
            print("2. View existing packages")
            print("3. Exit")
            
            choice = input("\nSelect an option (1-3): ")
            
            if choice == '1':
                version = input("Version (e.g. 1.0.0): ")
                if not version.strip():
                    print("Error: Version is required!")
                    continue
                
                severity = input("Severity (critical, normal, low) [normal]: ").strip().lower()
                if severity not in ['critical', 'normal', 'low']:
                    severity = 'normal'
                
                notes = input("Release notes [Test release]: ").strip()
                if not notes:
                    notes = "Test release"
                
                upload_choice = input("Upload to server? (y/n) [y]: ").strip().lower()
                upload = upload_choice != 'n'
                
                print(f"\nGenerating package version {version}...")
                package_info = create_package(version, severity, notes=notes)
                
                print(f"Created package: {os.path.basename(package_info['package_path'])}")
                print(f"Version: {package_info['version']}")
                print(f"Severity: {package_info['severity']}")
                print(f"Checksum: {package_info['checksum']}")
                print(f"Path: {package_info['package_path']}")
                
                if upload:
                    print("\nUploading to server...")
                    success = upload_to_server(package_info)
                    
                    if success:
                        print("Upload successful!")
                    else:
                        print("Upload failed. Check if the server is running.")
            
            elif choice == '2':
                package_dir = Path(PACKAGE_DIRECTORY)
                if not package_dir.exists():
                    print("No packages directory found.")
                    continue
                    
                packages = list(package_dir.glob("update_package_*.zip"))
                
                if not packages:
                    print("No packages found.")
                    continue
                
                print("\nExisting packages:")
                for package in packages:
                    print(f"- {package.name}")
            
            elif choice == '3':
                print("Exiting...")
                break
            
            else:
                print("Invalid option. Please select 1, 2, or 3.")
                
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"Error: {str(e)}")

def main():
    # Check if Tkinter is available
    if check_tkinter():
        import tkinter as tk
        root = tk.Tk()
        app = PackageGeneratorApp(root)
        
        # Keep the console window open to display errors
        try:
            root.mainloop()
        except Exception as e:
            print(f"Error in GUI: {str(e)}")
            input("Press Enter to exit...")
    else:
        print("Tkinter is not available. Falling back to command-line mode.")
        run_cli_mode()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Critical error: {str(e)}")
        print("The application failed to start.")
        input("Press Enter to exit...") 