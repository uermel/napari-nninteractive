from pathlib import Path
from typing import Any, Optional

import numpy as np
import torch
from napari.layers import Labels
from napari.layers.base._base_constants import ActionType
from napari.viewer import Viewer
from nnunetv2.inference.nnInteractive.interactive_inference import (
    nnInteractiveInferenceSession,
)
from qtpy.QtWidgets import QWidget

from napari_nninteractive.widget_controls import LayerControls


class nnInteractiveWidget_(LayerControls):
    pass


class nnInteractiveWidget(LayerControls):
    """
    A widget for the nnInteractive plugin in Napari that manages model inference sessions
    and allows interactive layer-based actions.
    """

    def __init__(self, viewer: Viewer, parent: Optional[QWidget] = None):
        """
        Initialize the nnInteractiveWidget.
        """
        super().__init__(viewer, parent)
        self.session = None

    def _auto_run(self, event: Any):
        """
        Automatically run an action if a layer's checkbox is checked and data is added.

        Args:
            event (Any): The event triggering the auto-run, with information about
                the layer action and data.
        """
        if (
            self.run_ckbx.isChecked()
            and event.action == ActionType.ADDED
            and self._viewer.layers[event.source.name].data_current is not None
        ):
            self.on_run()

    def on_init(self, *args, **kwargs):
        """
        Initialize the inference session and setup layers for interaction.

        This method sets up the nnInteractiveInferenceSession, loading from a
        pre-trained model folder and initializing properties based on the viewer layer.
        """
        super().on_init(*args, **kwargs)
        if self.session is None:
            self.session = nnInteractiveInferenceSession(
                device=torch.device("cuda:0"),  # can also be cpu or mps. CPU not recommended
                use_torch_compile=False,
                torch_n_threads=8,
                point_interaction_radius=4,  # may be adapted depending on final nnInteractive version
                point_interaction_use_etd=True,  # may be adapted depending on final nnInteractive version
                verbose=False,
                use_background_preprocessing=self.bg_preprocessing_ckbx.isChecked(),
            )

            self.session.initialize_from_trained_model_folder(
                Path(self.nnUNet_results).joinpath(
                    self.nnUNet_dataset, self.model_selection.currentText()
                ),
                5,
                "checkpoint_best.pth",
            )

        _layer = self._viewer.layers[self.session_cfg["name"]]
        _data = _layer.data[np.newaxis, ...]
        _properties = {"spacing": _layer.scale}
        self._data_res = np.zeros(_data.shape[1:], dtype=np.uint8)

        self.session.set_image(_data, _properties)
        self.session.set_target_buffer(self._data_res)

        self.label_layer_name = f"nnInteractive - Label Layer - {self.session_cfg["name"]} - {self.session_cfg["model"]}"
        if self.label_layer_name in self._viewer.layers:
            self._viewer.layers.remove(self.label_layer_name)

        _layer_res = Labels(self._data_res, name=self.label_layer_name, affine=_layer.affine)
        self._viewer.add_layer(_layer_res)

    def _reset(self):
        """Reset the Interactions of current session"""
        super()._reset()
        if self.session is not None:
            self.session.reset_interactions()

    def _reset_interactions(self):
        if self.session is not None:
            self.session.reset_interactions()
            self.clear_layers()

            self.label_layer_name = f"nnInteractive - Label Layer - {self.session_cfg["name"]} - {self.session_cfg["model"]}"
            if self.label_layer_name in self._viewer.layers:
                self._viewer.layers.remove(self.label_layer_name)

            _layer_res = Labels(
                self._data_res, name=self.label_layer_name, affine=self.session_cfg["affine"]
            )
            self._viewer.add_layer(_layer_res)

    def on_model_selection(self):
        """Reset the Session if another model is selected"""
        self.session = None

    def inference(self, data: Any, index: int):
        """
        Performs inference on the provided data.

        Args:
            data: The data obtained from the layer's run method.
            index (int): The index of the layer type, corresponding to the layer_dict key.
        """
        if data is not None:
            if index == 0:
                self.session.add_point_interaction(data, self.prompt_button.index == 0)
            elif index == 1:
                # add_bbox_interaction expects [[xmin, xmax], [ymin, ymax], [zmin, zmax]]
                _min = np.min(data, axis=0)
                _max = np.max(data, axis=0)
                bbox = [[_min[0], _max[0]], [_min[1], _max[1]], [_min[2], _max[2]]]
                self.session.add_bbox_interaction(bbox, self.prompt_button.index == 0)
            elif index == 2:
                self.session.add_scribble_interaction(data, self.prompt_button.index == 0)
            self._viewer.layers[self.label_layer_name].refresh()
