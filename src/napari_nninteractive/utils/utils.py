import numpy as np
from kornia.geometry import nms2d
from napari.layers import Layer
from napari.utils.colormaps import label_colormap
from napari.utils.transforms import Affine


class ColorMapper:
    """
    A color mapping class that generates colors for labeled items using a colormap.
    Args:
        num_colors (int, optional): The total number of colors to generate. Defaults to 49.
        seed (float, optional): A seed for random color generation. Defaults to 0.5.
        background_value (int, optional): The background value for the colormap. Defaults to 0.
        skip_bg (bool, optional): If True, skips the background color in mappings. Defaults to True.
    """

    def __init__(
        self, num_colors=49, seed: float = 0.5, background_value: int = 0, skip_bg: bool = True
    ):
        self.num_colors = num_colors
        self.skip_bg = skip_bg
        self.cmap = label_colormap(
            num_colors=num_colors, seed=seed, background_value=background_value
        )

    def __getitem__(self, item: int):
        """
        Gets the color mapping for a specified item. Background values and `None` return transparent colors.

        Args:
            item (int): The index of the item to map.
        """
        item = item % self.num_colors
        item = item + 1 if self.skip_bg else item
        _color = self.cmap.map([item])[0]
        return {None: (0, 0, 0, 0), 0: (0, 0, 0, 0), 1: _color}


def determine_layer_index(name, layer_names, splitter) -> str:
    """
    Determines the index assigned to the next layer.
    """
    layer_names = [l_name for l_name in layer_names if name in l_name and name != l_name]
    if layer_names != []:
        return max([int(layer_name.split(splitter)[-1]) for layer_name in layer_names]) + 1
    else:
        return 0
