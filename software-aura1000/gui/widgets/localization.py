"""Helpers para actualizar textos visibles sin reconstruir las pantallas."""

from PyQt5.QtWidgets import (
    QAbstractButton,
    QComboBox,
    QDialog,
    QGroupBox,
    QLabel,
    QLineEdit,
    QTabWidget,
    QWidget,
)

import config_gui.strings as strings


_SOURCE_PROPERTY = "i18nSourceText"


def set_localized_text(widget, source_text):
    """Establece un texto fuente en español y presenta su traducción activa."""
    widget.setProperty(f"{_SOURCE_PROPERTY}_text", source_text)
    widget.setText(strings.tr(source_text))


def translate_widget_tree(root):
    """Traduce textos, tooltips y pestañas de un subárbol de widgets."""
    widgets = [root, *root.findChildren(QWidget)]
    for widget in widgets:
        if isinstance(widget, (QLabel, QAbstractButton)):
            _translate_text_property(widget, "text", widget.text, widget.setText)
        if isinstance(widget, QGroupBox):
            _translate_text_property(widget, "title", widget.title, widget.setTitle)
        if isinstance(widget, QLineEdit):
            current = widget.placeholderText()
            if current:
                widget.setPlaceholderText(_translated_source(widget, "placeholder", current))
        tooltip = widget.toolTip()
        if tooltip:
            widget.setToolTip(_translated_source(widget, "toolTip", tooltip))
        accessible_description = widget.accessibleDescription()
        if accessible_description:
            widget.setAccessibleDescription(
                _translated_source(
                    widget,
                    "accessibleDescription",
                    accessible_description,
                )
            )
        if isinstance(widget, QDialog):
            title = widget.windowTitle()
            if title:
                widget.setWindowTitle(_translated_source(widget, "windowTitle", title))
        if isinstance(widget, QTabWidget):
            for index in range(widget.count()):
                widget.setTabText(
                    index,
                    _translated_source(widget, f"tabText{index}", widget.tabText(index)),
                )
        if isinstance(widget, QComboBox):
            for index in range(widget.count()):
                source = _translated_source(
                    widget,
                    f"itemText{index}",
                    widget.itemText(index),
                )
                widget.setItemText(index, source)


def _translate_text_property(widget, property_name, getter, setter):
    current = getter()
    if current:
        setter(_translated_source(widget, property_name, current))


def _translated_source(widget, property_name, current):
    source_key = f"{_SOURCE_PROPERTY}_{property_name}"
    source = widget.property(source_key)
    if source is None:
        source = strings.source_text(current)
        widget.setProperty(source_key, source)
    return strings.tr(source)
