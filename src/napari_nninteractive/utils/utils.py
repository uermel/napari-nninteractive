from napari.utils.colormaps import label_colormap


class ColorMapper:
    """
    A color mapping class that generates colors for labeled items using a colormap.
    Args:
        num_colors (int, optional): The total number of colors to generate. Defaults to 49.
        seed (float, optional): A seed for random color generation. Defaults to 0.5.
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


def determine_layer_index(names, prefix, postfix) -> str:
    """
    Determines the index assigned to the next layer.
    Handles layer names with format: "object X" or "object X (object_name)"
    """
    names = [name for name in names if name.startswith(prefix) and name.endswith(postfix)]
    
    indices = []
    for name in names:
        # Remove prefix and postfix
        middle_part = name.replace(prefix, "").replace(postfix, "")
        
        # Check if there's an object name in parentheses
        if " (" in middle_part and ")" in middle_part:
            # Extract just the number part before the parentheses
            number_part = middle_part.split(" (")[0].strip()
        else:
            number_part = middle_part.strip()
            
        try:
            indices.append(int(number_part))
        except ValueError:
            # If we can't convert to int, skip this name
            continue

    _index = max(indices) + 1 if indices else 0
    return _index
