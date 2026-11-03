#!/usr/bin/env python3
"""
Runner für Controller-Integration in server.py
Wird von server.py aufgerufen: python controller_runner.py paths... --output outdir
"""
import sys
import subprocess
from pathlib import Path

def main():
    # controller.py erwartet: captures... --output OUTPUT [--voxel VOXEL]
    args = sys.argv[1:]
    if not args:
        print("Usage: controller_runner.py <capture1> <capture2> [capture3] --output <dir>", file=sys.stderr)
        sys.exit(1)
    
    cmd = [sys.executable, str(Path(__file__).with_name('controller.py'))] + args
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=7200)
    
    # Konsolenausgabe direkt weiterleiten (wie lidarmonk_backend.py)
    sys.stdout.write(result.stdout)
    sys.stderr.write(result.stderr)
    
    return result.returncode

if __name__ == '__main__':
    sys.exit(main())