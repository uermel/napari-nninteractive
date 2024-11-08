from qtpy.QtGui import QKeySequence
from qtpy.QtWidgets import QHBoxLayout, QPushButton, QShortcut, QVBoxLayout, QWidget


class _Switch(QWidget):
    """
    A widget that provides a toggleable switch with multiple button options.

    Args:
        layout (QLayout): The layout to arrange the buttons in.
        options (List[str]): List of option names for each button.
        function (Callable[[], None]): Function to call when a button is pressed.
        default (Optional[int], optional): Index of the default selected option. Defaults to None.
        shortcuts (Optional[List[str]], optional): List of keyboard shortcuts for each option. Defaults to None.
    """

    def __init__(self, layout, options, function, default=None, shortcuts=None):
        super().__init__()
        self.function = function
        self.options = options
        self.value = None
        self.index = None

        self.buttons = []
        for i, opt in enumerate(options):
            _btn = QPushButton(opt)
            _btn.clicked.connect(lambda _, idx=i: self._on_button_pressed(idx))
            layout.addWidget(_btn)
            self.buttons.append(_btn)

        if shortcuts is not None:
            for i, shortcut in enumerate(shortcuts):
                key = QShortcut(QKeySequence(shortcut), self)
                key.activated.connect(lambda idx=i: self._on_button_pressed(idx))
                self.buttons[i].setToolTip(shortcut)

        self._check(default)
        self.setLayout(layout)

    def _on_button_pressed(self, idx: int):
        """
        Handles the button press event, updating the selected option.

        Args:
            idx (int): Index of the button pressed.
        """
        self._uncheck()
        self._check(idx)
        self.function()

    def _uncheck(self):
        """Unchecks all buttons and resets the selection state."""
        self.value = None
        self.index = None
        for btn in self.buttons:
            btn.setChecked(False)
            btn.setStyleSheet("")

    def _check(self, idx: int):
        """
        Checks the button at the specified index and updates the selection state.

        Args:
            idx (int): Index of the button to check.
        """
        if idx is not None and 0 <= idx < len(self.buttons):
            self.value = self.options[idx]
            self.index = idx
            self.buttons[idx].setChecked(True)
            self.buttons[idx].setStyleSheet("QPushButton {background-color: rgb(0,100, 167);}")


class HSwitch(_Switch):
    """
    A horizontal switch widget with multiple button options.

    Args:
        options (List[str]): List of option names for each button.
        function (Callable[[], None]): Function to call when a button is pressed.
        default (Optional[int], optional): Index of the default selected option. Defaults to None.
        shortcuts (Optional[List[str]], optional): List of keyboard shortcuts for each option. Defaults to None.
    """

    def __init__(self, options, function, default=None, shortcuts=None):
        _layout = QHBoxLayout()
        super().__init__(_layout, options, function, default, shortcuts)


class VSwitch(_Switch):
    """
    A vertical switch widget with multiple button options.

    Args:
        options (List[str]): List of option names for each button.
        function (Callable[[], None]): Function to call when a button is pressed.
        default (Optional[int], optional): Index of the default selected option. Defaults to None.
        shortcuts (Optional[List[str]], optional): List of keyboard shortcuts for each option. Defaults to None.
    """

    def __init__(self, options, function, default=None, shortcuts=None):
        _layout = QVBoxLayout()
        super().__init__(_layout, options, function, default, shortcuts)
