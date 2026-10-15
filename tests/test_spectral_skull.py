import unittest
from pathlib import Path
from PIL import Image
from spectral_skull import Scene,DURATION

ASSET=Path(__file__).parents[1]/'spectral_skull/assets_source.jpg'
class SpectralSkullTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not ASSET.exists():raise unittest.SkipTest('Optional user-supplied source art missing')
        cls.scene=Scene(ASSET,192,seed=42)
    def test_loop_is_exact(self):
        self.assertEqual(self.scene.image(0).tobytes(),self.scene.image(DURATION).tobytes())
    def test_last_exported_frame_is_exactly_first(self):
        self.assertEqual(self.scene.frame(149,25).tobytes(),self.scene.frame(0,25).tobytes())
    def test_alpha(self):
        frame=self.scene.image(0)
        self.assertEqual(frame.mode,'RGBA')
        self.assertEqual(frame.getpixel((0,0))[3],0)
        self.assertGreater(frame.getpixel((100,100))[3],10)
    def test_deterministic(self):
        self.assertEqual(self.scene.image(3.4).tobytes(),self.scene.image(3.4).tobytes())
    def test_frames_vary(self):
        self.assertNotEqual(self.scene.image(.4).tobytes(),self.scene.image(3.4).tobytes())
if __name__=='__main__':unittest.main()
