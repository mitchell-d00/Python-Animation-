"""Command-line entry point for reproducible transparent spectral skull renders."""
import argparse
import json
from pathlib import Path
from .export import render

def main(argv=None):
    p=argparse.ArgumentParser(description='Spin, explode, and reform your original skull in a transparent vortex')
    p.add_argument('--source',type=Path,default=Path(__file__).with_name('assets_source.jpg'))
    p.add_argument('--output',default='renders/spectral_skull.gif')
    p.add_argument('--size',type=int,default=768)
    p.add_argument('--fps',type=int,default=25)
    p.add_argument('--seed',type=int,default=42)
    p.add_argument('--frames-dir',default=None)
    p.add_argument('--apng',default=None,help='Also export APNG preserving full 8-bit alpha')
    p.add_argument('--no-gif',action='store_true')
    a=p.parse_args(argv)
    if not a.source.exists():p.error(f'source image not found: {a.source}')
    print(json.dumps(render(a.source,a.output,a.size,a.fps,a.seed,a.frames_dir,a.apng,not a.no_gif),indent=2))
if __name__=='__main__':main()
