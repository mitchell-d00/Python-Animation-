"""Recover alpha from the reference illustration's connected white background."""
from __future__ import annotations
import cv2
import numpy as np
from PIL import Image

def cutout(source: str | Image.Image) -> Image.Image:
    image = Image.open(source).convert('RGB') if isinstance(source, str) else source.convert('RGB')
    rgb = np.asarray(image).copy()
    lo = rgb.min(axis=2)
    hi = rgb.max(axis=2)
    candidate = ((lo > 236) & ((hi-lo) < 19)).astype('uint8')
    count, labels = cv2.connectedComponents(candidate, connectivity=4)
    border = np.concatenate((labels[0,:],labels[-1,:],labels[:,0],labels[:,-1]))
    positive = border[border != 0]
    if positive.size == 0:
        return image.convert('RGBA')
    bg_id = np.bincount(positive, minlength=count).argmax()
    mask = (labels != bg_id).astype('uint8') * 255
    alpha = cv2.GaussianBlur(mask, (3,3), 0.65)
    rgba = np.dstack((rgb,alpha))
    rgba[alpha==0,:3] = 0
    return Image.fromarray(rgba,'RGBA')
