from pathlib import Path
from typing import Any, Optional

import nnunetv2
import numpy as np
import torch
from batchgenerators.utilities.file_and_folder_operations import join, load_json
from napari.viewer import Viewer
from nnunetv2.utilities.find_class_by_name import recursive_find_python_class
from qtpy.QtWidgets import QWidget

from napari_nninteractive.widget_controls import LayerControls


class nnInteractiveWidget_(LayerControls):
    """Just a Debug Dummy without all the machine learning stuff"""


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
        self._viewer.dims.events.order.connect(self.on_axis_change)

    # Base Behaviour
    def _reset_session(self):
        """Reset the current session"""
        super()._reset_session()
        self.session = None

    # Event Handlers
    def on_init(self, *args, **kwargs):
        """
        Initialize the inference session and setup layers for interaction.

        This method sets up the nnInteractiveInferenceSession, loading from a
        pre-trained model folder and initializing properties based on the viewer layer.
        """
        super().on_init(*args, **kwargs)
        if self.session is None:
            _cktp = Path(self.nnUNet_results).joinpath(
                self.nnUNet_dataset, self.model_selection.currentText()
            )

            # Get inference class from Checkpoint
            if Path(_cktp).joinpath("inference_session_class.json").is_file():
                inference_class = load_json(Path(_cktp).joinpath("inference_session_class.json"))
            else:
                inference_class = "nnInteractiveInferenceSession"
            print(inference_class)

            inference_class = recursive_find_python_class(
                join(nnunetv2.__path__[0], "inference", "nnInteractive"),
                inference_class,
                "nnunetv2.inference.nnInteractive",
            )

            # Initialize the Session
            self.session = inference_class(
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
                "checkpoint_final.pth",
            )

        _data = self._viewer.layers[self.session_cfg["name"]].data
        _data = _data[np.newaxis, ...]

        if self.session_cfg["ndim_source"] == 2:
            _data = _data[np.newaxis, ...]

        self.session.set_image(_data, {"spacing": self.session_cfg["spacing"]})

        self.session.set_target_buffer(self._data_result)
        self._scribble_brush_size = self.session.recommended_scribble_thickness[
            self._viewer.dims.not_displayed[0]
        ]

    def on_reset_interations(self):
        """Reset only the current interaction"""
        super().on_reset_interations()
        if self.session is not None:
            self.session.reset_interactions()
        self._viewer.layers[self.label_layer_name].refresh()

    def on_next(self):
        """Reset the Interactions of current session"""
        super().on_next()
        if self.session is not None:
            self.session.reset_interactions()
        self._viewer.layers[self.label_layer_name].refresh()

    def on_axis_change(self, event: Any):
        """Change the brush size of the scribble layer when the axis changes"""
        if self.session is not None:
            self._scribble_brush_size = self.session.recommended_scribble_thickness[
                self._viewer.dims.not_displayed[0]
            ]
            if self.scribble_layer_name in self._viewer.layers:
                self._viewer.layers[self.scribble_layer_name].brush_size = self._scribble_brush_size

    # Inference Behaviour
    def inference(self, data: Any, index: int):
        """
        Performs inference on the provided data.

        Args:
            data: The data obtained from the layer's run method.
            index (int): The index of the layer type, corresponding to the layer_dict key.
        """
        if data is not None:

            if index == 0:
                self._viewer.layers[self.point_layer_name].refresh(force=True)
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
