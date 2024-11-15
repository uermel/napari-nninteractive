from typing import Any, Optional

import numpy as np
from napari._qt.layer_controls.qt_layer_controls_container import layer_to_controls
from napari.layers import Labels
from napari.layers.base._base_constants import ActionType
from napari.utils.action_manager import action_manager
from napari.viewer import Viewer
from qtpy.QtWidgets import QWidget

from napari_nninteractive.controls.bbox_controls import CustomQtBBoxControls
from napari_nninteractive.controls.point_controls import CustomQtPointsControls
from napari_nninteractive.controls.scribble_controls import CustomQtScribbleControls
from napari_nninteractive.layers.bbox_layer import BBoxLayer
from napari_nninteractive.layers.point_layer import SinglePointLayer
from napari_nninteractive.layers.scribble_layer import ScibbleLayer
from napari_nninteractive.utils.utils import ColorMapper, determine_layer_index
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
        self.layer_dict = {
            0: self.point_layer_name,
            1: self.bbox_layer_name,
            2: self.scribble_layer_name,
        }

        self.label_layer_name = "nnInteractive - Label Layer"
        self.colormap = ColorMapper(49, seed=0.5, background_value=0)
        self._scribble_brush_size = 5

        self._viewer.layers.selection.events.active.connect(self.on_layer_selected)

    # Layer Handling
    def _clear_layers(self) -> None:
        """Removes all layers in the viewer that are managed by this class."""
        layer_names = list(self.layer_dict.values())  # + [self.label_layer_name]
        # for layer_name in self.layer_dict.values():
        for layer_name in layer_names:
            if layer_name in self._viewer.layers:
                self._viewer.layers.remove(layer_name)

    def add_point_layer(self) -> None:
        """Adds a single point layer to the viewer."""
        point_layer = SinglePointLayer(
            name=self.point_layer_name,
            ndim=self.session_cfg["ndim"],
            affine=self.session_cfg["affine"],
            opacity=0.7,
            size=5,
            prompt_index=self.prompt_button.index,
        )
        point_layer.events.finished.connect(self.on_auto_run)
        self._viewer.add_layer(point_layer)

    def add_bbox_layer(self) -> None:
        """Adds a bounding box layer to the viewer."""
        bbox_layer = BBoxLayer(
            name=self.bbox_layer_name,
            ndim=self.session_cfg["ndim"],
            affine=self.session_cfg["affine"],
            prompt_index=self.prompt_button.index,
            opacity=0.5,
        )
        bbox_layer.events.data.connect(self.on_auto_run)
        self._viewer.add_layer(bbox_layer)

    def add_scribble_layer(self) -> None:
        """Adds a scribble layer to the viewer with an initial blank data array."""
        _data = np.zeros(self.session_cfg["shape"], dtype=np.uint8)
        scribble_layer = ScibbleLayer(
            data=_data,
            name=self.scribble_layer_name,
            affine=self.session_cfg["affine"],
            prompt_index=self.prompt_button.index,
        )

        scribble_layer.brush_size = self._scribble_brush_size

        scribble_layer.events.finished.connect(self.on_auto_run)
        self._viewer.add_layer(scribble_layer)

    # Event Handlers
    def on_init(self, *args, **kwargs) -> None:
        """
        Initializes the session by configuring the selected model and image and creating a label layer.

        Retrieves the selected model and image names from the GUI, extracts relevant data from the
        image layer, and creates a corresponding label layer in the viewer.
        """
        # Get all model and image from the GUI
        image_name = self.image_selection.currentText()
        model_name = self.model_selection.currentText()
        self.label_layer_name = f"nnInteractive - Label Layer - {image_name} - {model_name}"

        # Get everything we need from the image layer
        image_layer = self._viewer.layers[image_name]
        self.session_cfg = {
            "name": image_name,
            "model": model_name,
            "ndim": image_layer.ndim,
            "shape": image_layer.data.shape,
            "affine": image_layer.affine,
            "spacing": image_layer.scale,
        }

        # Create the target label array and layer
        self._data_result = np.zeros(self.session_cfg["shape"], dtype=np.uint8)

        _layer_res = Labels(
            self._data_result,
            name=self.label_layer_name,
            affine=self.session_cfg["affine"],
            colormap=self.colormap[0],
        )

        # Add Layer to Viewer
        if self.label_layer_name in self._viewer.layers:
            self._viewer.layers.remove(self.label_layer_name)
        self._viewer.add_layer(_layer_res)

        # Lock the Session
        self._lock_session()

    def on_next(self) -> None:
        """
        Prepares the next label layer for interactions in the viewer.

        Retrieves the index of the last labeled object, renames the current label layer with
        this index, unbinds the original data by creating a deep copy, and clears all interaction
        layers. A new label layer with an updated colormap is then added to the viewer.
        """
        # Get index of the last object
        _index = determine_layer_index(
            self.label_layer_name,
            [layer.name for layer in self._viewer.layers],
            splitter=" - object ",
        )
        # Rename layer and unbind data
        _layer = self._viewer.layers[self.label_layer_name]
        _layer.name = f"{_layer.name} - object {_index}"
        _layer.data = _layer.data.copy()

        # Clear all interaction layers
        self._clear_layers()

        # Add a new label to the viewer
        _layer_res = Labels(
            self._data_result,
            name=self.label_layer_name,
            affine=self.session_cfg["affine"],
            colormap=self.colormap[_index + 1],
        )
        self._viewer.add_layer(_layer_res)

    def on_prompt_selected(self) -> None:
        """
        Updates the prompt index for each layer in the viewer based on the selected prompt.

        Iterates through the layers specified in `layer_dict`, sets the prompt index for each
        corresponding layer using the current prompt button selection, and refreshes each layer to
        apply the updated prompt.
        """
        for layer_name in self.layer_dict.values():
            if layer_name in self._viewer.layers:
                self._viewer.layers[layer_name].set_prompt(self.prompt_button.index)
                self._viewer.layers[layer_name].refresh()

    def on_interaction_selected(self) -> None:
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

    def on_run(self, *args, **kwargs) -> None:
        """
        Executes the run method of the selected layer and triggers inference if data is obtained.

        Args:
            *args: Additional arguments for the run method.
            **kwargs: Additional keyword arguments for the run method.
        """
        _index = self.interaction_button.index
        _layer_name = self.layer_dict.get(_index)
        if _layer_name is not None and _layer_name in self._viewer.layers:
            if not self._viewer.layers[_layer_name].is_free():
                _data = self._viewer.layers[_layer_name].get_last()
                self._viewer.layers[_layer_name].run()
                self.inference(_data, _index)

    def on_auto_run(self, event: Any) -> None:
        """
        Automatically run an action if the checkbox is checked and data is added.

        Args:
            event (Any): The event triggering the auto-run, with information about
                the layer action and data.
        """
        if (
            self.run_ckbx.isChecked()
            and event.action == ActionType.ADDED
            and not self._viewer.layers[event.source.name].is_free()
        ):
            self.on_run()

    def on_layer_selected(self, *args, **kwargs) -> None:
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

    # Inference Behaviour
    def inference(self, data: Any, index: int) -> None:
        """
        Performs inference on the provided data.

        Args:
            _data: The data obtained from the layer's run method.
            _index (int): The index of the layer type, corresponding to the layer_dict key.
        """
        print(
            f"Inference for interaction {index} and prompt {self.prompt_button.index == 0} and valid data {data is not None} "
        )
