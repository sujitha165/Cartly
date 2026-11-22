"""
Cartly Launcher Script
Convenience entry point to run the Streamlit web application.
Usage:
    python run_cartly.py
"""

import os
import sys
import subprocess

if __name__ == "__main__":
    app_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app", "main.py")
    cmd = [sys.executable, "-m", "streamlit", "run", app_path]
    print(f"Starting Cartly on Streamlit... ({' '.join(cmd)})")
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\nCartly application stopped.")
