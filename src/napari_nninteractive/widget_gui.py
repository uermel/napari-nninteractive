import warnings
from pathlib import Path
from typing import Optional

from napari.layers.image.image import Image
from napari.viewer import Viewer
from nnunetv2.paths import nnUNet_results
from qtpy.QtWidgets import QGroupBox, QHBoxLayout, QVBoxLayout, QWidget

from napari_nninteractive.widgets.switch_widget import HSwitch, VSwitch
from napari_nninteractive.widgets.widget_helpers import (
    add_button,
    add_checkbox,
    add_layerselection,
    add_tooltipcombobox,
)


class BaseGUI(QWidget):
    """
    A base GUI class for building the Base GUI and connect the components with the correct functions.

    Args:
        viewer (Viewer): The Napari viewer instance to connect with the GUI.
        parent (Optional[QWidget], optional): The parent widget. Defaults to None.
    """

    def __init__(self, viewer: Viewer, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._viewer = viewer
        self.session_cfg = None

        _main_layout = QVBoxLayout()
        self.setLayout(_main_layout)

        _main_layout.addWidget(self._init_model_selection())  # Model Selection
        _main_layout.addWidget(self._init_image_selection())  # Image Selection
        _main_layout.addWidget(self._init_control_buttons())  # Init and Reset Button
        _main_layout.addWidget(self._init_prompt_selection())  # Prompt Selection
        _main_layout.addWidget(self._init_interaction_selection())  # Interaction Selection
        _main_layout.addWidget(self._init_run_button())  # Run Button
        _main_layout.addWidget(self._init_export_button())  # Run Button
        _main_layout.addWidget(self._init_acknowledgements())  # Acknowledgements

        self._unlock_session()
        # self._viewer.bind_key("Ctrl+Enter", self.on_run, overwrite=True)
        self._viewer.bind_key("R", self.on_run, overwrite=True)
        self._viewer.bind_key("Ctrl+Q", self._close, overwrite=True)
        # self._viewer.bind_key("+", self.prompt_button._next, overwrite=True)
        self._viewer.bind_key("T", self.prompt_button._next, overwrite=True)

    # Base Behaviour
    def _close(self):
        """Closes the viewer and quits the application."""
        self._viewer.close()
        quit()

    def _unlock_session(self):
        """Unlocks the session, enabling model and image selection, and initializing controls."""
        self.init_button.setEnabled(True)

        self.reset_button.setEnabled(False)
        self.prompt_button.setEnabled(False)
        self.interaction_button.setEnabled(False)
        self.run_button.setEnabled(False)
        self.run_ckbx.setEnabled(False)
        self.export_button.setEnabled(False)

    def _lock_session(self):
        """Locks the session, disabling model and image selection, and enabling control buttons."""
        self.init_button.setEnabled(False)

        self.reset_button.setEnabled(True)
        self.prompt_button.setEnabled(True)
        self.interaction_button.setEnabled(True)
        self.run_button.setEnabled(True)
        self.run_ckbx.setEnabled(True)
        self.export_button.setEnabled(True)

    def _reset_session(self):
        """Clear Layers, reset session configuration and unlock the session controls."""
        self.session_cfg = None
        self._clear_layers()
        self._unlock_session()

    def _clear_layers(self):
        """Abstract function to clear all needed layers"""

    # Init Methods
    def _init_model_selection(self) -> QGroupBox:
        """Initializes the model selection as a combo box."""
        _group_box = QGroupBox("Model Selection:")
        _layout = QVBoxLayout()

        self.nnUNet_results = nnUNet_results
        self.nnUNet_dataset = "Dataset224_nnInteractive"

        _dir = Path(self.nnUNet_results).joinpath(self.nnUNet_dataset)
        _folders = [str(f.name) for f in _dir.iterdir() if f.is_dir()] if _dir.is_dir() else []
        if _folders == []:
            warnings.warn(
                f"No nnInteractive checkpoints {self.nnUNet_dataset} found in your nnUNet_results folder {self.nnUNet_results}. Add some and restart the plugin",
                UserWarning,
                stacklevel=2,
            )
        self.model_selection = add_tooltipcombobox(_layout, _folders, self._reset_session)
        self.model_selection.setFixedWidth(250)

        self.bg_preprocessing_ckbx = add_checkbox(
            _layout,
            "Background Preprocessing",
            False,
            tooltips="Use background preprocessing for nnInteractive session",
        )

        _group_box.setLayout(_layout)
        return _group_box

    def _init_image_selection(self) -> QGroupBox:
        """Initializes the image selection combo box in a group box."""
        _group_box = QGroupBox("Image Selection:")
        _layout = QVBoxLayout()

        self.image_selection = add_layerselection(
            _layout, viewer=self._viewer, layer_type=Image, function=self._reset_session
        )
        self.image_selection.setFixedWidth(250)

        _group_box.setLayout(_layout)
        return _group_box

    def _init_control_buttons(self) -> QGroupBox:
        """Initializes the control buttons (Initialize and Reset)."""
        _group_box = QGroupBox("")
        _layout = QVBoxLayout()

        self.init_button = add_button(
            _layout, "Initialize", self.on_init, tooltips="Initialize the Model and Image Pair"
        )
        self.reset_button = add_button(
            _layout,
            "Next Object",
            self.on_next,
            tooltips="Keep Model and Image Pair, just reset the interactions",
        )

        _group_box.setLayout(_layout)
        return _group_box

    def _init_prompt_selection(self) -> QGroupBox:
        """Initializes the prompt selection as switch with options and shortcuts."""
        _group_box = QGroupBox("Prompt:")
        _layout = QHBoxLayout()

        options = ["positive", "negative"]
        shortcuts = ["Ctrl+Alt++", "Ctrl+Alt+-"]
        self.prompt_button = HSwitch(
            options, self.on_prompt_selected, default=0, shortcuts=shortcuts, add_tooltip=False
        )
        self.prompt_button.setToolTip("Press T to switch")
        _layout.addWidget(self.prompt_button)

        _group_box.setLayout(_layout)
        return _group_box

    def _init_interaction_selection(self) -> QGroupBox:
        """Initializes the interaction selection as switch with options and shortcuts."""
        _group_box = QGroupBox("Interaction:")
        _layout = QVBoxLayout()

        options = ["Point", "BBox", "Scribble"]
        self.interaction_button = VSwitch(options, self.on_interaction_selected)
        _layout.addWidget(self.interaction_button)

        _group_box.setLayout(_layout)
        return _group_box

    def _init_run_button(self) -> QGroupBox:
        """Initializes the run button and auto-run checkbox"""
        _group_box = QGroupBox("")
        _layout = QVBoxLayout()

        self.run_button = add_button(_layout, "Run", self.on_run, tooltips="Press R")
        self.run_ckbx = add_checkbox(
            _layout,
            "Auto Run",
            True,
            tooltips="Run automatically after each interaction",
        )

        _group_box.setLayout(_layout)
        return _group_box

    def _init_export_button(self) -> QGroupBox:
        """Initializes the export button"""
        _group_box = QGroupBox("")
        _layout = QVBoxLayout()

        self.export_button = add_button(_layout, "Export", self._export)
        # self.browse_button = add_button(_layout, "Browse", self.select_path)

        _group_box.setLayout(_layout)
        return _group_box

    def _init_acknowledgements(self) -> QGroupBox:
        """Initializes acknowledgements by adding the logos"""
        _group_box = QGroupBox("")

        _layout = QVBoxLayout()

        import importlib.resources

        from qtpy.QtCore import Qt
        from qtpy.QtGui import QPixmap
        from qtpy.QtWidgets import QLabel, QSizePolicy, QSpacerItem

        path_resources = importlib.resources.files("napari_nninteractive.resources")
        path_DKFZ = path_resources.joinpath("DKFZ_Logo.png")
        path_HI = path_resources.joinpath("HI_Logo.png")

        pixmap_DKFZ = QPixmap(str(path_DKFZ))
        pixmap_HI = QPixmap(str(path_HI))

        pixmap_DKFZ = pixmap_DKFZ.scaledToWidth(250, Qt.SmoothTransformation)
        pixmap_HI = pixmap_HI.scaledToWidth(250, Qt.SmoothTransformation)

        logo_DKFI = QLabel()
        logo_HI = QLabel()

        logo_DKFI.setPixmap(pixmap_DKFZ)
        logo_HI.setPixmap(pixmap_HI)
        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum)  # , QSizePolicy.Expanding)

        _layout.addWidget(logo_HI)
        _layout.addSpacerItem(spacer)
        _layout.addWidget(logo_DKFI)

        _group_box.setLayout(_layout)
        return _group_box

    # Event Handlers
    def on_init(self, *args, **kwargs) -> None:
        """Initializes the session configuration based on the selected model and image."""
        image_name = self.image_selection.currentText()
        model_name = self.model_selection.currentText()
        if image_name != "" and model_name != "":
            image_layer = self._viewer.layers[image_name]
            self.session_cfg = {
                "name": image_name,
                "model": model_name,
                "ndim": image_layer.ndim,
                "shape": image_layer.data.shape,
                "affine": image_layer.affine,
                "spacing": image_layer.scale,
            }
            self._lock_session()

    def on_next(self) -> None:
        """Resets the interactions."""
        print("_reset_interactions")

    def on_prompt_selected(self, *args, **kwargs) -> None:
        """Placeholder method for when a prompt type is selected"""
        print("on_prompt_selected", self.prompt_button.index, self.prompt_button.value)

    def on_interaction_selected(self, *args, **kwargs) -> None:
        """Placeholder method for when an interaction type is selected."""
        print(
            "on_interaction_selected", self.interaction_button.index, self.interaction_button.value
        )

    def on_run(self, *args, **kwargs) -> None:
        """Placeholder method for run operation"""
        print("on_run")

    def _export(self) -> None:
        """Placeholder method for exporting all generated label layers"""
