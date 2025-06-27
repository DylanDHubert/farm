#!/usr/bin/env python3
"""
Launcher script for the PB&J RAG Streamlit app.
This script properly sets up the Python path and runs the app.
"""

import sys
import subprocess
from pathlib import Path

def main():
    # Get the project root
    project_root = Path(__file__).parent
    app_path = project_root / "app" / "streamlit_app.py"
    
    # Set the PYTHONPATH environment variable
    env = os.environ.copy()
    env['PYTHONPATH'] = str(project_root / "src")
    
    # Run streamlit
    cmd = [
        sys.executable, "-m", "streamlit", "run", 
        str(app_path),
        "--server.headless", "true",
        "--server.port", "8507"
    ]
    
    print("🚀 Starting PB&J RAG Streamlit app...")
    print(f"📁 Project root: {project_root}")
    print(f"📁 App path: {app_path}")
    print(f"🔧 Python path: {env['PYTHONPATH']}")
    print("\n🌐 App will be available at: http://localhost:8507")
    print("Press Ctrl+C to stop the app\n")
    
    try:
        subprocess.run(cmd, env=env, check=True)
    except KeyboardInterrupt:
        print("\n👋 App stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running app: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    import os
    sys.exit(main()) 