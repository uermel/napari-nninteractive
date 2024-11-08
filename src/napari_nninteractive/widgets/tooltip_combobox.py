from qtpy.QtWidgets import QComboBox


class ToolTipQComboBox(QComboBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.currentIndexChanged.connect(self.update_tooltip)
        self.update_tooltip()

    def update_tooltip(self):
        # Set the tooltip to the current item’s text
        self.setToolTip(self.currentText())
