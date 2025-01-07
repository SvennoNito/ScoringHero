from PySide6 import QtCore, QtWidgets, QtGui
from PySide6.QtWidgets import QStyleFactory

def appstyler(app):

    # Set Fusion style (consistent across platforms)
    app.setStyle(QStyleFactory.create("Fusion"))

    # Define a light palette
    light_palette = QtGui.QPalette()
    light_palette.setColor(QtGui.QPalette.Window, QtGui.QColor(255, 255, 255))  # White background
    light_palette.setColor(QtGui.QPalette.WindowText, QtGui.QColor(0, 0, 0))    # Black text
    light_palette.setColor(QtGui.QPalette.Base, QtGui.QColor(240, 240, 240))    # Input fields background
    light_palette.setColor(QtGui.QPalette.AlternateBase, QtGui.QColor(225, 225, 225))
    light_palette.setColor(QtGui.QPalette.ToolTipBase, QtGui.QColor(255, 255, 255))
    light_palette.setColor(QtGui.QPalette.ToolTipText, QtGui.QColor(0, 0, 0))
    light_palette.setColor(QtGui.QPalette.Text, QtGui.QColor(0, 0, 0))
    light_palette.setColor(QtGui.QPalette.Button, QtGui.QColor(240, 240, 240))
    light_palette.setColor(QtGui.QPalette.ButtonText, QtGui.QColor(0, 0, 0))
    light_palette.setColor(QtGui.QPalette.BrightText, QtGui.QColor(255, 0, 0))  # Highlight error text
    light_palette.setColor(QtGui.QPalette.Highlight, QtGui.QColor(0, 120, 215))  # Highlight color (blue)
    light_palette.setColor(QtGui.QPalette.HighlightedText, QtGui.QColor(255, 255, 255))  # Text in highlight
    light_palette.setColor(QtGui.QPalette.Disabled, QtGui.QPalette.ButtonText, QtGui.QColor(160, 160, 160))  # Gray text
    light_palette.setColor(QtGui.QPalette.Disabled, QtGui.QPalette.WindowText, QtGui.QColor(160, 160, 160)) # Gray text for windows
    light_palette.setColor(QtGui.QPalette.Disabled, QtGui.QPalette.Base, QtGui.QColor(240, 240, 240))       # Light background
    light_palette.setColor(QtGui.QPalette.Disabled, QtGui.QPalette.Button, QtGui.QColor(240, 240, 240))     # Light background
    light_palette.setColor(QtGui.QPalette.Disabled, QtGui.QPalette.Text, QtGui.QColor(160, 160, 160))       # Gray text inside text boxes
    light_palette.setColor(QtGui.QPalette.Disabled, QtGui.QPalette.Highlight, QtGui.QColor(200, 200, 200))  # Dimmed highlight
    light_palette.setColor(QtGui.QPalette.Disabled, QtGui.QPalette.HighlightedText, QtGui.QColor(160, 160, 160)) # Dimmed text

    # Apply the light palette
    app.setPalette(light_palette)        