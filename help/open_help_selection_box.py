import os
import sys
from PySide6.QtWidgets import QDialog, QLabel, QVBoxLayout
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    # For development (non-bundled), use the current script's directory
    base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    
    # For PyInstaller bundle, use the _MEIPASS attribute
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
        print("sys has MEIPASS attribute")        
    print(f"basepath: {base_path}")

    return os.path.join(base_path, relative_path)

def open_help_selection_box(ui):
    # Construct the path to the image using resource_path
    image_path = resource_path(os.path.join('help', 'images', 'selection_box.png'))
    print(f"image_path: {image_path}")
 
    # Create a dialog
    dialog = QDialog(ui)
    dialog.setWindowTitle("Signal Selection Box Help")
    
    # Create a label and set the image
    label = QLabel(dialog)
    pixmap = QPixmap(image_path)
    
    # Scale the image to a smaller size (e.g., 300x300 pixels)
    scaled_pixmap = pixmap.scaled(800, 800, Qt.KeepAspectRatio)
    label.setPixmap(scaled_pixmap)
    
    # Set layout for the dialog
    layout = QVBoxLayout()
    layout.addWidget(label)
    dialog.setLayout(layout)
    
    # Show the dialog
    dialog.exec_()