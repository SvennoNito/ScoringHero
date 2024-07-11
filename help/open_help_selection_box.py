import os
from PySide6.QtWidgets import QDialog, QLabel, QVBoxLayout
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt


def open_help_selection_box(ui):
    # Construct the path to the image
    image_path = os.path.join(os.path.dirname(__file__), 'images', 'selection_box.png')
    
    # Create a dialog
    dialog = QDialog(ui)
    dialog.setWindowTitle("Signal Selection Box Help")
    
    # Create a label and set the image
    label = QLabel(dialog)
    pixmap = QPixmap(image_path)
    
    # Scale the image to a smaller size (e.g., 300x300 pixels)
    scaled_pixmap = pixmap.scaled(800, 800, aspectMode=Qt.KeepAspectRatio)
    label.setPixmap(scaled_pixmap)
    
    # Set layout for the dialog
    layout = QVBoxLayout()
    layout.addWidget(label)
    dialog.setLayout(layout)
    
    # Show the dialog
    dialog.exec_()