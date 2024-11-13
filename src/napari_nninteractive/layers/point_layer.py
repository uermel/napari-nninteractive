import numpy as np
from napari.layers import Points

from napari_nninteractive.layers.abstract_layer import BaseLayerClass


class SinglePointLayer(BaseLayerClass, Points):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.point_colors = []

    def remove_color(self):
        self.point_colors = self.point_colors[:-1]
        self.face_color = np.array(self.point_colors)
        self.border_color = np.array(self.point_colors)

    def replace_color(self, _color):
        self.point_colors[-1] = _color
        self.face_color = np.array(self.point_colors)
        self.border_color = np.array(self.point_colors)

    def remove_last(self):
        self.data = self.data[:-1]
        self.remove_color()

    def _add(self, data, *arg, **kwargs):
        Points.add(self, data, *arg, **kwargs)
        _color = self.colors[self.prompt_index]
        self.point_colors.append(_color)
        self.face_color = np.array(self.point_colors)
        self.border_color = np.array(self.point_colors)

    def remove_selected(self) -> None:
        """Removes selected points if any."""
        index = list(self.selected_data)
        if not self._is_free and len(index) == 1 and index[0] == (len(self.data) - 1):
            super().remove_selected()
            self._is_free = True
            self.remove_color()

    def _move(
        self,
        selection_indices,
        position,
    ) -> None:
        # Only the last edited one should be able to be moved
        if (
            not self._is_free
            and len(selection_indices) == 1
            and list(selection_indices)[0] == (len(self.data) - 1)
        ):
            super()._move(selection_indices, position)

    def get_last(self):
        return self.data[-1]
