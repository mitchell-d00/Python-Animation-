# Spectral Skull: Fracture / Escape / Vortex / Reformation

A **deterministic, frame-exact, transparent** 6-second animation of your **original supplied skull illustration**. This is a compositing and 2.5D effect engine, not a newly invented skull. It keeps the uploaded skull pixels and triangulates them into independently animated crystal shards. Four procedural screaming specters break loose, orbit a spectral vortex, and return as the skull rebuilds. Uses seeded Delaunay fragmentation, translucent smoke, glowing eyes, scream-wave rings and 170 particles.

> **Accuracy:** a single 2D reference cannot supply missing 3D rear/side geometry. The spin is a full 360° screen-plane rotation of the **exact reference artwork**, rather than claiming an invented 3D back face. The ghosts escaping are *stylized procedural sprites*, not exact isolated layers from the flattened image.

## Install and render

```bash
python -m pip install -e .
python -m spectral_skull --source /path/to/your/skull.jpg --output renders/spectral_skull.gif --size 768 --fps 25 --apng renders/spectral_skull.png
```

Or use `spectral-skull` after installation. Provide the original illustration as `--source`; the rendered example and original input are bundled in the downloadable package from the chat. The repository contains the generic renderer, not the artwork. The default render writes **150 distinct 768x768 RGBA PNG frames** to `renders/spectral_skull_frames/` plus a 150-frame transparent GIF and optional APNG. GIF supports only a 1-bit transparency index; the individual PNGs and APNG preserve soft alpha. `--size`, `--fps`, `--seed`, `--frames-dir` and `--no-gif` are configurable. Valid GIF FPS: 10, 20, 25, 50. Rendering is headless.

## Timeline (6 seconds, loops)

| Time | Action |
|---|---|
| 0.00–1.71s | Original transparent skull spins a full 360 degrees in-plane. |
| 1.71–2.7s | Crystal artwork fractures into precisely masked Delaunay shards; shock rings wake up. |
| 2.19–4.10s | Four screaming ghosts leave the skull amid halos and particles. |
| 3.48–4.68s | Shards spiral in a luminous vortex; ghosts turn and dissolve inward. |
| 4.68–6.00s | Original shards reassemble and the reference skull reforms. |

## Source files

- `spectral_skull/matte.py`: border-connected white removal (internal white reflections are protected).
- `spectral_skull/scene.py`: procedural ghosts, crystals, vortex, full deterministic choreography.
- `spectral_skull/export.py`: all PNG frames, shared-palette transparent GIF, lossless-alpha APNG.
- `spectral_skull/cli.py`: reproducible headless CLI.
- `tests/test_spectral_skull.py`: transparency, determinism, exact loop validation.

Artwork credit/rights belong to the original creator. For new skulls, replace `--source` with any white-background image. Mask quality depends on background separability. Python >=3.10, Pillow >=10, numpy >=1.24, opencv-python-headless >=4.7, scipy >=1.10.