"""Bounded-memory, shared-palette GIF export with exact centisecond timing."""
from __future__ import annotations
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from PIL import Image
from .scene import Scene, DURATION


def render_gif(path='ghost_dance.gif', width=640, fps=25, supersample=2, seed=7):
    if fps not in (10,20,25,50):
        raise ValueError('GIF fps must be 10, 20, 25, or 50 for exact timing')
    if not 160<=width<=1920:
        raise ValueError('width must be between 160 and 1920')
    path=Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    scene=Scene(supersample,seed)
    count=round(DURATION*fps)
    height=round(width*.75)
    # All choreography phases contribute to one palette, preventing palette flicker.
    atlas=Image.new('RGB',(240*6,180*4))
    for i in range(24):
        atlas.paste(scene.image(i*DURATION/24,240),((i%6)*240,(i//6)*180))
    palette=atlas.quantize(colors=256,method=Image.Quantize.MEDIANCUT)
    # RGB frames are immediately quantized; only compact palette frames are retained.
    frames=[]
    for i in range(count):
        frame=scene.image(i/fps,width).quantize(palette=palette,dither=Image.Dither.NONE)
        frames.append(frame)
        if i%fps==0:
            print(f'Rendering {i//fps:2d}/{int(DURATION)} seconds',flush=True)
    # Atomic destination replacement: a failed render never truncates a prior GIF.
    with TemporaryDirectory(prefix='.ghost-',dir=path.parent) as tmp:
        staged=Path(tmp)/'render.gif'
        frames[0].save(staged,save_all=True,append_images=frames[1:],duration=1000//fps,
                       loop=0,optimize=False,disposal=1,comment=b'Entirely procedural: pygame + Pillow')
        verify_gif(staged,count,(width,height))
        os.replace(staged,path)
    return {'path':str(path),'frames':count,'duration_ms':int(DURATION*1000),
            'width':width,'height':height,'bytes':path.stat().st_size}


def verify_gif(path,expected_frames=None,expected_size=None):
    with Image.open(path) as gif:
        if gif.info.get('loop') != 0:
            raise ValueError('GIF must loop indefinitely')
        if expected_frames is not None and gif.n_frames != expected_frames:
            raise ValueError(f'Expected {expected_frames} frames, got {gif.n_frames}')
        if expected_size is not None and gif.size != expected_size:
            raise ValueError(f'Expected dimensions {expected_size}, got {gif.size}')
        duration=0
        for i in range(gif.n_frames):
            gif.seek(i);gif.load();duration+=gif.info['duration']
        if duration != int(DURATION*1000):
            raise ValueError(f'Incorrect total duration: {duration}')
        return {'frames':gif.n_frames,'size':gif.size,'duration_ms':duration,'loop':0}
