#!/usr/bin/env python3
"""
Quick verification script for SecureLocalAgentSandbox
Checks all files exist and basic syntax is correct
"""

import os
import sys
import json
import ast

def check_file_exists(filepath, description):
    """Check if a file exists and report."""
    exists = os.path.isfile(filepath)
    status = "✓" if exists else "✗"
    print(f"  {status} {filepath} - {description}")
    return exists

def check_python_syntax(filepath):
    """Check if Python file has valid syntax."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            ast.parse(f.read())
        return True
    except SyntaxError as e:
        print(f"      Syntax Error: {e}")
        return False
    except Exception as e:
        print(f"      Error: {e}")
        return False

def check_json_syntax(filepath):
    """Check if JSON file has valid syntax."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            json.load(f)
        return True
    except json.JSONDecodeError as e:
        print(f"      JSON Error: {e}")
        return False

def verify_project():
    """Verify the project structure and files."""
    
    print("=" * 60)
    print("SecureLocalAgentSandbox - Project Verification")
    print("=" * 60)
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(base_dir)
    
    all_good = True
    
    print("\n📋 Checking Core Files:")
    files_to_check = [
        ("app.py", "FastAPI Server"),
        ("sandbox.py", "Docker Orchestration"),
        ("agent.py", "AI Agent Integration"),
        ("test.py", "Test Suite"),
        ("requirements.txt", "Python Dependencies"),
        ("Dockerfile", "Container Image"),
        (".env.example", "Environment Template"),
        ("README.md", "Documentation"),
        ("IMPROVEMENTS.md", "Improvement Log"),
    ]
    
    for filepath, description in files_to_check:
        exists = check_file_exists(filepath, description)
        if not exists:
            all_good = False
        elif filepath.endswith('.py'):
            if check_python_syntax(filepath):
                print(f"      ✓ Valid Python syntax")
            else:
                print(f"      ✗ Invalid Python syntax")
                all_good = False
    
    print("\n📁 Checking Project Structure:")
    dirs_to_check = [
        "workspaces",
    ]
    
    for dirname in dirs_to_check:
        exists = os.path.isdir(dirname)
        status = "✓" if exists else "⚠"
        print(f"  {status} {dirname}/ - {'exists' if exists else 'optional'}")
    
    print("\n📦 Checking Dependencies in requirements.txt:")
    try:
        with open("requirements.txt", "r") as f:
            deps = [line.strip() for line in f if line.strip() and not line.startswith("#")]
        print(f"  ✓ Found {len(deps)} dependencies:")
        for dep in deps:
            print(f"      • {dep}")
    except Exception as e:
        print(f"  ✗ Error reading requirements.txt: {e}")
        all_good = False
    
    print("\n🔍 Checking Configuration:")
    env_vars = [
        "OPENAI_API_KEY",
        "API_HOST",
        "API_PORT",
        "SANDBOX_MEMORY",
        "SANDBOX_CPUS",
        "SANDBOX_TIMEOUT"
    ]
    print(f"  ✓ Expected environment variables:")
    for var in env_vars:
        print(f"      • {var}")
    
    print("\n✅ Verification Summary:")
    if all_good:
        print("  ✓ All files present and valid!")
        print("  ✓ Project structure is complete!")
        print("\n🚀 Next Steps:")
        print("  1. Set up environment: cp .env.example .env")
        print("  2. Add OpenAI API key to .env file")
        print("  3. Install dependencies: pip install -r requirements.txt")
        print("  4. Build Docker image: docker build -t secure-sandbox-base .")
        print("  5. Run server: python app.py")
        print("  6. Run tests: python test.py")
    else:
        print("  ✗ Some issues found. Please review above.")
        return False
    
    print("\n" + "=" * 60)
    return True

if __name__ == "__main__":
    success = verify_project()
    sys.exit(0 if success else 1)
