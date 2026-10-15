"""Headless exporters: lossless PNG sequence and APNG + transparent GIF."""
from __future__ import annotations
from pathlib import Path
from PIL import Image
import numpy as np
from .scene import Scene, DURATION


def _indexed_rgba(frame:Image.Image, palette:Image.Image, threshold:int=96)->Image.Image:
    rgba=np.asarray(frame.convert('RGBA'))
    rgb=Image.fromarray(rgba[:,:,:3],'RGB')
    idx=np.asarray(rgb.quantize(palette=palette,dither=Image.Dither.NONE)).astype(np.uint16)+1
    idx[rgba[:,:,3]<threshold]=0
    pal=Image.fromarray(idx.astype('uint8'),'P')
    pal.putpalette([0,0,0]+palette.getpalette()[:765])
    pal.info['transparency']=0
    return pal


def render(source, output='renders/spectral_skull.gif', size=768, fps=25,
           seed=42, frames_dir=None, apng=None, gif=True, verbose=True):
    """Produce every frame, deterministic and independently addressable.

    GIF transparency is binary by format design; PNG/APNG preserves 8-bit alpha.
    PNG frames are written individually so a render can be inspected/reused.
    """
    if fps not in (10,20,25,50):raise ValueError('GIF timing is exact only for fps 10, 20, 25, or 50')
    if not (192<=size<=2048):raise ValueError('size must be 192..2048')
    out=Path(output);out.parent.mkdir(parents=True,exist_ok=True)
    directory=Path(frames_dir) if frames_dir else out.parent/'spectral_skull_frames'
    directory.mkdir(parents=True,exist_ok=True)
    scene=Scene(source,size=size,seed=seed)
    count=round(DURATION*fps)
    for i in range(count):
        frame=scene.frame(i,fps)
        frame.save(directory/f'frame_{i:04d}.png',compress_level=6)
        if verbose and i%fps==0:print(f'Frames {i:03d}/{count} / {i//fps} seconds',flush=True)
    paths=sorted(directory.glob('frame_????.png'))
    if len(paths)!=count:raise RuntimeError(f'Incorrect frame count: {len(paths)} != {count}')
    # Build the GIF's global palette using all phases of the story.
    if gif:
        atlas=Image.new('RGB',(192*6,192*4),'black')
        for j in range(24):
            with Image.open(paths[j*count//24]) as f:
                thumb=f.convert('RGBA').resize((192,192),Image.Resampling.LANCZOS)
            panel=Image.new('RGB',(192,192),'black');panel.paste(thumb,mask=thumb.getchannel('A'))
            atlas.paste(panel,((j%6)*192,(j//6)*192))
        palette=atlas.quantize(colors=255,method=Image.Quantize.MEDIANCUT)
        palframes=[]
        for path in paths:
            with Image.open(path) as frame:palframes.append(_indexed_rgba(frame,palette))
        palframes[0].save(out,save_all=True,append_images=palframes[1:],duration=1000//fps,
                          loop=0,disposal=2,transparency=0,optimize=False)
        with Image.open(out) as check:
            if check.n_frames!=count:raise RuntimeError('GIF missing frames')
            if check.info.get('transparency')!=0:raise RuntimeError('GIF has no transparency index')
    if apng:
        p=Path(apng);p.parent.mkdir(parents=True,exist_ok=True)
        # PNG animation supports 256 alpha levels, unlike GIF.
        images=[]
        for path in paths:
            with Image.open(path) as f:images.append(f.convert('RGBA'))
        images[0].save(p,save_all=True,append_images=images[1:],duration=1000//fps,
                       loop=0,format='PNG',disposal=0,blend=0,compress_level=5)
    return {'frames':count,'size':size,'fps':fps,'seconds':DURATION,
            'gif':str(out) if gif else None,'frames_dir':str(directory),'apng':str(apng) if apng else None}