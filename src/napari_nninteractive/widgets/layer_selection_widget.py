from napari.layers.base._base_constants import ActionType
from napari.viewer import Viewer
from qtpy.QtWidgets import QComboBox


class LayerSelectionWidget(QComboBox):
    """
    A QComboBox widget that dynamically updates with the names of layers in a Napari viewer.

    Args:
        parent (Optional[QWidget]): The parent widget.
        layer_type (Optional[Type[Layer]]): A specific Napari layer type to filter by (e.g., Image, Labels).
    """

    def __init__(self, parent=None, layer_type=None):
        super().__init__(parent)
        self.layer_type = layer_type
        self.value = self.currentText()
        self.currentIndexChanged.connect(self.update_tooltip)
        self.update_tooltip()

    def _update(self, event):
        """
        Updates the combo box with the names of layers in the viewer that match the specified layer type.

        Args:
            event: The Napari event triggered by a layer being added or removed.
        """

        layer = event.value
        if isinstance(layer, self.layer_type):
            if event.type == "removed":
                item_index = self.findText(layer.name)
                if item_index != -1:
                    self.removeItem(item_index)
            elif event.type == "inserted":
                self.addItem(layer.name)

    def connect(self, viewer: Viewer):
        """
        Connects the widget to the Napari viewer's layer events to update the combo box
        when layers are added or removed.

        Args:
            viewer (Viewer): The Napari viewer instance to connect to.
        """
        viewer.layers.events.inserted.connect(self._update)
        viewer.layers.events.removed.connect(self._update)

        # Initial population of combo box with layer names
        layer_names = [
            layer.name
            for layer in viewer.layers
            if self.layer_type is None or isinstance(layer, self.layer_type)
        ]
        self.addItems(layer_names)

    def update_tooltip(self):
        # Set the tooltip to the current item’s text
        self.setToolTip(self.currentText())
