"""Contract checks for deterministic renders, temporal seams, and CLI validation."""
import os
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
import unittest
from PIL import ImageChops,ImageStat
from ghost_party.scene import Scene,DURATION
from ghost_party.cli import main

class AnimationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.scene=Scene(1)

    def test_periodicity_at_all_story_beats(self):
        for t in (0,.08,2.4,3,3.6,5,7,9.3,10,10.6,11.9):
            with self.subTest(t=t):
                a=self.scene.image(t,240);b=self.scene.image(t+DURATION,240)
                self.assertIsNone(ImageChops.difference(a,b).getbbox())

    def test_repeatability(self):
        a=self.scene.image(5,240);self.scene.image(9,240)
        self.assertEqual(a.tobytes(),self.scene.image(5,240).tobytes())

    def test_seam_has_small_visual_change(self):
        a=self.scene.image(DURATION-1/25,240);b=self.scene.image(0,240)
        delta=sum(ImageStat.Stat(ImageChops.difference(a,b)).mean)/3
        self.assertLess(delta,2.5)

    def test_boundary_continuity(self):
        for t in (2.4,3.6,9.3,10.6):
            a=self.scene.image(t-.001,240);b=self.scene.image(t+.001,240)
            delta=sum(ImageStat.Stat(ImageChops.difference(a,b)).mean)/3
            self.assertLess(delta,.8)

    def test_invalid_dimensions(self):
        with self.assertRaises(SystemExit) as exc:main(['--width','0'])
        self.assertEqual(exc.exception.code,2)

if __name__=='__main__':unittest.main()
