"""Frame-exact spectral skull choreography on a real transparent canvas.

Every frame is a pure function of a normalized timestamp; no simulation step,
random draw, font, GPU, or window is required at render time.
"""
from __future__ import annotations
import math
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy.spatial import Delaunay
from .matte import cutout

DURATION = 6.0
TAU = math.tau


def clamp(x): return max(0.0, min(1.0,float(x)))
def ease(x):
    x=clamp(x)
    return x*x*(3-2*x)
def mix(a,b,p): return a+(b-a)*p


def _smoke_ghost(size:int, variant:int) -> Image.Image:
    """Draw a luminous screaming wraith with flowing tendrils, ink mouth and eyes."""
    s=size; scale=s/240
    rng=np.random.default_rng(500+variant)
    base=Image.new('RGBA',(s,s),'#00000000')
    glow=Image.new('RGBA',(s,s),'#00000000')
    d=ImageDraw.Draw(base,'RGBA'); g=ImageDraw.Draw(glow,'RGBA')
    def p(x,y):return (round(x*scale),round(y*scale))
    def poly(points):return [p(x,y) for x,y in points]
    # Layered smoke plumes form a wispy body, never a simple sheet ghost.
    for k in range(42):
        y=55+k*3.7
        x=115+math.sin(k*.37+variant)*19
        width=(45+22*math.sin(k*.21+1))*(1-k/65)
        left=x-width +rng.normal(0,7)
        right=x+width+rng.normal(0,7)
        opacity=max(3,int((24-k*.37)))
        col=(80+int(25*(k%3==0)),226,211,opacity)
        g.line(poly([(left,y),(x-21,y+9),(x+5,y+12),(right,y-4)]),fill=col,width=max(1,round(12*scale)),joint='curve')
    # Long hooks and ragged lower vapor ribbons.
    for j in range(24):
        x0=60+(j%9)*14
        y0=132+(j%5)*11
        side=(-1 if j%2 else 1)
        pts=[]
        for n in range(26):
            t=n/25
            x=x0+side*(25+28*math.sin(t*math.pi))*t+math.sin(t*12+j)*6*t
            y=y0+95*t+math.sin(t*8+j)*13*t
            pts.append(p(x,y))
        g.line(pts,fill=(54,243,219,max(8,57-j)),width=max(1,round((5-j/9)*scale)),joint='curve')
        d.line(pts,fill=(162,254,240,max(8,41-j)),width=max(1,round((2-j/18)*scale)))
    # Dark head / occult halo silhouette.
    d.ellipse((p(57,23),p(185,155)),fill=(18,48,52,98),outline=(106,244,230,148),width=max(1,round(3*scale)))
    d.ellipse((p(75,39),p(175,152)),fill=(16,31,41,168))
    # Disordered living hair tendrils rising outward from the head.
    for j in range(33):
        a=(j/32)*math.pi*1.5 + math.pi*.7
        x0=125+51*math.cos(a);y0=91+64*math.sin(a)
        pts=[]
        for n in range(22):
            t=n/21
            x=x0+(20+30*math.sin(j*3))*math.cos(a)*t+13*math.sin(t*11+j)*t
            y=y0+(20+20*math.cos(j*2))*math.sin(a)*t-12*math.sin(7*t+j)*t
            pts.append(p(x,y))
        g.line(pts,fill=(56,222,215,40),width=max(1,round(6*scale)))
        d.line(pts,fill=(169,255,241,80),width=max(1,round(1.7*scale)))
    # Screaming jaw: elongated black abyss and multiple needle-like teeth.
    d.ellipse((p(103,95),p(153,163)),fill=(0,8,17,233),outline=(150,252,232,184),width=max(1,round(3*scale)))
    d.polygon(poly([(109,102),(118,134),(123,109),(130,140),(137,106),(148,102),(143,150),(128,166),(112,145)]),fill=(0,9,16,214))
    for j in range(7):
        x=108+j*6
        d.line([p(x,100),p(x+2,112+(j%3)*7)],fill=(196,255,246,194),width=max(1,round(2*scale)))
    # Glowing asymmetrical eyes; glows on their own layer.
    for x,y,r in [(98,87,11),(155,83,9)]:
        g.ellipse((p(x-r*2,y-r*2),p(x+r*2,y+r*2)),fill=(93,255,235,116))
        d.ellipse((p(x-r,y-r),p(x+r,y+r)),fill=(207,255,249,236))
        d.ellipse((p(x-r/2,y-r/2),p(x+r/2,y+r/2)),fill=(255,255,255,255))
    halo=glow.filter(ImageFilter.GaussianBlur(max(2,round(7*scale))))
    halo.alpha_composite(glow)
    halo.alpha_composite(base)
    return halo


class Scene:
    def __init__(self, source: str | Path | Image.Image, size: int=768, seed:int=42):
        if size<192 or size>2048: raise ValueError('size must be 192..2048')
        self.size=size; self.seed=seed
        self.asset=cutout(str(source) if isinstance(source,Path) else source)
        w,h=self.asset.size
        limit=int(size*.77)
        k=min(limit/w,limit/h)
        self.art=self.asset.resize((round(w*k),round(h*k)),Image.Resampling.LANCZOS)
        self.center=(size//2,size//2)
        self.artpos=((size-self.art.width)//2,(size-self.art.height)//2)
        self.ghosts=[_smoke_ghost(max(130,round(size*.29)),i) for i in range(4)]
        self.shards=self._make_shards()
        rng=np.random.default_rng(seed)
        self.stars=[(rng.uniform(0,TAU), rng.uniform(35,size*.52),rng.uniform(1,3.2),rng.uniform(0,TAU)) for _ in range(170)]

    def _make_shards(self):
        w,h=self.art.size
        rng=np.random.default_rng(self.seed)
        # A seeded Delaunay glass mesh: every pixel belongs to original art.
        xx=np.linspace(-7,w+7,8); yy=np.linspace(-7,h+7,8)
        points=[]
        for j,y in enumerate(yy):
            for i,x in enumerate(xx):
                wiggle_x=0 if i in (0,len(xx)-1) else rng.uniform(-18,18)
                wiggle_y=0 if j in (0,len(yy)-1) else rng.uniform(-18,18)
                points.append((x+wiggle_x,y+wiggle_y))
        mesh=Delaunay(np.asarray(points))
        shards=[]
        for index,ids in enumerate(mesh.simplices):
            poly=np.asarray(points)[ids]
            x0=max(0,int(math.floor(poly[:,0].min()))-2); x1=min(w,int(math.ceil(poly[:,0].max()))+3)
            y0=max(0,int(math.floor(poly[:,1].min()))-2); y1=min(h,int(math.ceil(poly[:,1].max()))+3)
            if x0>=x1 or y0>=y1:continue
            mask=np.zeros((y1-y0,x1-x0),np.uint8)
            cv2.fillConvexPoly(mask,np.rint(poly-[x0,y0]).astype(np.int32),255, cv2.LINE_AA)
            patch=np.asarray(self.art.crop((x0,y0,x1,y1))).copy()
            patch[:,:,3]=(patch[:,:,3].astype('uint16')*mask//255).astype('uint8')
            if patch[:,:,3].max()==0:continue
            center=(x0+x1)/2, (y0+y1)/2
            theta=math.atan2(center[1]-h/2,center[0]-w/2)
            shards.append((Image.fromarray(patch,'RGBA'),center,theta, float(rng.uniform(-1,1)), float(rng.uniform(.76,1.25)),index))
        return shards

    def _overlay(self,canvas, sprite, at, scale=1.0, angle=0,opacity=1.0):
        if opacity<=0 or scale<=0:return
        if abs(scale-1)>.005:
            sprite=sprite.resize((max(1,round(sprite.width*scale)),max(1,round(sprite.height*scale))),Image.Resampling.BICUBIC)
        if angle:
            sprite=sprite.rotate(angle,Image.Resampling.BICUBIC,expand=True)
        if opacity<.995:
            a=sprite.getchannel('A').point(lambda v:int(v*opacity))
            sprite.putalpha(a)
        pos=(round(at[0]-sprite.width/2),round(at[1]-sprite.height/2))
        canvas.alpha_composite(sprite,pos)

    def _halo(self, canvas, t):
        if not (.20<t<.96):return
        s=self.size; cx=cy=s/2
        layer=Image.new('RGBA',(s,s)); d=ImageDraw.Draw(layer,'RGBA')
        power=min(ease((t-.2)/.11),ease((.97-t)/.15))
        for j in range(8):
            r=s*(.16+j*.057+ .015*math.sin(t*TAU*3+j))
            start=math.degrees(t*TAU*(1.4+j*.05))+j*46
            col=(65+int(j*6),245,227,round((70-j*6)*power))
            d.arc((cx-r,cy-r,cx+r,cy+r),start,start+175-8*j,fill=col,width=max(1,int(s*(.004-j*.0002))))
        blur=layer.filter(ImageFilter.GaussianBlur(max(3,s//65)))
        canvas.alpha_composite(blur)
        canvas.alpha_composite(layer)

    def _stardust(self, canvas,t):
        if t<.22 or t>.98:return
        s=self.size;cx=cy=s/2
        d=ImageDraw.Draw(canvas,'RGBA')
        power=min(ease((t-.22)/.12),ease((.98-t)/.15))
        for i,(theta,r,rad,phase) in enumerate(self.stars):
            a=theta + TAU*(t*1.15) + .14*math.sin(t*TAU*3+phase)
            radius = r*(.35+.6*ease((t-.26)/.29))
            x=cx+math.cos(a)*radius; y=cy+math.sin(a)*radius*.84
            pulse=.5+.5*math.sin(t*TAU*6+phase)
            R=max(.6,rad*(.7+pulse))
            alpha=int(200*power*(.35+.65*pulse))
            c=(124,255,239,alpha) if i%3 else (255,213,125,alpha)
            d.ellipse((x-R,y-R,x+R,y+R),fill=c)
            if i%13==0:
                d.line([(x-R*3,y),(x+R*3,y)],fill=(169,253,247,alpha//2),width=1)
                d.line([(x,y-R*3),(x,y+R*3)],fill=(169,253,247,alpha//2),width=1)

    def _draw_shards(self,canvas,t):
        s=self.size;cx=cy=s/2
        if t<.285 or t>=.982:return
        out=ease((t-.285)/.16)
        vortex=ease((t-.58)/.17)
        reform=ease((t-.78)/.195)
        # Intact source dissolves into precise triangular pieces, then reforms.
        for patch,(x,y),theta,twist,variation,index in self.shards:
            origin=(self.artpos[0]+x,self.artpos[1]+y)
            dist=math.hypot(origin[0]-cx, origin[1]-cy)
            angle=theta+.55*twist
            radius=s*(.13+.30*variation) * out
            explode=(origin[0]+radius*math.cos(angle),origin[1]+radius*math.sin(angle))
            orbit=TAU*(t-.58)*2.2 + index*2.39996323 + theta
            ring=s*(.20+.17*(.5+.5*math.sin(index*2.0)))
            cyclone=(cx+math.cos(orbit)*ring,cy+math.sin(orbit)*ring*.75)
            x1=mix(explode[0],cyclone[0],vortex)
            y1=mix(explode[1],cyclone[1],vortex)
            pos=(mix(x1,origin[0],reform),mix(y1,origin[1],reform))
            rotation=(out*(25+120*variation)*twist + vortex*(t-.58)*580) * (1-reform)
            sc=(1-.28*vortex)*(1-reform)+reform
            self._overlay(canvas,patch,pos,sc,rotation,1)

    def _draw_ghosts(self,canvas,t):
        if t<.36 or t>.935:return
        s=self.size;cx=cy=s/2
        for j,sprite in enumerate(self.ghosts):
            beginning=.365 + j*.027
            flight=ease((t-beginning)/.19)
            back=ease((t-.675-j*.018)/.22)
            if flight<=0 or back>=1:continue
            offsets=[(-.33,-.29),(.42,-.25),(.31,.22),(-.37,.19)]
            tx,ty=offsets[j]
            origin=(cx+s*.16,cy-s*.14)
            endpoint=(cx+s*tx,cy+s*ty)
            spiral_angle=TAU*(1.5*(t-.66))+j*TAU/4
            inward=(cx+s*(.27*(1-back))*math.cos(spiral_angle),cy+s*(.27*(1-back))*math.sin(spiral_angle))
            first=(mix(origin[0],endpoint[0],flight),mix(origin[1],endpoint[1],flight))
            pos=(mix(first[0],inward[0],back),mix(first[1],inward[1],back))
            alpha=ease((t-beginning)/.055)*min(1,ease((.935-t)/.085))
            sz=(.75+.22*math.sin(flight*math.pi))*(1-.65*back)
            ang=10*math.sin(t*21+j*2)+back*720
            self._overlay(canvas,sprite,pos,sz,ang,alpha*.93)
            # Visible scream shockwaves escape each wraith at peak of flight.
            scream=min(ease((t-.46)/.075),ease((.68-t)/.07))*(1-back)
            if scream>0:
                layer=Image.new('RGBA',(s,s)); d=ImageDraw.Draw(layer,'RGBA')
                for k in range(3):
                    rr=s*(.045 + ((t*3.2 + j*.31+k*.33)%1)*.13)
                    a=round((1-rr/(s*.20))*120*scream)
                    if a>0:
                        d.arc((pos[0]-rr,pos[1]-rr,pos[0]+rr,pos[1]+rr),-65,80,fill=(137,255,236,a),width=max(1,s//250))
                canvas.alpha_composite(layer)

    def _spin(self, canvas,t):
        s=self.size
        # This is a strictly image-faithful full 360-degree screen-plane spin;
        # a real 3D back face cannot be recovered from a single source image.
        turn=ease(t/.285)*360
        base=Image.new('RGBA',(s,s))
        base.alpha_composite(self.art,self.artpos)
        spin=base.rotate(-turn,Image.Resampling.BICUBIC,expand=False)
        # Oscillating refractive glint behind its crystalline surface.
        self._overlay(canvas,spin,self.center,1+.025*math.sin(TAU*t*4),0,1)

    def frame(self, index:int, fps:int=25) -> Image.Image:
        if fps<1:raise ValueError('fps must be positive')
        return self.image(index/fps)

    def image(self, seconds:float) -> Image.Image:
        t=(seconds%DURATION)/DURATION
        # Last frames return to the reference skull, with a moving glint
        # that prevents indexed GIF exports from merging duplicate frames.
        if t>=.955:
            restored=Image.new('RGBA',(self.size,self.size))
            restored.alpha_composite(self.art,self.artpos)
            if t < .99:
                q=(t-.955)/.035
                x=round(self.size*(.31+.29*q))
                y=round(self.size*(.62-.025*math.sin(q*math.pi)))
                r=max(2,self.size//160)
                d=ImageDraw.Draw(restored,'RGBA')
                d.line([(x-r*2,y),(x+r*2,y)],fill=(255,238,181,230),width=2)
                d.line([(x,y-r*2),(x,y+r*2)],fill=(255,238,181,230),width=2)
                d.ellipse((x-r,y-r,x+r,y+r),fill=(255,255,250,255))
            return restored
        canvas=Image.new('RGBA',(self.size,self.size))
        self._halo(canvas,t)
        if t<.285:
            self._spin(canvas,t)
        else:
            self._draw_shards(canvas,t)
        self._draw_ghosts(canvas,t)
        self._stardust(canvas,t)
        if .962<t<1:
            # Crossfade back to a pixel-identical fully restored original.
            restored=Image.new('RGBA',(self.size,self.size));restored.alpha_composite(self.art,self.artpos)
            a=ease((t-.962)/.038)
            restored.putalpha(restored.getchannel('A').point(lambda q:round(q*a)))
            canvas.alpha_composite(restored)
        return canvas