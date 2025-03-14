import os
import warnings
from pathlib import Path
from typing import Any, Optional

import numpy as np
from huggingface_hub import snapshot_download
from napari._qt.layer_controls.qt_layer_controls_container import layer_to_controls
from napari.layers import Labels
from napari.layers.base._base_constants import ActionType
from napari.utils.notifications import show_warning
from napari.utils.transforms import Affine
from napari.viewer import Viewer
from qtpy.QtWidgets import QFileDialog, QWidget

from napari_nninteractive.controls.bbox_controls import CustomQtBBoxControls
from napari_nninteractive.controls.lasso_controls import CustomQtLassoControls
from napari_nninteractive.controls.point_controls import CustomQtPointsControls
from napari_nninteractive.controls.scribble_controls import CustomQtScribbleControls
from napari_nninteractive.layers.bbox_layer import BBoxLayer
from napari_nninteractive.layers.lasso_layer import LassoLayer
from napari_nninteractive.layers.point_layer import SinglePointLayer
from napari_nninteractive.layers.scribble_layer import ScribbleLayer
from napari_nninteractive.utils.utils import ColorMapper, determine_layer_index
from napari_nninteractive.widget_gui import BaseGUI

layer_to_controls[SinglePointLayer] = CustomQtPointsControls
layer_to_controls[BBoxLayer] = CustomQtBBoxControls
layer_to_controls[ScribbleLayer] = CustomQtScribbleControls
layer_to_controls[LassoLayer] = CustomQtLassoControls


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
        self.lasso_layer_name = "nnInteractive - Lasso Layer"
        self.layer_dict = {
            0: self.point_layer_name,
            1: self.bbox_layer_name,
            2: self.scribble_layer_name,
            3: self.lasso_layer_name,
        }

        self.label_layer_name = "nnInteractive - Label Layer"
        self.mask_init_layer_name = "nnInteractive - Initial Mask Layer"
        self.colormap = ColorMapper(49, seed=0.5, background_value=0)
        self._scribble_brush_size = 5

        self._viewer.layers.selection.events.active.connect(self.on_layer_selected)

    # Layer Handling
    def _clear_layers(self) -> None:
        """Removes all layers in the viewer that are managed by this class."""
        layer_names = list(self.layer_dict.values())
        for layer_name in layer_names:
            if layer_name in self._viewer.layers:
                self._viewer.layers.remove(layer_name)

    def add_point_layer(self) -> None:
        """Adds a single point layer to the viewer."""
        point_layer = SinglePointLayer(
            name=self.point_layer_name,
            ndim=self.session_cfg["ndim"],
            affine=self.session_cfg["affine"],
            # scale=self.session_cfg["spacing"],
            # translate=self.session_cfg["origin"],
            # rotate=self.session_cfg["direction"],
            metadata=self.session_cfg["metadata"],
            opacity=0.7,
            size=3,
            prompt_index=self.prompt_button.index,
        )

        # point_layer.size = 0.2
        point_layer.events.finished.connect(self.on_interaction)
        self._viewer.add_layer(point_layer)

    def add_bbox_layer(self) -> None:
        """Adds a bounding box layer to the viewer."""
        bbox_layer = BBoxLayer(
            name=self.bbox_layer_name,
            ndim=self.session_cfg["ndim"],
            affine=self.session_cfg["affine"],
            # scale=self.session_cfg["spacing"],
            # translate=self.session_cfg["origin"],
            # rotate=self.session_cfg["direction"],
            metadata=self.session_cfg["metadata"],
            prompt_index=self.prompt_button.index,
            opacity=0.3,
        )
        bbox_layer.events.data.connect(self.on_interaction)
        self._viewer.add_layer(bbox_layer)

    def add_scribble_layer(self) -> None:
        """Adds a scribble layer to the viewer with an initial blank data array."""
        _data = np.zeros(self.session_cfg["shape"], dtype=np.uint8)
        scribble_layer = ScribbleLayer(
            data=_data,
            name=self.scribble_layer_name,
            affine=self.session_cfg["affine"],
            # scale=self.session_cfg["spacing"],
            # translate=self.session_cfg["origin"],
            # rotate=self.session_cfg["direction"],
            metadata=self.session_cfg["metadata"],
            prompt_index=self.prompt_button.index,
        )

        scribble_layer.brush_size = self._scribble_brush_size

        scribble_layer.events.finished.connect(self.on_interaction)
        self._viewer.add_layer(scribble_layer)

    def add_lasso_layer(self) -> None:
        """Adds a lasso layer to the viewer."""
        lasso_layer = LassoLayer(
            shape=self.session_cfg["shape"],
            name=self.lasso_layer_name,
            ndim=self.session_cfg["ndim"],
            affine=self.session_cfg["affine"],
            # scale=self.session_cfg["spacing"],
            # translate=self.session_cfg["origin"],
            # rotate=self.session_cfg["direction"],
            metadata=self.session_cfg["metadata"],
            prompt_index=self.prompt_button.index,
            opacity=0.3,
        )
        lasso_layer.events.data.connect(self.on_interaction)
        self._viewer.add_layer(lasso_layer)

    def add_label_layer(self) -> None:
        """
        Check if a layer with the layer_name already exists. If yes rename this by adding an index
        and afterward create the layer
        :return:
        :rtype:
        """
        if self.label_layer_name in self._viewer.layers:
            _index = determine_layer_index(
                names=[layer.name for layer in self._viewer.layers if isinstance(layer, Labels)],
                prefix="object ",
                postfix=f" - {self.session_cfg['name']}",
            )
            _layer = self._viewer.layers[self.label_layer_name]
            
            # Get the current object name from the dropdown (if any)
            object_name = self.object_name_combo.currentText().strip()
            name_suffix = f" ({object_name})" if object_name else ""
            
            _layer.name = f"object {_index}{name_suffix} - {self.session_cfg['name']}"
            _layer.data = _layer.data.copy()
            _index += 1
        else:
            _index = 0

        _layer_res = Labels(
            self._data_result,
            name=self.label_layer_name,
            opacity=0.3,
            affine=self.session_cfg["affine"],
            # scale=self.session_cfg["spacing"],
            # translate=self.session_cfg["origin"],
            # rotate=self.session_cfg["direction"],
            colormap=self.colormap[_index],
            metadata=self.session_cfg["metadata"],
        )
        _layer_res._source = self.session_cfg["source"]

        self._viewer.add_layer(_layer_res)

    def add_mask_init_layer(self) -> None:
        """
        Check if a layer with the layer_name already exists. If yes rename this by adding an index
        and afterward create the layer
        :return:
        :rtype:
        """

        _layer_res = Labels(
            np.zeros_like(self._data_result),
            name=self.mask_init_layer_name,
            opacity=0.3,
            affine=self.session_cfg["affine"],
            # scale=self.session_cfg["spacing"],
            # translate=self.session_cfg["origin"],
            # rotate=self.session_cfg["direction"],
            metadata=self.session_cfg["metadata"],
        )
        _layer_res._source = self.session_cfg["source"]

        self._viewer.add_layer(_layer_res)

    def init_with_mask(self):
        _layer_data = self._viewer.layers[self.label_for_init.currentText()].data

        assert (
            _layer_data.shape == self.session_cfg["shape"]
        )  # Labels and Image should have same shape

        self._data_result = (_layer_data == self.class_for_init.value()).astype(np.uint8)
        self.session.set_target_buffer(self._data_result)
        self._viewer.layers[self.label_layer_name].data = self._data_result

    # Event Handlers
    def on_init(self, *args, **kwargs) -> None:
        """
        Initializes the session by configuring the selected model and image and creating a label layer.

        Retrieves the selected model and image names from the GUI, extracts relevant data from the
        image layer, and creates a corresponding label layer in the viewer.
        """
        # --- MODEL HANDLING --- #
        # Get all model and image from the GUI
        image_name = self.image_selection.currentText()

        if image_name == "":
            raise ValueError("No Image Layer selected")

        model_name = self.model_selection.currentText()
        model_name_local = self.model_selection_local.text()
        if model_name_local != "" and Path(model_name_local).exists():
            # Use Local Checkpoint
            model_name = Path(model_name_local).name
            self.checkpoint_path = model_name_local
        else:
            # Download Checkpoint
            repo_id = "nnInteractive/nnInteractive"
            force_download = False
            download_path = snapshot_download(
                repo_id=repo_id, allow_patterns=[f"{model_name}/*"], force_download=force_download
            )
            self.checkpoint_path = Path(download_path).joinpath(model_name)
        print(f"Using Model {model_name} at : {self.checkpoint_path}")

        # --- DATA HANDLING --- #
        # Get everything we need from the image layer
        image_layer = self._viewer.layers[image_name]

        _ndim_source = image_layer.ndim
        _affine_source = image_layer.affine

        _ndim = image_layer.ndim
        _shape = image_layer.data.shape
        _affine = image_layer.affine
        _spacing = image_layer.scale
        _origin = image_layer.translate
        _direction = image_layer.rotate
        _shear = image_layer.shear

        # 1. Check and Correct Non-orthogonal Data
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", FutureWarning)
            if not image_layer._slice_input.is_orthogonal(_affine):
                _origin = _affine.translate
                # we ignore direction and shear
                _affine = Affine(scale=_spacing, translate=_origin)
                show_warning(
                    "Your data is non-orthogonal. This is not supported by napari. "
                    "To fix this the direction is ignored during visualizing which changes the appearance (only visual) of your data. "
                )
                _step = self._viewer.dims.current_step
                image_layer.affine = _affine
                self._viewer.dims.current_step = _step

        # 2. Convert 2D to dummy 3D data
        if _ndim == 2:
            _ndim = 3
            _shape = np.insert(_shape, 0, 1)

            _spacing = np.insert(_spacing, 0, 1)
            _origin = np.insert(_affine.translate, 0, 0)
            _direction = np.eye(_ndim)
            _direction[-2:, -2:] = _affine.rotate
            _shear = np.insert(_affine.shear, 0, 0)

        _affine = Affine(scale=_spacing, translate=_origin, rotate=_direction, shear=_shear)

        self.session_cfg = {
            "name": image_name,
            "model": model_name,
            "ndim": _ndim,
            "ndim_source": image_layer.ndim,
            "shape": _shape,
            "affine": _affine,
            "affine_source": _affine_source,
            "spacing": _spacing,
            "source": image_layer.source,
            "metadata": image_layer.metadata,
        }
        # Create the target label array and layer
        self._data_result = np.zeros(self.session_cfg["shape"], dtype=np.uint8)

        # Add Layer
        self.add_label_layer()

        # Lock the Session
        self._lock_session()

    def on_reset_interactions(self):
        """Reset only the current interaction"""
        super().on_reset_interactions()
        self.on_layer_selected()

    def on_next(self) -> None:
        """
        Prepares the next label layer for interactions in the viewer.

        Retrieves the index of the last labeled object, renames the current label layer with
        this index, unbinds the original data by creating a deep copy, and clears all interaction
        layers. A new label layer with an updated colormap is then added to the viewer.
        """
        # Rename the current layer and add a new one
        self.add_label_layer()
        # Clear all interaction layers
        self._clear_layers()
        # Clear the object name selection
        self.object_name_combo.setCurrentIndex(0)
        self.prompt_button._uncheck()
        self.prompt_button._check(0)

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
            self._viewer.layers.selection.active = self._viewer.layers[layer_name]

            self._viewer.layers.selection.events.active(value=self._viewer.layers[layer_name])

        elif self.interaction_type == 0:  # Add Point Layer
            self.add_point_layer()
        elif self.interaction_type == 1:  # Add BBox Layer
            self.add_bbox_layer()
        elif self.interaction_type == 2:  # Add Scrible Layer
            self.add_scribble_layer()
        elif self.interaction_type == 3:  # Add Lasso Layer
            self.add_lasso_layer()

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", FutureWarning)
            self._viewer.window._qt_viewer.setFocus()

    def on_run(self):
        if self.session is not None:
            self.session._predict()
            self._viewer.layers[self.label_layer_name].refresh()

    def on_interaction(self, event: Any):
        if (
            self.add_ckbx.isChecked()
            and event.action == ActionType.ADDED
            and not self._viewer.layers[event.source.name].is_free()
        ):
            self._viewer.layers[event.source.name].refresh()

            self.add_interaction()

    def on_layer_selected(self, *args, **kwargs) -> None:
        """
        Updates the interaction button and sets the `interaction_type` based on
        the currently selected layer in the viewer.

        Args:
            *args: Additional arguments for the method.
            **kwargs: Additional keyword arguments for the method.
        """
        _layer = self._viewer.layers.selection.active

        if _layer is None:
            key = None
        else:
            key = next((k for k, v in self.layer_dict.items() if v == _layer.name), None)

        self.interaction_type = key
        self.interaction_button._uncheck()
        self.interaction_button._check(self.interaction_type)

    # Inference Behaviour
    def inference(self, data: Any, index: int) -> None:
        """
        Performs inference on the provided data.

        Args:
            data: The data obtained from the layer's run method.
            index (int): The index of the layer type, corresponding to the layer_dict key.
        """
        print(
            f"Inference for interaction {index} and prompt {self.prompt_button.index == 0} and valid data {data is not None} "
        )

    def _export(self) -> None:
        """Export all Label layers belonging to the current image & model pair as separate files
        using the napari plugins. When separate_omezarr_ckbx is checked, each segmentation is also exported 
        as a separate OME-Zarr file."""
        _img_layer = self._viewer.layers[self.session_cfg["name"]]
        _img_file = Path(_img_layer.source.path).name
        _dtype = ".nii.gz" if str(_img_file).endswith(".nii.gz") else Path(_img_file).suffix
        _output_file = _img_file.replace(_dtype, "")

        _dialog = QFileDialog(self)
        _dialog.setDirectory(os.getcwd())

        _output_dir = _dialog.getExistingDirectory(
            self,
            "Select an Output Directory",
            options=QFileDialog.DontUseNativeDialog | QFileDialog.ShowDirsOnly,
        )

        if _output_dir == "":
            return

        elif Path(_output_dir).is_dir():
            _output_dir = Path(_output_dir).joinpath(f"{_output_file}_nnInteractive")
            Path(_output_dir).mkdir(exist_ok=True)

            # Check if we should export as separate OME-Zarr files
            export_as_omezarr = self.separate_omezarr_ckbx.isChecked()

            for _layer in self._viewer.layers:
                if self.label_layer_name == _layer.name:
                    _index = determine_layer_index(
                        names=[
                            layer.name for layer in self._viewer.layers if isinstance(layer, Labels)
                        ],
                        prefix="object ",
                        postfix=f" - {self.session_cfg['name']}",
                    )
                    # No object name for the current working layer
                    object_name = ""
                elif _layer.name.startswith("object ") and _layer.name.endswith(
                    f" - {self.session_cfg['name']}"
                ):
                    # Extract the object index and possibly the object name
                    layer_name_part = _layer.name.replace(f" - {self.session_cfg['name']}", "")
                    # Check if there's an object name in parentheses
                    if " (" in layer_name_part and ")" in layer_name_part:
                        base_part = layer_name_part.split(" (")[0].strip()
                        name_part = layer_name_part.split(" (")[1].split(")")[0]
                        try:
                            _index = int(base_part.replace("object ", ""))
                            object_name = name_part
                        except ValueError:
                            # If we can't convert to int, skip this layer
                            continue
                    else:
                        try:
                            _index = int(layer_name_part.replace("object ", ""))
                            object_name = ""
                        except ValueError:
                            # If we can't convert to int, skip this layer
                            continue
                else:
                    continue

                # Add object name to filename if it exists
                name_suffix = f"_{object_name}" if object_name else ""
                _file_name = f"{_output_file}_{str(_index).zfill(4)}{name_suffix}{_dtype}"
                _file = str(Path(_output_dir).joinpath(_file_name))

                # reverse the corrections for non-orthogonal data and convert dummy 3d back to 2d
                _data = _layer.data[0] if self.session_cfg["ndim_source"] == 2 else _layer.data
                _layer_temp = Labels(
                    _data,
                    name="_temp",
                    affine=self.session_cfg["affine_source"],
                    metadata=self.session_cfg["metadata"],
                )

                _layer_temp._source = self.session_cfg["source"]
                _layer_temp.save(_file)
                
                # If separate OME-Zarr export is enabled, export each object as a separate OME-Zarr file
                if export_as_omezarr:
                    try:
                        import zarr
                        import numpy as np
                        
                        # Create a binary mask for the current object (all non-zero values are set to 1)
                        binary_mask = (_data > 0).astype(np.uint8)
                        
                        # Create OME-Zarr file path with object name if it exists
                        _zarr_file_name = f"{_output_file}_{str(_index).zfill(4)}{name_suffix}.zarr"
                        _zarr_path = Path(_output_dir).joinpath(_zarr_file_name)
                        
                        # Create the zarr store with proper OME-Zarr v0.4 structure
                        root = zarr.open(str(_zarr_path), mode='w')
                        
                        # Save the binary mask directly at the root level as "labels" array
                        # napari expects the data at this level
                        chunk_size = (128, 128, 128) if len(binary_mask.shape) == 3 else (128, 128)
                        mask_dataset = root.create_dataset(
                            '0',  # Use '0' as the main image dataset name
                            data=binary_mask,
                            chunks=chunk_size,
                            dtype=np.uint8
                        )
                        
                        # Add OME-Zarr metadata including object name if it exists
                        layer_display_name = f"Object {_index}"
                        if object_name:
                            layer_display_name = f"{layer_display_name} ({object_name})"
                            
                        root.attrs['omero'] = {
                            'name': f'{layer_display_name} - {self.session_cfg["name"]}',
                            'version': '0.4'  # Use a stable version
                        }
                        
                        # Add coordinate metadata
                        axes = []
                        if len(binary_mask.shape) == 3:
                            axes = [
                                {'name': 'z', 'type': 'space'},
                                {'name': 'y', 'type': 'space'},
                                {'name': 'x', 'type': 'space'}
                            ]
                        else:
                            axes = [
                                {'name': 'y', 'type': 'space'},
                                {'name': 'x', 'type': 'space'}
                            ]
                            
                        multiscales = [{
                            'version': '0.4',
                            'name': layer_display_name,
                            'axes': axes,
                            'datasets': [{'path': '0'}]
                        }]
                        
                        root.attrs['multiscales'] = multiscales
                        
                    except ImportError:
                        from napari.utils.notifications import show_warning
                        show_warning(
                            "Cannot export as OME-Zarr: zarr package is not installed. "
                            "Install it with 'pip install zarr'."
                        )
                    except Exception as e:
                        from napari.utils.notifications import show_warning
                        show_warning(f"Error exporting OME-Zarr file: {str(e)}")

                del _layer_temp
        else:
            raise ValueError("Output path has to be a directory, not a file")

    def on_object_name_selected(self, text=None, *args, **kwargs) -> None:
        """
        Updates the name of the current label layer when a new object name is selected.
        """
        if self.label_layer_name in self._viewer.layers:
            # If text is provided by the signal, use it, otherwise get from combobox
            object_name = text if text is not None else self.object_name_combo.currentText().strip()
            
            # Get the current layer's name
            current_layer = self._viewer.layers[self.label_layer_name]
            
            # If the layer is still using the default name, don't modify it
            if current_layer.name == self.label_layer_name:
                return
                
            # Parse the current layer name to extract the index
            layer_name_part = current_layer.name.replace(f" - {self.session_cfg['name']}", "")
            
            # Extract the base part (with "object" and the index)
            if " (" in layer_name_part and ")" in layer_name_part:
                base_part = layer_name_part.split(" (")[0].strip()
            else:
                base_part = layer_name_part.strip()
                
            # Create the new name with or without the object name
            if object_name:
                new_name = f"{base_part} ({object_name}) - {self.session_cfg['name']}"
            else:
                new_name = f"{base_part} - {self.session_cfg['name']}"
                
            # Update the layer name
            current_layer.name = new_name
