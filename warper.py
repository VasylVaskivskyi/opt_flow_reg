from typing import Tuple, List

import numpy as np
import cv2 as cv

from slicer import split_image_into_tiles_of_size
from stitcher import stitch_image
Image = np.ndarray


class Warper:
    def __init__(self):
        self.image = None
        self.image_tiles = []
        self.slicer_info = {}
        self.flow_tiles = []
        self.block_w = 1000
        self.block_h = 1000
        self.overlap = 50


    def warp(self):
        if self.image is not None:
            self.image_tiles, self.slicer_info = split_image_into_tiles_of_size(self.image, self.block_w, self.block_h, self.overlap)
            self.image = None  # cleanup

        warped_image_tiles = self.warp_image_tiles(self.image_tiles, self.flow_tiles)

        self.flow_tiles = []  # cleanup
        self.image_tiles = []  # cleanup

        stitched_warped_image = stitch_image(warped_image_tiles, self.slicer_info)

        self.slicer_info = {}  # cleanup
        del warped_image_tiles  # cleanup

        return stitched_warped_image

    #TODO for some reasons dask hangs trying to run wapring in parallel so I need to work on it later
    def make_flow_for_remap(self, flow):
        h, w = flow.shape[:2]
        new_flow = np.negative(flow)
        new_flow[:, :, 0] += np.arange(w)
        new_flow[:, :, 1] += np.arange(h)[:, np.newaxis]
        return new_flow


    def warp_with_flow(self, img: Image, flow: np.ndarray) -> Image:
        """ Warps input image according to optical flow """
        new_flow = self.make_flow_for_remap(flow)
        res = cv.remap(img, new_flow, None, cv.INTER_LINEAR)
        return res


    def warp_image_tiles(self, image_tiles: List[Image], flow_tiles: List[np.ndarray]) -> List[Image]:
        warped_tiles = []
        for t in range(0, len(image_tiles)):
            warped_tiles.append(self.warp_with_flow(image_tiles[t], flow_tiles[t]))

        return warped_tiles

