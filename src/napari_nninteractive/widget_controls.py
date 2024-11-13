from typing import Any, Optional

import numpy as np
from napari._qt.layer_controls.qt_layer_controls_container import layer_to_controls
from napari.viewer import Viewer
from qtpy.QtWidgets import QWidget

from napari_nninteractive.controls.bbox_controls import CustomQtBBoxControls
from napari_nninteractive.controls.point_controls import CustomQtPointsControls
from napari_nninteractive.controls.scribble_controls import CustomQtScribbleControls
from napari_nninteractive.layers.bbox_layer import BBoxLayer
from napari_nninteractive.layers.point_layer import SinglePointLayer
from napari_nninteractive.layers.scribble_layer import ScibbleLayer
from napari_nninteractive.widget_gui import BaseGUI

layer_to_controls[SinglePointLayer] = CustomQtPointsControls
layer_to_controls[BBoxLayer] = CustomQtBBoxControls
layer_to_controls[ScibbleLayer] = CustomQtScribbleControls


class LayerControls(BaseGUI):
    """
    A class for managing and interacting with different layers in the viewer,
    specifically designed for point, bounding box, and scribble layers.

    Args:
        viewer (Viewer): The Napari viewer instance to which layers will be added.
        parent (Optional[QWidget], optional): The parent widget. Defaults to None.
    """

    def __init__(self, viewer: Viewer, parent: Optional[QWidget] = None):
        super().__init__(viewer, parent)
        self.point_layer_name = "nnInteractive - Point Layer"
        self.bbox_layer_name = "nnInteractive - BBox Layer"
        self.scribble_layer_name = "nnInteractive - Scribble Layer"
        self.label_layer_name = "nnInteractive - Label Layer"
        self.layer_dict = {
            0: self.point_layer_name,
            1: self.bbox_layer_name,
            2: self.scribble_layer_name,
        }
        self._viewer.layers.selection.events.active.connect(self.on_layer_selected)

    def add_point_layer(self):
        """Adds a single point layer to the viewer."""
        point_layer = SinglePointLayer(
            name=self.point_layer_name,
            ndim=self.session_cfg["ndim"],
            affine=self.session_cfg["affine"],
            opacity=0.7,
            size=5,
            prompt_index=self.prompt_button.index,
        )
        # point_layer.events.data.connect(self._auto_run)
        point_layer.events.finished.connect(self._auto_run)
        self._viewer.add_layer(point_layer)

        # self._viewer.layers[self.point_layer_name].events.data_current.connect(self._auto_run)
        # self._viewer.layers[self.point_layer_name].events.data.connect(self._auto_run)

    def add_bbox_layer(self):
        """Adds a bounding box layer to the viewer."""
        bbox_layer = BBoxLayer(
            name=self.bbox_layer_name,
            ndim=self.session_cfg["ndim"],
            affine=self.session_cfg["affine"],
            prompt_index=self.prompt_button.index,
            opacity=0.5,
        )
        bbox_layer.events.data.connect(self._auto_run)
        # bbox_layer.events.finished.connect(self._auto_run)
        self._viewer.add_layer(bbox_layer)

        # self._viewer.layers[self.bbox_layer_name].events.data.connect(self._auto_run)

    def add_scribble_layer(self):
        """Adds a scribble layer to the viewer with an initial blank data array."""
        _data = np.zeros(self.session_cfg["shape"], dtype=np.uint8)
        scribble_layer = ScibbleLayer(
            data=_data,
            name=self.scribble_layer_name,
            affine=self.session_cfg["affine"],
            prompt_index=self.prompt_button.index,
        )
        scribble_layer.events.finished.connect(self._auto_run)
        self._viewer.add_layer(scribble_layer)

    def clear_layers(self):
        """Removes all layers in the viewer that are managed by this class."""
        layer_names = list(self.layer_dict.values())  # + [self.label_layer_name]
        # for layer_name in self.layer_dict.values():
        for layer_name in layer_names:
            if layer_name in self._viewer.layers:
                self._viewer.layers.remove(layer_name)

    def on_interaction_selected(self):
        """
        Activates or creates a layer based on the selected interaction type.

        If a layer of the specified `interaction_type` already exists, it is activated;
        otherwise, a new layer is created.
        """
        self.interaction_type = self.interaction_button.index
        layer_name = self.layer_dict.get(self.interaction_type)

        if layer_name is not None and layer_name in self._viewer.layers:  # Activate the Layer
            self._viewer.layers.selection.clear()
            self._viewer.layers.selection.add(self._viewer.layers[layer_name])
        elif self.interaction_type == 0:  # Add Point Layer
            self.add_point_layer()
        elif self.interaction_type == 1:  # Add BBox Layer
            self.add_bbox_layer()
        elif self.interaction_type == 2:  # Add Scrible Layer
            self.add_scribble_layer()

    def on_layer_selected(self, *args, **kwargs):
        """
        Updates the interaction button and sets the `interaction_type` based on
        the currently selected layer in the viewer.

        Args:
            *args: Additional arguments for the method.
            **kwargs: Additional keyword arguments for the method.
        """
        _layer = self._viewer.layers.selection.active
        if _layer is not None:
            key = next((k for k, v in self.layer_dict.items() if v == _layer.name), None)
            self.interaction_type = key
            self.interaction_button._uncheck()
            self.interaction_button._check(self.interaction_type)

    def on_run(self, *args, **kwargs):
        """
        Executes the run method of the selected layer and triggers inference if data is obtained.

        Args:
            *args: Additional arguments for the run method.
            **kwargs: Additional keyword arguments for the run method.
        """
        _index = self.interaction_button.index
        _layer_name = self.layer_dict.get(_index)
        if _layer_name is not None and _layer_name in self._viewer.layers:
            _ = self._viewer.layers[_layer_name].run()
            _data = self._viewer.layers[_layer_name].get_last()  # .data[-1]
            if _data is not None:
                self.inference(_data, _index)

    def on_prompt_selected(self):
        for layer_name in self.layer_dict.values():
            if layer_name in self._viewer.layers:
                self._viewer.layers[layer_name].set_prompt(self.prompt_button.index)
                self._viewer.layers[layer_name].refresh()

    def inference(self, data: Any, index: int):
        """
        Performs inference on the provided data.

        Args:
            _data: The data obtained from the layer's run method.
            _index (int): The index of the layer type, corresponding to the layer_dict key.
        """
        print(
            f"Inference for interaction {index} and prompt {self.prompt_button.index == 0} and valid data {data is not None} "
        )
