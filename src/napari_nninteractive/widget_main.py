import os
import warnings
from pathlib import Path
from typing import Any, Optional

import nnInteractive
import numpy as np
import torch
from batchgenerators.utilities.file_and_folder_operations import join, load_json
from napari.viewer import Viewer
from nnunetv2.utilities.find_class_by_name import recursive_find_python_class
from qtpy.QtWidgets import QWidget
from qtpy.QtCore import QTimer

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

    # Event Handlers
    def on_init(self, *args, **kwargs):
        """
        Initialize the inference session and setup layers for interaction.

        This method sets up the nnInteractiveInferenceSession, loading from a
        pre-trained model folder and initializing properties based on the viewer layer.
        """
        super().on_init(*args, **kwargs)
        if self.session is None:
            # Get inference class from Checkpoint
            if Path(self.checkpoint_path).joinpath("inference_session_class.json").is_file():
                inference_class = load_json(
                    Path(self.checkpoint_path).joinpath("inference_session_class.json")
                )
                if isinstance(inference_class, dict):
                    inference_class = inference_class["inference_class"]
            else:
                inference_class = "nnInteractiveInferenceSession"

            inference_class = recursive_find_python_class(
                join(nnInteractive.__path__[0], "inference"),
                inference_class,
                "nnInteractive.inference",
            )

            # Initialize the Session
            self.session = inference_class(
                device=torch.device("cuda:0"),  # can also be cpu or mps. CPU not recommended
                use_torch_compile=False,
                torch_n_threads=os.cpu_count(),
                verbose=False,
                do_autozoom=self.propagate_ckbx.isChecked(),
            )

            self.session.initialize_from_trained_model_folder(
                self.checkpoint_path,
                0,
                "checkpoint_final.pth",
            )

        _data = self._viewer.layers[self.session_cfg["name"]].data
        _data = _data[np.newaxis, ...]

        if self.session_cfg["ndim_source"] == 2:
            _data = _data[np.newaxis, ...]

        self.session.set_image(_data, {"spacing": self.session_cfg["spacing"]})

        self.session.set_target_buffer(self._data_result)
        self._scribble_brush_size = self.session.preferred_scribble_thickness[
            self._viewer.dims.not_displayed[0]
        ]
        # Set the prompt type to positive
        self.prompt_button._uncheck()
        self.prompt_button._check(0)

    def on_model_selected(self):
        """Reset the current session completely"""
        super().on_model_selected()
        self.session = None

    def on_image_selected(self):
        """Reset the current sessions interaction but keep the session itself"""
        super().on_image_selected()
        if self.session is not None:
            self.session.reset_interactions()

    def on_reset_interactions(self):
        """Reset only the current interaction"""
        _ind = self.interaction_button.index
        super().on_reset_interactions()
        if self.session is not None:
            self.session.reset_interactions()

        self._viewer.layers[self.label_layer_name].refresh()

        self.interaction_button._check(_ind)
        self.on_interaction_selected()
        # self.prompt_button._uncheck()
        self.prompt_button._on_button_pressed(0)

    def on_next(self):
        """Reset the Interactions of current session"""
        _ind = self.interaction_button.index
        super().on_next()
        if self.session is not None:
            self.session.reset_interactions()

        # if (
        #     self.use_init_ckbx.isChecked()
        #     and self.label_for_init.currentText() in self._viewer.layers
        # ):
        #     self.init_with_mask()

        self._viewer.layers[self.label_layer_name].refresh()

        self.interaction_button._check(_ind)
        self.on_interaction_selected()
        self.prompt_button._check(0)

    def on_propagate_ckbx(self, *args, **kwargs):
        if self.session is not None:
            self.session.set_do_autozoom(self.propagate_ckbx.isChecked())
            
    def on_center_on_labels_ckbx(self, *args, **kwargs):
        """Toggle whether to center the camera on labels when changing axes"""
        # No need for implementation here, just used as a flag

    def on_axis_change(self, event: Any):
        """Handle axis change event - adjust brush size and potentially center view on labels"""
        if self.session is not None:
            # Update scribble brush size
            self._scribble_brush_size = self.session.preferred_scribble_thickness[
                self._viewer.dims.not_displayed[0]
            ]
            if self.scribble_layer_name in self._viewer.layers:
                self._viewer.layers[self.scribble_layer_name].brush_size = self._scribble_brush_size
                
            # Center on labels if enabled - use a short timer to ensure axis change is complete
            if hasattr(self, 'center_on_labels_ckbx') and self.center_on_labels_ckbx.isChecked():
                # Use Qt timer for a short delay to ensure the axis change is complete
                QTimer.singleShot(50, self._center_on_labels)

    def _center_on_labels(self):
        """Center the camera view on the center of mass of current label layer"""
        if self.label_layer_name in self._viewer.layers:
            label_layer = self._viewer.layers[self.label_layer_name]
            label_data = label_layer.data
            
            # Only center if there are actually labels
            if not np.any(label_data > 0):
                return
                
            # Get indices where label data is non-zero
            indices = np.where(label_data > 0)
            
            if not indices or len(indices[0]) == 0:
                return
            
            # Calculate center of mass (mean position of all labeled voxels)
            center_of_mass = np.array([np.mean(dim_indices) for dim_indices in indices])
            
            # Calculate bounding box of the labeled region
            min_coords = np.array([np.min(indices[i]) for i in range(len(indices))])
            max_coords = np.array([np.max(indices[i]) for i in range(len(indices))])
            
            # Get current view dimensions
            ndim = label_data.ndim
            displayed_dims = list(self._viewer.dims.displayed)
            not_displayed = list(self._viewer.dims.not_displayed)
            
            # For non-displayed dimensions, set slice to the center of mass
            current_step = list(self._viewer.dims.current_step)
            for dim in not_displayed:
                if dim < ndim:
                    current_step[dim] = int(center_of_mass[dim])
            
            # Update the viewer position for non-displayed dimensions
            self._viewer.dims.current_step = tuple(current_step)
            
            # Center the camera on the center of mass for displayed dimensions
            displayed_center = np.array([center_of_mass[dim] for dim in displayed_dims])
            
            # Set the center explicitly (this works for both 2D and 3D)
            self._viewer.camera.center = displayed_center
            
            # Calculate the size of the bounding box in displayed dimensions
            if displayed_dims:
                # Get dimensions of the bounding box in displayed dimensions
                bbox_sizes = []
                for dim in displayed_dims:
                    if dim < len(min_coords):
                        size = max_coords[dim] - min_coords[dim] + 1
                        # Get the scale (pixel size) for this dimension
                        scale = label_layer.scale[dim] if dim < len(label_layer.scale) else 1.0
                        bbox_sizes.append(size * scale)
                
                if bbox_sizes:
                    # Add 20% padding around the bounding box
                    max_size = max(bbox_sizes) * 1.4
                    
                    # Set a reasonable zoom factor based on the bounding box size
                    # Use a fallback approach that doesn't depend on canvas.size()
                    if max_size > 0:
                        self._viewer.camera.zoom = 800 / max_size

    def on_reset_all(self, *args, **kwargs):
        """Reset the plugin to initial state and close all layers, preserving object names"""
        if self.session is not None:
            self.session.reset_interactions()
            self.session = None
            
        # Call the parent implementation to handle UI reset and layer closing
        super().on_reset_all(*args, **kwargs)

    # Inference Behaviour

    def add_interaction(self):
        _index = self.interaction_button.index
        _layer_name = self.layer_dict.get(_index)
        if (
            _layer_name is not None
            and _layer_name in self._viewer.layers
            and not self._viewer.layers[_layer_name].is_free()
        ):
            data = self._viewer.layers[_layer_name].get_last()

            self._viewer.layers[_layer_name].run()
            # self.inference(_data, _index)

            if data is not None:
                _prompt = self.prompt_button.index == 0
                _auto_run = self.run_ckbx.isChecked()

                if _index == 0:
                    self._viewer.layers[self.point_layer_name].refresh(force=True)
                    self.session.add_point_interaction(data, _prompt, _auto_run)
                elif _index == 1:
                    # add_bbox_interaction expects [[xmin, xmax], [ymin, ymax], [zmin, zmax]]
                    _min = np.min(data, axis=0)
                    _max = np.max(data, axis=0)
                    bbox = [[_min[0], _max[0]], [_min[1], _max[1]], [_min[2], _max[2]]]
                    self.session.add_bbox_interaction(bbox, _prompt, _auto_run)
                elif _index == 2:
                    self.session.add_scribble_interaction(data, _prompt, _auto_run)
                elif _index == 3:
                    self.session.add_lasso_interaction(data, _prompt, _auto_run)

                self._viewer.layers[self.label_layer_name].refresh()

    def on_load_mask(self):

        _layer_data = self._viewer.layers[self.label_for_init.currentText()].data

        assert (
            _layer_data.shape == self.session_cfg["shape"]
        )  # Labels and Image should have same shape

        data = _layer_data == self.class_for_init.value()

        if np.any(data):
            if self.session is not None:
                self.session.add_initial_seg_interaction(data.astype(np.uint8), run_prediction=self.auto_refine.isChecked())
                self._viewer.layers[self.label_layer_name].refresh()
        else:
            warnings.warn("Mask is not valid - probably its empty", UserWarning, stacklevel=1)
