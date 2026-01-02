from PySide6.QtCore import Qt
from PySide6.QtWidgets import QSlider, QWidget, QVBoxLayout, QLabel

class HypnogramSlider(QWidget):
    def __init__(self, centralWidget):
        super().__init__()
        self.box = QVBoxLayout()  # Use a QVBoxLayout to stack the label and slider vertically
        self.setLayout(self.box)

        # Create the label for the title
        labelbox = QLabel("SWA")

        # Rotate the label by 90 degrees
        # labelbox.setStyleSheet("transform: rotate(90deg);")
        labelbox.setAlignment(Qt.AlignTop | Qt.AlignCenter)  # Align the label to the top

        # Create the vertical slider
        self.slider = QSlider(Qt.Vertical)
        self.slider.setValue(100)
        self.slider.setMinimum(0)
        self.slider.setMaximum(100)
        self.slider.setFocusPolicy(Qt.NoFocus)
        
        # Disable the slider initially
        self.slider.setEnabled(False)

        # Add the label and slider to the layout
        self.box.addWidget(labelbox)
        self.box.addWidget(self.slider)

        # Set alignment to center
        self.box.setAlignment(Qt.AlignCenter)

        self.slider.sliderMoved.connect(self.transform_value)

    def transform_value(self, value):
        remainder = value % 2
        value_by_two = value - remainder if remainder < 1 else value + (2 - remainder)
        self.slider.setValue(value_by_two)

    # Method to enable the slider after EEG data is imported
    def enable_slider(self):
        self.slider.setEnabled(True)