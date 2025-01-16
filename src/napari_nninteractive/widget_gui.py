import importlib.resources
import warnings
from pathlib import Path
from typing import Optional

from napari.layers import Image, Labels
from napari.viewer import Viewer
from nnunetv2.paths import nnUNet_results
from qtpy.QtCore import Qt
from qtpy.QtGui import QKeySequence, QPixmap
from qtpy.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QShortcut,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)

from napari_nninteractive.napari_utils.icon_factory import setup_icon
from napari_nninteractive.napari_utils.widget_factory import (
    setup_button,
    setup_checkbox,
    setup_hswitch,
    setup_layerselection,
    setup_spinbox,
    setup_text,
    setup_tooltipcombobox,
    setup_vswitch,
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
        self._width = 300

        self._viewer = viewer
        self.session_cfg = None

        _main_layout = QVBoxLayout()
        self.setLayout(_main_layout)

        _main_layout.addWidget(self._init_model_selection())  # Model Selection
        _main_layout.addWidget(self._init_image_selection())  # Image Selection
        _main_layout.addWidget(self._init_control_buttons())  # Init and Reset Button
        _main_layout.addWidget(self._init_init_buttons())  # Init and Reset Button

        _main_layout.addWidget(self._init_prompt_selection())  # Prompt Selection
        _main_layout.addWidget(self._init_interaction_selection())  # Interaction Selection
        _main_layout.addWidget(self._init_run_button())  # Run Button
        _main_layout.addWidget(self._init_export_button())  # Run Button

        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum)  # , QSizePolicy.Expanding)
        _main_layout.addItem(spacer)

        _main_layout.addWidget(self._init_acknowledgements())  # Acknowledgements

        self._unlock_session()
        self._viewer.bind_key("Ctrl+Q", self._close, overwrite=True)

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
        self.reset_interaction_button.setEnabled(False)

    def _lock_session(self):
        """Locks the session, disabling model and image selection, and enabling control buttons."""
        self.init_button.setEnabled(False)

        self.reset_button.setEnabled(True)
        self.prompt_button.setEnabled(True)
        self.interaction_button.setEnabled(True)
        self.run_button.setEnabled(True)
        self.run_ckbx.setEnabled(True)
        self.export_button.setEnabled(True)
        self.reset_interaction_button.setEnabled(True)

    # def _reset_session(self):
    #     """Clear Layers, reset session configuration and unlock the session controls."""
    #     self.session_cfg = None
    #     self._clear_layers()
    #     self._unlock_session()

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
        self.model_selection = setup_tooltipcombobox(_layout, _folders, self.on_model_selected)
        self.model_selection.setFixedWidth(self._width)

        self.bg_preprocessing_ckbx = setup_checkbox(
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

        self.image_selection = setup_layerselection(
            _layout, viewer=self._viewer, layer_type=Image, function=self.on_image_selected
        )
        self.image_selection.setFixedWidth(self._width)

        _group_box.setLayout(_layout)
        return _group_box

    def _init_control_buttons(self) -> QGroupBox:
        """Initializes the control buttons (Initialize and Reset)."""
        _group_box = QGroupBox("")
        _layout = QVBoxLayout()

        self.init_button = setup_button(
            _layout, "Initialize", self.on_init, tooltips="Initialize the Model and Image Pair"
        )

        self.propagate_ckbx = setup_checkbox(
            _layout,
            "Propagate predictions",
            True,
            function=self.on_propagate_ckbx,
        )

        self.reset_interaction_button = setup_button(
            _layout,
            "Reset Interactions",
            self.on_reset_interations,
            tooltips="Keep Model and Image Pair, just reset the interactions",
        )
        self.reset_button = setup_button(
            _layout,
            "Next Object",
            self.on_next,
            tooltips="Keep current segmentation and go to the next object - press M",
            shortcut="M",
        )

        setup_icon(self.init_button, "new_labels", theme=self._viewer.theme)
        setup_icon(self.reset_interaction_button, "delete", theme=self._viewer.theme)
        setup_icon(self.reset_button, "step_right", theme=self._viewer.theme)

        _group_box.setLayout(_layout)
        return _group_box

    def _init_init_buttons(self):
        """Initializes the control buttons (Initialize and Reset)."""
        _group_box = QGroupBox("Initialization")
        _layout = QVBoxLayout()

        h_layout = QHBoxLayout()

        self.label_for_init = setup_layerselection(h_layout, viewer=self._viewer, layer_type=Labels)
        _text = setup_text(h_layout, "ID:")
        _text.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.class_for_init = setup_spinbox(h_layout)

        h_layout.setStretch(0, 10)
        h_layout.setStretch(1, 2)
        h_layout.setStretch(2, 3)
        _layout.addLayout(h_layout)

        self.use_init_ckbx = setup_checkbox(
            _layout,
            "Use Mask for Initialization",
            False,
        )

        _group_box.setLayout(_layout)
        return _group_box

    def _init_prompt_selection(self) -> QGroupBox:
        """Initializes the prompt selection as switch with options and shortcuts."""
        _group_box = QGroupBox("Prompt:")
        _layout = QHBoxLayout()

        self.prompt_button = setup_hswitch(
            _layout,
            options=["positive", "negative"],
            function=self.on_prompt_selected,
            default=0,
            shortcut="T",
            tooltips="Press T to switch",
        )

        # def on_key_event(event):
        #     print(event)
        #     # if event.key == Qt.Key_Control:  # Check for Ctrl key
        #     #     if event.type == "key_press":
        #     #         ctrl_button.setChecked(True)  # Set button to pressed
        #     #     elif event.type == "key_release":
        #     #         ctrl_button.setChecked(False)
        #
        # # self._viewer.bind_key('Control', lambda event: on_key_event(event))
        # # key = QShortcut(QKeySequence("Control"), self.prompt_button)
        # # # key.activated.connect(function)
        # # key.event.connect(on_key_event)
        # self._viewer.bind_key("Control", lambda event: on_key_event(event))

        _group_box.setLayout(_layout)
        return _group_box

    def _init_interaction_selection(self) -> QGroupBox:
        """Initializes the interaction selection as switch with options and shortcuts."""
        _group_box = QGroupBox("Interaction:")
        _layout = QVBoxLayout()

        self.interaction_button = setup_vswitch(
            _layout,
            options=["Point", "BBox", "Scribble", "Lasso"],
            function=self.on_interaction_selected,
        )

        setup_icon(self.interaction_button.buttons[0], "new_points", theme=self._viewer.theme)
        setup_icon(self.interaction_button.buttons[1], "rectangle", theme=self._viewer.theme)
        setup_icon(self.interaction_button.buttons[2], "paint", theme=self._viewer.theme)
        setup_icon(self.interaction_button.buttons[3], "polygon_lasso", theme=self._viewer.theme)

        for i, shortcut in enumerate(["P", "B", "S", "L"]):
            key = QShortcut(QKeySequence(shortcut), self.interaction_button.buttons[i])
            key.activated.connect(lambda idx=i: self.interaction_button._on_button_pressed(idx))
            self.interaction_button.buttons[i].setToolTip(f"press {shortcut}")

        _group_box.setLayout(_layout)
        return _group_box

    def _init_run_button(self) -> QGroupBox:
        """Initializes the run button and auto-run checkbox"""
        _group_box = QGroupBox("")
        _layout = QVBoxLayout()

        self.run_button = setup_button(
            _layout, "Run", self.on_run, shortcut="R", tooltips="Press R"
        )
        self.run_ckbx = setup_checkbox(
            _layout,
            "Auto Run",
            True,
            tooltips="Run automatically after each interaction",
        )
        setup_icon(self.run_button, "right_arrow")
        _group_box.setLayout(_layout)
        return _group_box

    def _init_export_button(self) -> QGroupBox:
        """Initializes the export button"""
        _group_box = QGroupBox("")
        _layout = QVBoxLayout()

        self.export_button = setup_button(_layout, "Export", self._export)
        setup_icon(self.export_button, "pop_out", theme=self._viewer.theme)
        _group_box.setLayout(_layout)
        return _group_box

    def _init_acknowledgements(self) -> QGroupBox:
        """Initializes acknowledgements by adding the logos"""
        _group_box = QGroupBox("")

        _group_box.setStyleSheet(
            """
            QGroupBox {
                background-color: white;
            }
        """
        )

        _layout = QVBoxLayout()

        path_resources = importlib.resources.files("napari_nninteractive.resources")
        path_DKFZ = path_resources.joinpath("DKFZ_Logo.png")
        path_HI = path_resources.joinpath("HI_Logo.png")

        pixmap_DKFZ = QPixmap(str(path_DKFZ))
        pixmap_HI = QPixmap(str(path_HI))

        pixmap_DKFZ = pixmap_DKFZ.scaledToWidth(self._width, Qt.SmoothTransformation)
        pixmap_HI = pixmap_HI.scaledToWidth(self._width, Qt.SmoothTransformation)

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

    def on_image_selected(self):
        """When an new image is selected reset layers and session (cfg + gui)"""
        self._clear_layers()
        self._unlock_session()

    def on_model_selected(self):
        """When an new model is selected reset layers and session (cfg + gui)"""
        self._clear_layers()
        self._unlock_session()

    def on_reset_interations(self):
        """Reset only the current interaction"""
        self._clear_layers()

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

    def on_propagate_ckbx(self, *args, **kwargs):
        print("on_propergate_ckbx", *args, **kwargs)

    def _export(self) -> None:
        """Placeholder method for exporting all generated label layers"""
