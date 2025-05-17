#!/usr/bin/env python3
"""
Test runner script for OTA daemon.

This script runs all unit and integration tests and generates
a coverage report.
"""

import os
import sys
import unittest
import coverage

def run_tests():
    """Run all tests with coverage reporting."""
    # Start code coverage
    cov = coverage.Coverage(
        source=["OTA.daemon"],
        omit=[
            "*/tests/*",
            "*/__pycache__/*",
            "*/site-packages/*"
        ]
    )
    cov.start()
    
    try:
        # Discover and run tests
        loader = unittest.TestLoader()
        tests = loader.discover(start_dir=os.path.dirname(__file__), pattern="test_*.py")
        
        # Create a test runner
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(tests)
        
        # Stop coverage
        cov.stop()
        cov.save()
        
        # Print coverage report
        print("\nCoverage Report:")
        cov.report()
        
        # Generate HTML report
        report_dir = os.path.join(os.path.dirname(__file__), "coverage_html")
        if not os.path.exists(report_dir):
            os.makedirs(report_dir)
        
        cov.html_report(directory=report_dir)
        print(f"\nHTML coverage report generated in: {report_dir}")
        
        # Return exit code based on test results
        return 0 if result.wasSuccessful() else 1
    
    except KeyboardInterrupt:
        print("\nTests interrupted by user.")
        return 1

if __name__ == "__main__":
    sys.exit(run_tests()) 