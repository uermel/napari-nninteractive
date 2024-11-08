import numpy as np
from napari.layers import Points

colors = {
    "red": [0.827, 0.027, 0.0, 1],  # [211, 7, 0]
    "darkred": [0.561, 0.02, 0.0, 1],  # [143, 5, 0]
    "green": [0.0, 0.694, 0.047, 1],  # [0, 177, 12]
    "darkgreen": [0.0, 0.427, 0.027, 1],  # [0, 109, 7]
}
colors = {
    0: [0.0, 0.694, 0.047, 1],  # [0, 177, 12]
    1: [0.827, 0.027, 0.0, 1],  # [211, 7, 0]
}
colors_hist = {
    0: [0.0, 0.427, 0.027, 1],  # [0, 109, 7]
    1: [0.561, 0.02, 0.0, 1],  # [143, 5, 0]
}


class SinglePointLayer(Points):
    def __init__(self, prompt_index=0, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.prompt_index = prompt_index
        self.data_current = None
        self.colors_f = []

    def run(self):
        if self.data_current is None:
            return None
        _data = self.data_current.copy()
        self.data_current = None
        self.colors_f[-1] = colors_hist[self.prompt_index]
        self._upd_color()
        return _data

    def set_prompt(self, index):
        self.prompt_index = index
        if self.data_current is not None:
            self.colors_f[-1] = colors[self.prompt_index]
            self._upd_color()

    def add(self, coord, *args, **kwargs):
        if self.data_current is None:
            self.data_current = coord.copy()
            self._add_data(coord)
        else:
            self.data_current = coord.copy()
            self._rem_data()
            self._add_data(coord)
        self._upd_color()

    def _add_data(self, data):
        self.colors_f.append(colors[self.prompt_index])
        super().add(data)

    def _rem_data(self):
        self.colors_f = self.colors_f[:-1]
        self.data = self.data[:-1]

    def _upd_color(self):
        self.face_color = np.array(self.colors_f)
        self.border_color = np.array(self.colors_f)

    def _move(
        self,
        selection_indices,
        position,
    ) -> None:
        # Only the last edited one should be able to be moved
        if (
            self.data_current is not None
            and len(selection_indices) == 1
            and list(selection_indices)[0] == (len(self.data) - 1)
        ):
            super()._move(selection_indices, position)

    def remove_selected(self) -> None:
        """Removes selected points if any."""
        index = list(self.selected_data)
        if self.data_current is not None and len(index) == 1 and index[0] == (len(self.data) - 1):
            super().remove_selected()
            self.data_current = None
            self.colors_f = self.colors_f[:-1]
            self._upd_color()

    #
    #
    #
    # def _add_color(self):
    #     self.colors_f.append(self.current_color)
    #     self.colors_b.append([1, 1, 1, 1])
    #     self.width_b.append(self.border_const)
    #
    # def _rem_color(self):
    #     self.colors_b = self.colors_b[:-1]
    #     self.colors_f = self.colors_f[:-1]
    #     self.width_b = self.width_b[:-1]
    #
    # def _upd_color(self):
    #     self.face_color = np.array(self.colors_f)
    #     self.border_color = np.array(self.colors_b)
    #     self.border_width = np.array(self.border_const)
    #
    # def set_signal(self, idx):
    #     if idx == 0:
    #         self.current_color = self.color_pos
    #         if not self._addable:
    #             self._rem_color()
    #             self._add_color()
    #             self._upd_color()
    #     elif idx == 1:
    #         self.current_color = self.color_neg
    #         if not self._addable:
    #             self._rem_color()
    #             self._add_color()
    #             self._upd_color()
    #     else:
    #         print("Error")
