"""Deterministic procedural stage, cloth, skeleton rig, and choreography.

Coordinates use a 960 × 720 design space; Canvas supersamples every primitive.
No external artwork, fonts, numpy, image models, or network access are needed.
"""
from __future__ import annotations

import math
import os
import random

os.environ.setdefault('PYGAME_HIDE_SUPPORT_PROMPT', '1')
import pygame
from PIL import Image

W, H = 960, 720
DURATION = 12.0
TAU = math.tau
INK = (24, 23, 48)
BONE = (251, 237, 204)
BONE_SHADE = (179, 166, 171)
CLOTH = (243, 245, 255)


def clamp(x: float) -> float:
    return max(0.0, min(1.0, x))


def ease(x: float) -> float:
    x = clamp(x)
    return x*x*x*(x*(x*6-15)+10)


def ramp(t: float, a: float, b: float) -> float:
    return ease((t-a)/(b-a))


def mix(a, b, u):
    return a+(b-a)*u


def wave(t, k=1, phase=0):
    return math.sin(TAU*k*t/DURATION+phase)


def bez(a, b, c, u):
    return tuple((1-u)**2*a[i]+2*u*(1-u)*b[i]+u*u*c[i] for i in (0, 1))


def chain(p, angle, length):
    return p[0]+math.sin(angle)*length, p[1]+math.cos(angle)*length


class Canvas:
    """Small, resolution-independent pygame drawing interface."""
    def __init__(self, surface, scale=1):
        self.s, self.k = surface, scale

    def point(self, p):
        return round(p[0]*self.k), round(p[1]*self.k)

    def poly(self, color, pts):
        pygame.draw.polygon(self.s, color, [self.point(p) for p in pts])

    def oval(self, color, center, rx, ry):
        if rx <= 0 or ry <= 0:
            return
        rect = pygame.Rect(round((center[0]-rx)*self.k), round((center[1]-ry)*self.k),
                           max(1, round(2*rx*self.k)), max(1, round(2*ry*self.k)))
        pygame.draw.ellipse(self.s, color, rect)

    def line(self, color, pts, width=2):
        if len(pts) < 2:
            return
        pygame.draw.lines(self.s, color, False, [self.point(p) for p in pts], max(1, round(width*self.k)))
        for p in pts:
            self.oval(color, p, width/2, width/2)

    def text(self, text, pos, size, color, center=True):
        font = pygame.font.Font(None, round(size*self.k))
        img = font.render(text, True, color)
        rect = img.get_rect(center=self.point(pos)) if center else img.get_rect(topleft=self.point(pos))
        self.s.blit(img, rect)


def bone(c, a, b, width=12):
    """Outlined double-knuckle bone with a warm highlight."""
    angle = math.atan2(b[1]-a[1], b[0]-a[0])
    nx, ny = -math.sin(angle), math.cos(angle)
    for col, pad in ((INK, 3), (BONE_SHADE, 0)):
        c.line(col, [a, b], width*.63+pad*2)
        for p in (a,b):
            for side in (-1,1):
                c.oval(col, (p[0]+nx*width*.3*side, p[1]+ny*width*.3*side), width*.38+pad, width*.38+pad)
    c.line(BONE, [(a[0]-2,a[1]-2),(b[0]-2,b[1]-2)], width*.43)
    for p in (a,b):
        c.oval(BONE, (p[0]-2,p[1]-2), width*.4,width*.38)


def pumpkin(c, x, y, size, angle=0, dim=1):
    """A vector jack-o'-lantern; rotation affects the entire carved face."""
    co, si = math.cos(angle), math.sin(angle)
    def tf(p):
        return x+size*(p[0]*co-p[1]*si), y+size*(p[0]*si+p[1]*co)
    def col(rgb):
        return tuple(round(v*dim) for v in rgb)
    def ellipse(rgb, px, py, rx, ry):
        c.poly(col(rgb), [tf((px+rx*math.cos(i*TAU/40),py+ry*math.sin(i*TAU/40))) for i in range(40)])
    c.poly(col((93,127,102)), [tf(p) for p in [(-.08,-.29),(-.07,-.58),(.05,-.63),(.1,-.55),(.06,-.29)]])
    ellipse((75,34,48),0,.02,.55,.43)
    ellipse((205,78,43),0,0,.51,.39)
    for px in (-.27,.27):
        ellipse((240,109,48),px,0,.22,.36)
    ellipse((255,151,64),0,0,.25,.38)
    for points in [[(-.35,-.04),(-.1,-.07),(-.24,-.24)],[(.1,-.07),(.35,-.04),(.24,-.24)],
                   [(-.055,.075),(.055,.075),(0,-.035)],
                   [(-.34,.12),(-.17,.18),(-.12,.12),(-.06,.2),(.14,.19),(.19,.13),(.34,.11),(.23,.29),(.08,.31),(.04,.25),(-.08,.31),(-.24,.26)]]:
        c.poly(col((77,34,41)),[tf(p) for p in points])
        c.poly(col((255,226,125)),[tf((px*.87,py*.87+.012)) for px,py in points])


POSE_KEYS = ('la','lf','ra','rf','ll','lk','rl','rk','sway','tilt','bounce')


def dance(t):
    """Four moves, blended over half a beat to avoid rig discontinuities."""
    b = (t-3.0)*2
    def pose(i):
        s,f = math.sin(b*math.pi),math.sin(b*TAU)
        if i%4 == 0:  # rubber-bone shuffle
            v = (-1.4-.65*f,-.6-.7*s,1.4-.65*f,.6-.7*s,-.16-.4*max(s,0),.9*max(s,0),.16+.4*max(-s,0),-.9*max(-s,0),24*s,.14*s,10*abs(f))
        elif i%4 == 1:  # disco point
            v = (-2.4-.35*s,-.35,1.1+.6*s,-1.1,-.4,.35,.4,-.35,24*s,-.14*s,12*abs(s))
        elif i%4 == 2:  # chicken elbows
            v = (-1.2-.3*f,2.5,1.2+.3*f,-2.5,-.15-.5*max(s,0),1.1*max(s,0),.15+.5*max(-s,0),-1.1*max(-s,0),15*s,.1*f,8*abs(f))
        else:  # jazz hands
            v = (-2.45-.25*f,-.3,2.45-.25*f,.3,-.25,.1,.25,-.1,18*s,.13*s,10*abs(f))
        return dict(zip(POSE_KEYS,v))
    i = math.floor(b/3)
    u = ramp(b-i*3,2.5,3)
    p,q = pose(i),pose(i+1)
    return {key:mix(p[key],q[key],u) for key in POSE_KEYS}


def skeleton(c,t,x,y,activity):
    rest = dict(zip(POSE_KEYS,(-.18,-.1,.18,.1,-.1,0,.1,0,0,0,0)))
    p = {k:mix(rest[k],v,activity) for k,v in dance(t).items()}
    y -= p['bounce']
    sway = p['sway']
    hip=(x+sway,y+201)
    # Legs are drawn behind the torso.
    for side,a,knee_a in [(-1,p['ll'],p['lk']),(1,p['rl'],p['rk'])]:
        h=(hip[0]+side*20,hip[1]+7)
        knee=chain(h,a,58); ankle=chain(knee,a+knee_a,57)
        bone(c,h,knee,13); bone(c,knee,ankle,11)
        bone(c,ankle,(ankle[0]+side*26,ankle[1]+6),11)
        for j in range(3):
            c.oval(BONE,(ankle[0]+side*(16+j*5),ankle[1]+9),3,4)
    neck=(x,y+62)
    spine=lambda u:bez(neck,(x-sway*.25,y+130),hip,u)
    for i in range(5):
        sp=spine(.12+i*.105); rw=47-i*4
        for side in (-1,1):
            pts=[(sp[0]+side*rw*math.sin(a),sp[1]+23*(1-math.cos(a))*.5) for a in [j*2.6/18 for j in range(19)]]
            c.line(INK,pts,11);c.line(BONE_SHADE,pts,7);c.line(BONE,[(px,py-1.5) for px,py in pts],4)
    for i in range(12):
        q=spine(i/11);c.oval(INK,q,10,7);c.oval(BONE,q,7,4)
    for side in (-1,1):
        q=(hip[0]+side*17,hip[1]);c.oval(INK,q,22,17);c.oval(BONE,q,18,13)
        c.oval(INK,(q[0],q[1]+6),8,6)
    bone(c,(hip[0]-9,hip[1]+12),(hip[0]+9,hip[1]+12),10)
    for side,a,f in [(-1,p['la'],p['lf']),(1,p['ra'],p['rf'])]:
        sh=(x+side*46,y+76)
        el=chain(sh,a,62); hand=chain(el,a+f,56)
        bone(c,neck,sh,9);bone(c,sh,el,12);bone(c,el,hand,10)
        c.oval(INK,hand,11,11);c.oval(BONE,hand,8,8)
        for off in (-.6,-.2,.2,.6):
            end=chain(hand,a+f+off,20)
            c.line(INK,[hand,end],7);c.line(BONE,[hand,end],3)
    # Skull and loose jaw share a local rotation transform.
    tilt=p['tilt'];co,si=math.cos(tilt),math.sin(tilt)
    def tf(px,py):return x+px*co-py*si,y+px*si+py*co
    def oval(col,px,py,rx,ry):
        c.poly(col,[tf(px+rx*math.cos(i*TAU/50),py+ry*math.sin(i*TAU/50)) for i in range(50)])
    jaw=activity*(6+6*math.sin((t-3)*TAU*2))
    oval(INK,0,-5,47,49);oval(BONE_SHADE,0,-5,43,45);oval(BONE,-4,-9,39,40)
    c.poly(INK,[tf(-31,11),tf(31,11),tf(26,39),tf(-26,39)])
    c.poly(BONE,[tf(-28,9),tf(28,9),tf(24,34),tf(-24,34)])
    oval(INK,0,40+jaw,27,13);oval(BONE,0,39+jaw,23,10)
    for side in (-1,1):
        oval(INK,side*19,0,14,17)
        look=t*TAU*1.5
        oval((248,250,255),side*19+5*math.cos(look),7*math.sin(look),4.4,5.4)
        oval((255,255,255),side*19+5*math.cos(look)-1,7*math.sin(look)-1,1.2,1.4)
    c.poly(INK,[tf(-6,23),tf(6,23),tf(0,13)])
    for tx in (-16,-8,0,8,16):
        c.line(INK,[tf(tx,27),tf(tx,34)],2)
        c.line(INK,[tf(tx,35+jaw),tf(tx,41+jaw)],2)
    oval((255,250,231),-19,-30,11,5)


def sheet(c,t,pos,scale,rotation,fly,perched,squash=0):
    """Layered flowing fabric with a curved silhouette and inset fold ribbons."""
    co,si=math.cos(rotation),math.sin(rotation)
    sx=scale*(1+0.1*squash-.12*fly);sy=scale*(1-squash+.16*fly)
    def tf(x,y):
        x*=sx;y*=sy
        return pos[0]+x*co-y*si,pos[1]+x*si+y*co
    def poly(col,pts):c.poly(col,[tf(*p) for p in pts])
    def oval(col,x,y,rx,ry):
        poly(col,[(x+rx*math.cos(i*TAU/44),y+ry*math.sin(i*TAU/44)) for i in range(44)])
    phase=TAU*t/DURATION
    hem=330
    def width(y):return 73+.20*y+5*math.sin(y*.025-6*phase)*min(y/80,1)
    # Cloth arms cheer while the sheet watches the dance.
    for side in (-1,1):
        a=mix(.9+.3*wave(t,4,side),2.25+.3*wave(t,12,side),perched)
        a=mix(a,2.65,fly)
        root=(side*78,94)
        tip=(root[0]+side*math.sin(a)*87,root[1]+math.cos(a)*87)
        arm=[(root[0]-side*17,root[1]-24),(tip[0],tip[1]-18),(tip[0]+side*15,tip[1]),(tip[0],tip[1]+17),(root[0]+side*24,root[1]+37)]
        poly((159,163,201),arm)
        poly((222,228,247),[(px,py-4) for px,py in arm])
        oval(CLOTH,tip[0],tip[1]-3,16,16)
    pts=[(73*math.cos(math.pi+i*math.pi/48),73*math.sin(math.pi+i*math.pi/48)) for i in range(49)]
    pts += [(width(y),y) for y in range(12,hem+1,6)]
    def bottom(x):return hem+10*math.sin(x*.077+phase*8)+5*math.sin(x*.035-phase*6)
    pts += [(x,bottom(x)) for x in [width(hem)*(1-2*i/80) for i in range(81)]]
    pts += [(-width(y),y) for y in range(hem,0,-6)]
    poly((156,165,205),pts)
    # Slight inset highlight preserves a cool rim around the cloth.
    poly(CLOTH,[(px*.97,py-2) for px,py in pts])
    for side in (-1,1):
        ribbon=[]
        for y in range(70,hem-10,6):
            x=side*(40+y*.16)+7*math.sin(y*.022-phase*6+side)
            ribbon.append((x,y))
        other=[(px+side*(13+16*(py/hem)**2),py+3) for px,py in reversed(ribbon)]
        poly((215,221,241),ribbon+other)
        c.line((201,210,235),[tf(*p) for p in ribbon],1.4*scale)
    poly((230,235,250),[(-13,100),(-19,224),(-3,315),(12,318),(3,207)])
    oval((255,255,255),-26,-43,24,12)
    blink_phase=t%4
    blink=1-.93*math.sin(math.pi*blink_phase/.18) if blink_phase<.18 else 1
    look=mix(.8+wave(t,2)*.5,.1,perched)+TAU*ramp(t%3,2,2.8)
    for side in (-1,1):
        oval((175,184,215),side*27,-4,17,25*blink)
        oval(INK,side*27,-7,15,22*blink)
        if blink>.4:
            oval((255,255,255),side*27+6*math.cos(look),-7+9*math.sin(look)*blink,5,6)
    oval(INK,0,40,10+4*fly,11+12*fly+3*perched)
    oval((231,189,208),-46,27,10,4)
    oval((231,189,208),46,27,10,4)


class Scene:
    """A pure-time animation: render(t) == render(t + 12), including particles."""
    def __init__(self, supersample=2, seed=7):
        if not isinstance(supersample,int) or not 1<=supersample<=4:
            raise ValueError('supersample must be an integer from 1 to 4')
        pygame.font.init()
        self.scale=supersample
        self.surface=pygame.Surface((W*supersample,H*supersample))
        self.c=Canvas(self.surface,supersample)
        rng=random.Random(seed)
        self.stars=[(rng.uniform(36,924),rng.uniform(100,520),rng.uniform(.8,2),rng.uniform(0,TAU)) for _ in range(80)]
        self.particles=[(rng.uniform(30,930),rng.random(),rng.uniform(20,43),rng.choice((1,2,3)),rng.uniform(0,TAU)) for _ in range(18)]
        self.background=self._background()

    def _background(self):
        c=self.c
        for y in range(H):
            u=y/H
            c.line(tuple(round(mix(a,b,u)) for a,b in zip((13,16,39),(43,31,67))),[(0,y),(W,y)],2)
        # Radial atmospheric wash drawn once, not on every frame.
        glow=pygame.Surface(self.surface.get_size(),pygame.SRCALPHA)
        g=Canvas(glow,self.scale)
        for r in range(400,0,-4):
            g.oval((92,81,139,round(16*(1-r/400))), (480,370),r,r*.85)
        self.surface.blit(glow,(0,0))
        c.oval((45,48,81),(793,174),71,71)
        c.oval((71,73,104),(793,174),60,60)
        c.oval((242,221,174),(793,174),49,49)
        c.oval((29,28,57),(812,156),44,45)
        # Distant rolling hills and graphic evergreens.
        for base,col,amp in [(533,(29,30,57),24),(564,(35,32,61),17)]:
            pts=[(0,H)]+[(x,base+amp*math.sin(x*.008+.7)) for x in range(0,W+1,12)]+[(W,H)]
            c.poly(col,pts)
        for x,y,h in [(55,536,126),(112,555,85),(885,554,114),(930,550,163)]:
            c.line((22,25,48),[(x,y),(x,y-h)],5)
            for j in range(3):
                cy=y-h+j*h*.21
                c.poly((22,25,48),[(x,cy),(x-20-j*5,cy+55),(x+20+j*5,cy+55)])
        c.oval((24,24,48),(480,607),347,59)
        c.oval((62,50,86),(480,599),335,48)
        c.oval((43,37,69),(480,593),335,43)
        c.line((97,77,117),[(182,611),(244,628),(716,628),(778,611)],1.3)
        c.text('B O O - G I E   N I G H T S',(480,54),39,(249,230,197))
        c.text('A LITTLE SOUL.  A LOT OF MOVES.',(480,87),17,(162,160,191))
        c.text('THE AFTERLIFE DANCE CLUB',(480,680),18,(151,143,175))
        for x in (283,677):
            c.poly((190,137,104),[(x,676),(x+4,680),(x,684),(x-4,680)])
        for x,y,sz,rot in [(112,617,79,-.12),(170,637,51,.12),(842,622,86,.12),(785,642,48,-.13)]:
            pumpkin(c,x,y,sz,rot)
        return self.surface.copy()

    def draw(self,t):
        t=t%DURATION  # Normalize *all* animation, including eyes and particles.
        c=self.c
        self.surface.blit(self.background,(0,0))
        for x,y,r,ph in self.stars:
            a=.65+.35*wave(t,2,ph)
            col=tuple(round(v*a) for v in (177,184,220))
            c.oval(col,(x,y),r,r)
        active=ramp(t,2.8,3.8)*(1-ramp(t,9.4,10.6))
        # Small lanterns rain behind the hero and fade in/out with the dance.
        if active>.001:
            for x,offset,size,falls,ph in self.particles:
                y=((offset+t*falls/DURATION)%1)*600-60
                # Avoid the title and stage; smooth edge fade prevents wrap pops.
                vis=active*ramp(y,102,150)*(1-ramp(y,510,555))
                if vis>.015:
                    layer=pygame.Surface((round(size*1.8*self.scale),round(size*1.8*self.scale)),pygame.SRCALPHA)
                    pc=Canvas(layer,self.scale)
                    pumpkin(pc,size*.9,size*.9,size,t*TAU/DURATION+ph,.8)
                    layer.set_alpha(round(190*vis))
                    self.surface.blit(layer,c.point((x+10*wave(t,3,ph)-size*.9,y-size*.9)))
        home=(480+15*wave(t),252+6*wave(t,2))
        perch=(239+8*wave(t,2),360+10*wave(t,3))
        fly=0;rot=0
        if t<2.4 or t>=10.6:
            pos=home;k=0
        elif t<3.6:
            u=ramp(t,2.4,3.6);k=u
            pos=bez(home,(310,67),perch,u);fly=math.sin(math.pi*u);rot=-.45*fly
        elif t<9.3:
            pos=perch;k=1
        else:
            u=ramp(t,9.3,10.6);k=1-u
            pos=bez(perch,(525,92),home,u);fly=math.sin(math.pi*u);rot=.55*fly
        skx=mix(home[0],563+12*wave(t,4),active)
        sky=mix(home[1],263,active)
        # Grounding shadows and dance-floor rings.
        c.oval((29,27,50),(skx,599),81,13)
        c.oval((34,30,56),(pos[0],603),mix(120,65,k),mix(15,8,k))
        if active>.05:
            for side in (-1,1):
                for j in range(3):
                    px=skx+side*(119+j*17);py=367+12*wave(t,12,j)
                    color=tuple(round(mix(a,b,active)) for a,b in zip((43,37,69),(244,186,111)))
                    c.line(color,[(px,py-j*10),(px+side*7,py-j*10-10)],3)
        # Completely hide the rig while covered, preventing stray bones at rest.
        if k>.005:
            skeleton(c,t,skx,sky,active)
        anticipation=.08*math.sin(math.pi*clamp((t-2.0)/.4))
        landing=.11*math.sin(math.pi*clamp((t-10.6)/.6))
        sheet(c,t,pos,mix(1,.59,k),rot,fly,k,anticipation+landing)
        return self.surface

    def image(self,t,width=640):
        if width<1:raise ValueError('width must be positive')
        surface=self.draw(t)
        im=Image.frombytes('RGB',surface.get_size(),pygame.image.tobytes(surface,'RGB'))
        return im.resize((width,round(width*H/W)),Image.Resampling.LANCZOS)
