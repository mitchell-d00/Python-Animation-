"""Command line export and optional real-time preview."""
import argparse
import json
import os
from pathlib import Path


def preview(supersample,seed):
    import pygame
    from .scene import Scene,W,H
    pygame.display.init()
    screen=pygame.display.set_mode((W,H))
    pygame.display.set_caption('Boo-gie Nights | Space: pause  R: restart  Esc: quit')
    scene=Scene(supersample,seed)
    clock=pygame.time.Clock();t=0;paused=False
    try:
        while True:
            dt=clock.tick(60)/1000
            for e in pygame.event.get():
                if e.type==pygame.QUIT:return
                if e.type==pygame.KEYDOWN:
                    if e.key in (pygame.K_ESCAPE,pygame.K_q):return
                    if e.key==pygame.K_SPACE:paused=not paused
                    if e.key==pygame.K_r:t=0
            if not paused:t+=dt
            pygame.transform.smoothscale(scene.draw(t),(W,H),screen)
            pygame.display.flip()
    finally:
        pygame.quit()


def main(argv=None):
    p=argparse.ArgumentParser(description='Procedural sheet-ghost dance. No external art assets.')
    p.add_argument('output',nargs='?',default='ghost_dance.gif',type=Path)
    p.add_argument('--preview',action='store_true',help='Live pygame window; Space pauses, R restarts')
    p.add_argument('--width',type=int,default=640,help='GIF width, 160–1920; height is 3/4 of width')
    p.add_argument('--fps',type=int,choices=(10,20,25,50),default=25)
    p.add_argument('--supersample',type=int,choices=(1,2,3,4),default=2)
    p.add_argument('--seed',type=int,default=7)
    p.add_argument('--poster',type=Path,help='Also save a PNG at the disco pose')
    args=p.parse_args(argv)
    if not 160<=args.width<=1920:p.error('--width must be 160–1920')
    if not args.preview and args.output.suffix.lower()!='.gif':p.error('output must end in .gif')
    os.environ.setdefault('PYGAME_HIDE_SUPPORT_PROMPT','1')
    if not args.preview:os.environ.setdefault('SDL_VIDEODRIVER','dummy')
    try:
        if args.preview:preview(args.supersample,args.seed)
        else:
            from .export import render_gif
            print(json.dumps(render_gif(args.output,args.width,args.fps,args.supersample,args.seed),indent=2))
        if args.poster:
            from .scene import Scene
            args.poster.parent.mkdir(parents=True,exist_ok=True)
            Scene(args.supersample,args.seed).image(5.0,args.width).save(args.poster)
    except (OSError,ValueError) as exc:
        p.exit(1,f'ghost-party: {exc}\n')
    return 0
