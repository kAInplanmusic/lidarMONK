#!/usr/bin/env python3
"""Prepare a standalone Docker Space source directory without credentials or scans."""
import argparse
import shutil
from pathlib import Path

here=Path(__file__).resolve().parent
backend=here.parent.parent/'backend'
p=argparse.ArgumentParser();p.add_argument('destination');a=p.parse_args()
out=Path(a.destination).resolve()
if out.exists() and any(out.iterdir()): raise SystemExit('Destination must be empty; refusing to overwrite.')
out.mkdir(parents=True,exist_ok=True)
for name in ['lidarmonk_backend.py','regional_tsdf.py','motion.py','server.py','requirements.txt']:
    shutil.copyfile(backend/name,out/name)
shutil.copyfile(here/'Dockerfile',out/'Dockerfile')
shutil.copyfile(here/'SPACE_README.md',out/'README.md')
print('Prepared',out)
