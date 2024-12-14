from PySide6.QtCore import Qt
from PySide6.QtWidgets import QSlider, QWidget, QVBoxLayout, QLabel

class SpectogramSlider(QWidget):
    def __init__(self, centralWidget):
        super().__init__()
        
        # Create a vertical layout to stack the title and slider
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Create the label for the title
        labelbox = QLabel("MAX")
        labelbox.setAlignment(Qt.AlignHCenter)  # Align the title to the center horizontally
        # Rotate the label by 90 degrees
        labelbox.setStyleSheet("transform: rotate(90deg);")
        labelbox.setAlignment(Qt.AlignTop | Qt.AlignCenter)  # Align the label to the top

        # Create the vertical slider
        self.slider = QSlider(Qt.Vertical)
        self.slider.setValue(100)
        self.slider.setMinimum(75)
        self.slider.setFocusPolicy(Qt.NoFocus)

        # Disable the slider initially
        self.slider.setEnabled(False)        

        # Add the title and slider to the layout
        layout.addWidget(labelbox)
        layout.addWidget(self.slider)

        # Optionally, you can adjust the alignment of the layout
        layout.setAlignment(Qt.AlignCenter)

    # Method to enable the slider after EEG data is imported
    def enable_slider(self):
        self.slider.setEnabled(True)        
