from typing import Callable, List, Optional

from napari.layers import Layer
from napari.viewer import Viewer
from qtpy.QtGui import QKeySequence
from qtpy.QtWidgets import (
    QCheckBox,
    QComboBox,
    QLabel,
    QLayout,
    QPushButton,
    QShortcut,
    QSpinBox,
    QWidget,
)

from napari_nninteractive.napari_utils.widgets.layer_selection_widget import LayerSelectionWidget
from napari_nninteractive.napari_utils.widgets.switch_widget import QHSwitch, QVSwitch
from napari_nninteractive.napari_utils.widgets.tooltip_combobox import ToolTipQComboBox


def _connect_widget(
    layout: QLayout,
    widget: QWidget,
    widget_event: Optional[Callable] = None,
    function: Optional[Callable] = None,
    shortcut: Optional[str] = None,
    tooltips: Optional[str] = None,
) -> QWidget:
    """
    Adds a widget to a layout, connects an optional function to a widget event,
    and sets optional tooltips and shortcut.

    Args:
        layout (QLayout): The layout to add the widget to.
        widget (QWidget): The widget to add and configure.
        widget_event (Optional[Callable], optional): The event of the widget to connect the function to.
        function (Optional[Callable], optional): The function to connect to the widget event.
        shortcut (Optional[str], optional): A keyboard shortcut to trigger the function.
        tooltips (Optional[str], optional): Tooltip text for the widget.

    Returns:
        QWidget: The configured widget added to the layout.
    """
    if function and widget_event:
        widget_event.connect(function)
        if shortcut:
            key = QShortcut(QKeySequence(shortcut), widget)
            key.activated.connect(function)

    if tooltips:
        widget.setToolTip(tooltips)

    layout.addWidget(widget)
    return widget


def _setup_switch(
    _widget: QWidget,
    layout: QLayout,
    options: List[str],
    function: Optional[Callable[[str], None]] = None,
    default: int = None,
    shortcut: Optional[str] = None,
    tooltips: Optional[str] = None,
):
    _widget.addItems(options)

    if default is not None:
        _widget._check(default)

    if shortcut:
        key = QShortcut(QKeySequence(shortcut), _widget)
        key.activated.connect(_widget.next)

    return _connect_widget(
        layout,
        _widget,
        widget_event=_widget.clicked,
        function=function,
        shortcut=None,
        tooltips=tooltips,
    )


def setup_vswitch(
    layout: QLayout,
    options: List[str],
    function: Optional[Callable[[str], None]] = None,
    default: int = None,
    shortcut: Optional[str] = None,
    tooltips: Optional[str] = None,
):

    _widget = QVSwitch()
    return _setup_switch(_widget, layout, options, function, default, shortcut, tooltips)


def setup_hswitch(
    layout: QLayout,
    options: List[str],
    function: Optional[Callable[[str], None]] = None,
    default: int = None,
    shortcut: Optional[str] = None,
    tooltips: Optional[str] = None,
):
    _widget = QHSwitch()
    return _setup_switch(_widget, layout, options, function, default, shortcut, tooltips)


def setup_layerselection(
    layout: QLayout,
    viewer: Optional[Viewer] = None,
    layer_type: Optional[Layer] = None,
    function: Optional[Callable[[str], None]] = None,
    tooltips: Optional[str] = None,
    shortcut: Optional[str] = None,
) -> QWidget:
    """
    Adds a LayerSelectionWidget to a layout with optional configurations, including connecting
    a function, setting a tooltip, and adding a keyboard shortcut.

    Args:
        layout (QLayout): The layout to add the LayerSelectionWidget to.
        viewer (Optional[Viewer], optional): The Napari viewer instance to connect the widget to. Defaults to None.
        layer_type (Optional[Type[Layer]], optional): A specific Napari layer type to filter by in the selection widget.
        function (Optional[Callable[[str], None]], optional): The function to call when the selection changes.
        tooltips (Optional[str], optional): Tooltip text for the widget. Defaults to None.
        shortcut (Optional[str], optional): A keyboard shortcut to trigger the function. Defaults to None.

    Returns:
        QWidget: The configured LayerSelectionWidget added to the layout.
    """
    _widget = LayerSelectionWidget(layer_type=layer_type)
    if viewer:
        _widget.connect(viewer)
    return _connect_widget(
        layout,
        _widget,
        widget_event=_widget.currentTextChanged,
        function=function,
        shortcut=shortcut,
        tooltips=tooltips,
    )


def setup_tooltipcombobox(
    layout: QLayout,
    options: List[str],
    function: Optional[Callable[[str], None]] = None,
    shortcut: Optional[str] = None,
) -> QWidget:
    """
    Adds a QComboBox to a layout with specified options, and optionally connects
    a function, sets a tooltip, and adds a keyboard shortcut.

    Args:
        layout (QLayout): The layout to add the QComboBox to.
        options (List[str]): A list of options to populate the combo box.
        function (Optional[Callable[[str], None]], optional): Function to call when the selection changes.
        tooltips (Optional[str], optional): Tooltip text for the combo box.
        shortcut (Optional[str], optional): Keyboard shortcut to trigger the function.

    Returns:
        QWidget: The configured QComboBox added to the layout.
    """
    _widget = ToolTipQComboBox()
    _widget.addItems(options)

    return _connect_widget(
        layout,
        _widget,
        widget_event=_widget.currentTextChanged,
        function=function,
        shortcut=shortcut,
        tooltips=None,
    )


def setup_combobox(
    layout: QLayout,
    options: List[str],
    function: Optional[Callable[[str], None]] = None,
    tooltips: Optional[str] = None,
    shortcut: Optional[str] = None,
) -> QWidget:
    """
    Adds a QComboBox to a layout with specified options, and optionally connects
    a function, sets a tooltip, and adds a keyboard shortcut.

    Args:
        layout (QLayout): The layout to add the QComboBox to.
        options (List[str]): A list of options to populate the combo box.
        function (Optional[Callable[[str], None]], optional): Function to call when the selection changes.
        tooltips (Optional[str], optional): Tooltip text for the combo box.
        shortcut (Optional[str], optional): Keyboard shortcut to trigger the function.

    Returns:
        QWidget: The configured QComboBox added to the layout.
    """
    _widget = QComboBox()
    _widget.addItems(options)

    return _connect_widget(
        layout,
        _widget,
        widget_event=_widget.currentTextChanged,
        function=function,
        shortcut=shortcut,
        tooltips=tooltips,
    )


def setup_text(layout: QLayout, text: str, verbose: bool = False, tooltips: str = None) -> QLayout:
    """
    Adds a QLabel with the specified text to a layout, optionally printing the text
    and setting a tooltip.

    Args:
        layout (QLayout): The layout to add the QLabel to.
        text (str): The text to display in the QLabel.
        verbose (bool, optional): If True, prints the text to the console. Defaults to True.
        tooltips (Optional[str], optional): Tooltip text for the QLabel. Defaults to None.

    Returns:
        QLayout: The layout with the QLabel added to it.
    """
    _widget = QLabel(text)
    if verbose:
        print(text)

    return _connect_widget(
        layout,
        _widget,
        widget_event=None,
        function=None,
        shortcut=None,
        tooltips=tooltips,
    )


def setup_button(
    layout: QLayout,
    text: str,
    function: Callable[[], None],
    tooltips: Optional[str] = None,
    shortcut: Optional[str] = None,
) -> QLayout:
    """
    Adds a QPushButton to a layout, connects it to a function, and optionally sets a tooltip and a shortcut.

    Args:
        layout (QLayout): The layout to add the QPushButton to.
        text (str): The text to display on the button.
        function (Callable[[], None]): The function to call when the button is clicked.
        tooltips (Optional[str], optional): Tooltip text for the button. Defaults to None.
        shortcut (Optional[str], optional): Keyboard shortcut to trigger the button click. Defaults to None.

    Returns:
        QLayout: The layout with the QPushButton added to it.
    """
    _widget = QPushButton(text)

    return _connect_widget(
        layout,
        _widget,
        widget_event=_widget.clicked,
        function=function,
        shortcut=shortcut,
        tooltips=tooltips,
    )


def setup_spinbox(
    layout: QLayout,
    min_val=1,
    max_val=255,
    function: Optional[Callable[[int], None]] = None,
    tooltips: Optional[str] = None,
    shortcut: Optional[str] = None,
) -> QWidget:
    _widget = QSpinBox()
    _widget.setRange(min_val, max_val)

    return _connect_widget(
        layout,
        _widget,
        widget_event=_widget.valueChanged,
        function=function,
        shortcut=shortcut,
        tooltips=tooltips,
    )


def setup_checkbox(
    layout: QLayout,
    text: str,
    checked: bool,
    function: Optional[Callable[[int], None]] = None,
    tooltips: Optional[str] = None,
    shortcut: Optional[str] = None,
) -> QWidget:
    """
    Adds a QCheckBox to a layout, optionally connects it to a function, and sets its initial state,
    tooltip, and shortcut.

    Args:
        layout (QLayout): The layout to add the QCheckBox to.
        text (str): The label text for the checkbox.
        checked (bool): The initial checked state of the checkbox.
        function (Optional[Callable[[int], None]], optional): The function to call when the checkbox state changes. Receives the state as an integer.
        tooltips (Optional[str], optional): Tooltip text for the checkbox. Defaults to None.
        shortcut (Optional[str], optional): Keyboard shortcut to toggle the checkbox. Defaults to None.

    Returns:
        QWidget: The configured QCheckBox added to the layout.
    """
    _widget = QCheckBox(text)
    _widget.setChecked(checked)

    return _connect_widget(
        layout,
        _widget,
        widget_event=_widget.stateChanged,
        function=function,
        shortcut=shortcut,
        tooltips=tooltips,
    )
