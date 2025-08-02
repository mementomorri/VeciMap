#!/usr/bin/env python3
"""
Test script to verify ferias-cli installation and dependencies.
"""

import sys
import importlib

def test_import(module_name, package_name=None):
    """Test if a module can be imported."""
    try:
        importlib.import_module(module_name)
        print(f"✅ {package_name or module_name} - OK")
        return True
    except ImportError as e:
        print(f"❌ {package_name or module_name} - FAILED: {e}")
        return False

def main():
    """Test all required dependencies."""
    print("Testing ferias-cli installation...\n")
    
    # Test Python dependencies
    print("Python Dependencies:")
    dependencies = [
        ('requests', 'requests'),
        ('bs4', 'beautifulsoup4'),
        ('lxml', 'lxml'),
        ('folium', 'folium'),
        ('geopy', 'geopy'),
        ('click', 'click'),
        ('tqdm', 'tqdm')
    ]
    
    all_python_ok = True
    for module, package in dependencies:
        if not test_import(module, package):
            all_python_ok = False
    
    print()
    
    # Test Node.js availability
    print("Node.js Dependencies:")
    try:
        import subprocess
        result = subprocess.run(['node', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Node.js - OK (version: {result.stdout.strip()})")
            node_ok = True
        else:
            print("❌ Node.js - FAILED: Not available")
            node_ok = False
    except FileNotFoundError:
        print("❌ Node.js - FAILED: Not installed")
        node_ok = False
    
    # Test npm availability
    try:
        result = subprocess.run(['npm', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ npm - OK (version: {result.stdout.strip()})")
            npm_ok = True
        else:
            print("❌ npm - FAILED: Not available")
            npm_ok = False
    except FileNotFoundError:
        print("❌ npm - FAILED: Not installed")
        npm_ok = False
    
    print()
    
    # Test script files
    print("Script Files:")
    import os
    
    scripts = ['scrape_ferias_json.py', 'generate_ferias_map.py']
    all_scripts_ok = True
    
    for script in scripts:
        if os.path.exists(script):
            print(f"✅ {script} - OK")
        else:
            print(f"❌ {script} - MISSING")
            all_scripts_ok = False
    
    print()
    
    # Summary
    print("Installation Summary:")
    if all_python_ok:
        print("✅ Python dependencies: All installed")
    else:
        print("❌ Python dependencies: Some missing - run 'pip install -r requirements.txt'")
    
    if node_ok and npm_ok:
        print("✅ Node.js dependencies: Available for PNG snapshots")
    else:
        print("⚠️  Node.js dependencies: Not available (PNG snapshots will not work)")
    
    if all_scripts_ok:
        print("✅ Script files: All present")
    else:
        print("❌ Script files: Some missing")
    
    print()
    
    if all_python_ok and all_scripts_ok:
        print("🎉 ferias-cli is ready to use!")
        print("\nQuick start:")
        print("  python scrape_ferias_json.py --help")
        print("  python generate_ferias_map.py --help")
    else:
        print("⚠️  Please fix the issues above before using ferias-cli")

if __name__ == '__main__':
    main() 