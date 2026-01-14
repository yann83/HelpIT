"""
Installation Verification Script for ProcessManager Module

This script checks if all required files and dependencies are properly installed.
Run this script before using the ProcessManager module to ensure everything is set up correctly.

Usage:
    python verify_installation.py
"""

import sys
import os
from pathlib import Path


class InstallationVerifier:
    """
    Verify that all required components for ProcessManager are installed
    """

    def __init__(self):
        """Initialize the verifier"""
        self.errors = []
        self.warnings = []
        self.success_count = 0
        self.total_checks = 0

    def check_python_version(self):
        """Check if Python version is 3.6 or higher"""
        self.total_checks += 1
        print("Checking Python version...", end=" ")
        
        version = sys.version_info
        if version.major >= 3 and version.minor >= 6:
            print("✓ OK")
            print(f"  Python {version.major}.{version.minor}.{version.micro}")
            self.success_count += 1
            return True
        else:
            print("✗ FAIL")
            self.errors.append(f"Python version {version.major}.{version.minor} is too old. Requires 3.6+")
            return False

    def check_file_exists(self, filepath, description, critical=True):
        """
        Check if a file exists
        
        Args:
            filepath (str or Path): Path to check
            description (str): Description of the file
            critical (bool): Whether this is a critical file
        """
        self.total_checks += 1
        print(f"Checking {description}...", end=" ")
        
        if Path(filepath).exists():
            print("✓ OK")
            print(f"  {filepath}")
            self.success_count += 1
            return True
        else:
            print("✗ MISSING")
            if critical:
                self.errors.append(f"Missing file: {filepath} ({description})")
            else:
                self.warnings.append(f"Missing file: {filepath} ({description})")
            return False

    def check_import(self, module_name, description):
        """
        Check if a module can be imported
        
        Args:
            module_name (str): Name of the module to import
            description (str): Description of the module
        """
        self.total_checks += 1
        print(f"Checking {description}...", end=" ")
        
        try:
            __import__(module_name)
            print("✓ OK")
            self.success_count += 1
            return True
        except ImportError as e:
            print("✗ FAIL")
            self.errors.append(f"Cannot import {module_name}: {e}")
            return False

    def check_directory(self, dirpath, description, create_if_missing=False):
        """
        Check if a directory exists
        
        Args:
            dirpath (str or Path): Path to check
            description (str): Description of the directory
            create_if_missing (bool): Create the directory if it doesn't exist
        """
        self.total_checks += 1
        print(f"Checking {description}...", end=" ")
        
        path = Path(dirpath)
        if path.exists() and path.is_dir():
            print("✓ OK")
            self.success_count += 1
            return True
        else:
            if create_if_missing:
                try:
                    path.mkdir(parents=True, exist_ok=True)
                    print("✓ CREATED")
                    self.success_count += 1
                    return True
                except Exception as e:
                    print("✗ FAIL")
                    self.errors.append(f"Cannot create directory {dirpath}: {e}")
                    return False
            else:
                print("✗ MISSING")
                self.warnings.append(f"Missing directory: {dirpath} ({description})")
                return False

    def verify_all(self):
        """Run all verification checks"""
        print("=" * 60)
        print("ProcessManager Installation Verification")
        print("=" * 60)
        print()

        # Check Python version
        self.check_python_version()
        print()

        # Check required Python modules
        print("Checking Python modules...")
        self.check_import("tkinter", "Tkinter GUI library")
        self.check_import("csv", "CSV module")
        self.check_import("logging", "Logging module")
        self.check_import("pathlib", "Pathlib module")
        print()

        # Get script directory (where verify_installation.py is located)
        script_dir = Path(__file__).parent

        # Check required Python files
        print("Checking required Python files...")
        self.check_file_exists(script_dir / "main.py", "Main application file")
        self.check_file_exists(script_dir / "process.py", "ProcessManager module")
        self.check_file_exists(script_dir / "psexec.py", "PsExec manager module")
        self.check_file_exists(script_dir / "credential.py", "Credential module")
        print()

        # Check directories
        print("Checking directories...")
        self.check_directory(script_dir / "bin", "Binary tools directory")
        self.check_directory(script_dir / "tmp", "Temporary files directory", create_if_missing=True)
        print()

        # Check PsExec executable
        print("Checking external tools...")
        psexec_path = script_dir / "bin" / "PsExec64.exe"
        if self.check_file_exists(psexec_path, "PsExec64.exe", critical=True):
            # Check if it's executable
            if os.access(psexec_path, os.X_OK) or sys.platform == 'win32':
                print("  ✓ PsExec64.exe is executable")
            else:
                self.warnings.append("PsExec64.exe may not be executable")
        print()

        # Check optional files
        print("Checking optional files...")
        self.check_file_exists(script_dir / "config.json", "Configuration file", critical=False)
        self.check_file_exists(script_dir / "README.md", "README documentation", critical=False)
        print()

        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print verification summary"""
        print("=" * 60)
        print("VERIFICATION SUMMARY")
        print("=" * 60)
        print(f"Total checks: {self.total_checks}")
        print(f"Successful: {self.success_count}")
        print(f"Failed: {len(self.errors)}")
        print(f"Warnings: {len(self.warnings)}")
        print()

        if self.errors:
            print("❌ ERRORS (must be fixed):")
            for i, error in enumerate(self.errors, 1):
                print(f"  {i}. {error}")
            print()

        if self.warnings:
            print("⚠️  WARNINGS (recommended to fix):")
            for i, warning in enumerate(self.warnings, 1):
                print(f"  {i}. {warning}")
            print()

        if not self.errors and not self.warnings:
            print("✅ ALL CHECKS PASSED!")
            print("Your installation is complete and ready to use.")
        elif not self.errors:
            print("✅ INSTALLATION OK (with warnings)")
            print("Your installation is functional but some optional components are missing.")
        else:
            print("❌ INSTALLATION INCOMPLETE")
            print("Please fix the errors above before using ProcessManager.")
        
        print()
        print("=" * 60)

        # Return exit code
        return 0 if not self.errors else 1


def main():
    """Main function"""
    verifier = InstallationVerifier()
    exit_code = verifier.verify_all()
    
    # Additional help
    if exit_code != 0:
        print("\nNeed help?")
        print("- Check INSTALLATION.md for setup instructions")
        print("- Check README.md for usage documentation")
        print("- Check DOCUMENTATION_FR.md for French documentation")
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
