import numpy as np
from napari.layers import Shapes
from napari.layers.base._base_constants import ActionType
from napari.layers.shapes._shape_list import ShapeList

from napari_nninteractive.layers.abstract_layer import BaseLayerClass


class CustomShapeList(ShapeList):
    """Custom list of shapes that disallows rotation, ensuring bounding boxes
    are always aligned with the grid.

    Attributes:
        ndisplay (int): The display dimensionality of the shapes.
    """

    def rotate(self, index, angle, center=None):
        """Override rotation to prevent bounding boxes from rotating."""


class BBoxLayer(BaseLayerClass, Shapes):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._data_view = CustomShapeList(ndisplay=self._slice_input.ndisplay)
        self._data_view.slice_key = np.array(self._data_slice.point)[
            self._slice_input.not_displayed
        ]

    def replace_color(self, _color):
        self._data_view.update_edge_color(len(self.data) - 1, _color)
        self._data_view.update_face_color(len(self.data) - 1, _color)

    def remove_last(self) -> None:
        """Remove any selected shapes."""
        index = [len(self.data) - 1]
        to_remove = sorted(index, reverse=True)
        self.events.data(
            value=self.data,
            action=ActionType.REMOVING,
            data_indices=tuple(
                index,
            ),
            vertex_indices=((),),
        )
        for ind in to_remove:
            self._data_view.remove(ind)

        self._feature_table.remove(index)
        self.text.remove(index)
        self._data_view._edge_color = np.delete(self._data_view._edge_color, index, axis=0)
        self._data_view._face_color = np.delete(self._data_view._face_color, index, axis=0)

    def run(self):
        super().run()
        # self.selected_data = set()
        self.selected_data.clear()
        self._finish_drawing()

    def _add(self, data, *args, **kwargs):
        Shapes.add(
            self,
            data,
            edge_color=self.colors[self.prompt_index],
            face_color=self.colors[self.prompt_index],
            *args,
            **kwargs,
        )
        # self.refresh(force=True)

    def remove_selected(self) -> None:
        """Removes selected points if any."""
        index = list(self.selected_data)
        if not self._is_free and len(index) == 1 and index[0] == (len(self.data) - 1):
            super().remove_selected()
            self._is_free = True

    def _rotate_box(self, angle, center=(0, 0)):
        """Disable rotation by overriding the rotation function."""

    @Shapes.selected_data.setter
    def selected_data(self, selected_data):
        index = list(selected_data)
        if len(index) == 1 and index[0] == (len(self.data) - 1) and not self._is_free:
            Shapes.selected_data.fset(self, selected_data)
        else:
            Shapes.selected_data.fset(self, set())

    def get_last(self):
        return self.data[-1]


# class BBoxLayer__(Shapes):
#     """Custom shapes layer specifically for bounding boxes, with restricted rotation.
#
#     Args:
#         **kwargs: Additional keyword arguments passed to the Shapes layer.
#     """
#
#     # def __init__(self, prompt_index=0, *args, **kwargs):
#     #     super().__init__(*args, **kwargs)
#     #     self.prompt_index = prompt_index
#     #     self.data_current = None
#     #     self.colors_f = []
#     #
#     #     self._data_view = CustomShapeList(ndisplay=self._slice_input.ndisplay)
#     #     self._data_view.slice_key = np.array(self._data_slice.point)[
#     #         self._slice_input.not_displayed
#     #     ]
#     #
#     #     # We only want one bbox at a time
#     #     self.data_current = None
#
#     # def run(self):
#     #     if self.data_current is None:
#     #         return None
#     #
#     #     _data = self.data_current.copy()
#     #     self.data_current = None
#     #     self.selected_data = set()
#     #     self._data_view.update_edge_color(len(self.data) - 1, colors_hist[self.prompt_index])
#     #     self._data_view.update_face_color(len(self.data) - 1, colors_hist[self.prompt_index])
#     #     self.selected_data.clear()
#     #     self._finish_drawing()
#     #     return _data
#     #
#     # def set_prompt(self, index):
#     #     self.prompt_index = index
#     #     if self.data_current is not None:
#     #         self.replace_color()
#     #
#     # def add(self, coord, *args, **kwargs):
#     #     if self.data_current is None:
#     #         self.data_current = coord.copy()
#     #         super().add(
#     #             coord,
#     #             edge_color=colors[self.prompt_index],
#     #             face_color=colors[self.prompt_index],
#     #             *args,
#     #             **kwargs,
#     #         )
#     #     else:
#     #         self.data_current = coord.copy()
#     #         self.remove_index(len(self.data) - 1)
#     #         super().add(
#     #             coord,
#     #             edge_color=colors[self.prompt_index],
#     #             face_color=colors[self.prompt_index],
#     #             *args,
#     #             **kwargs,
#     #         )
#     #         self.colors_f.append(colors[self.prompt_index])
#
#     def _rotate_box(self, angle, center=(0, 0)):
#         """Disable rotation by overriding the rotation function."""
#
#     def remove_selected(self):
#         super().remove_selected()
#         self.data_current = None
#
#     @property
#     def selected_data(self):
#         """set: set of currently selected shapes."""
#         return self._selected_data
#
#     @Shapes.selected_data.setter
#     def selected_data(self, selected_data):
#         index = list(selected_data)
#         if len(index) == 1 and index[0] == (len(self.data) - 1) and self.data_current is not None:
#             Shapes.selected_data.fset(self, selected_data)
#         else:
#             Shapes.selected_data.fset(self, set())
#
#     def remove_index(self, index) -> None:
#         """Remove any selected shapes."""
#         index = [index]
#         to_remove = sorted(index, reverse=True)
#         self.events.data(
#             value=self.data,
#             action=ActionType.REMOVING,
#             data_indices=tuple(
#                 index,
#             ),
#             vertex_indices=((),),
#         )
#         for ind in to_remove:
#             self._data_view.remove(ind)
#
#         self._feature_table.remove(index)
#         self.text.remove(index)
#         self._data_view._edge_color = np.delete(self._data_view._edge_color, index, axis=0)
#         self._data_view._face_color = np.delete(self._data_view._face_color, index, axis=0)
#
#     def replace_color(self):
#         self._data_view.update_edge_color(len(self.data) - 1, colors[self.prompt_index])
#         self._data_view.update_face_color(len(self.data) - 1, colors[self.prompt_index])
