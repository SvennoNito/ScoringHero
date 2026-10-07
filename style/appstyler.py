from PySide6 import QtGui
from PySide6.QtWidgets import QStyleFactory

def appstyler(app):

    # Set Fusion style (consistent across platforms)
    app.setStyle(QStyleFactory.create("Fusion"))

    # Define a light palette
    light_palette = QtGui.QPalette()
    c = QtGui.QColor
    light_palette.setColor(QtGui.QPalette.Window, c("#ffffff"))
    light_palette.setColor(QtGui.QPalette.WindowText, c("#1f2933"))
    light_palette.setColor(QtGui.QPalette.Base, c("#ffffff"))
    light_palette.setColor(QtGui.QPalette.AlternateBase, c("#f8f9fb"))
    light_palette.setColor(QtGui.QPalette.ToolTipBase, c("#1f2933"))
    light_palette.setColor(QtGui.QPalette.ToolTipText, c("#ffffff"))
    light_palette.setColor(QtGui.QPalette.Text, c("#1f2933"))
    light_palette.setColor(QtGui.QPalette.Button, c("#ffffff"))
    light_palette.setColor(QtGui.QPalette.ButtonText, c("#1f2933"))
    light_palette.setColor(QtGui.QPalette.BrightText, c("#c0392b"))
    light_palette.setColor(QtGui.QPalette.Highlight, c("#2f6fed"))
    light_palette.setColor(QtGui.QPalette.HighlightedText, c("#ffffff"))
    for role in (QtGui.QPalette.ButtonText, QtGui.QPalette.WindowText, QtGui.QPalette.Text, QtGui.QPalette.HighlightedText):
        light_palette.setColor(QtGui.QPalette.Disabled, role, c("#a3aab5"))
    light_palette.setColor(QtGui.QPalette.Disabled, QtGui.QPalette.Base, c("#f4f6f9"))
    light_palette.setColor(QtGui.QPalette.Disabled, QtGui.QPalette.Button, c("#f4f6f9"))
    light_palette.setColor(QtGui.QPalette.Disabled, QtGui.QPalette.Highlight, c("#d3d8e0"))

    # Apply the light palette
    app.setPalette(light_palette)        