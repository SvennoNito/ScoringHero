from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import *

class annotationBox(QtWidgets.QDialog):
    changesMade = QtCore.pyqtSignal()

    def __init__(self, annotation_containers, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        self.countbox = []
        self.labelbox = []
        self.colorbox = []    
        self.colorpick = [] 

        # Loop through channels
        for count, container in enumerate(annotation_containers):

            # Channe label
            countbox = QLabel(f'#{count}')
            countbox.setAlignment(QtCore.Qt.AlignRight)
            countbox.setFixedWidth(len('#1')*8)            

            # Channe label
            labelbox = QLineEdit(f'{container.label}')
            labelbox.setAlignment(QtCore.Qt.AlignRight)
            labelbox.setFixedWidth(max(len(container.label) for container in annotation_containers)*16)

            ## Color in RGB
            #colorbox = QLineEdit(f'{container.facecolor}')
            #colorbox.setAlignment(QtCore.Qt.AlignRight)
            #colorbox.setFixedWidth(max(len(str(container.facecolor)) for container in annotation_containers)*8)
            #colorbox.setStyleSheet("background-color: {}".format(container.facecolor))
            
            # Set the background color
            palette = labelbox.palette()
            palette.setColor(QtGui.QPalette.Base, QtGui.QColor(*container.facecolor))
            labelbox.setPalette(palette)           

            # Annotation color
            colorpick = QPushButton("Change color")
            colorpick.clicked.connect(self.pick_color)            

            # Layout
            row_layout = QHBoxLayout()
            row_layout.addWidget(countbox)
            row_layout.addWidget(labelbox)
            #row_layout.addWidget(colorpick)
            form_layout.addRow(row_layout)

            # Append  
            self.countbox.append(countbox)
            self.labelbox.append(labelbox)
            self.colorpick.append(colorpick)

        layout.addLayout(form_layout)

    def pick_color(self):
        color = QColorDialog.getColor()
        rgb   = (color.red(), color.green(), color.blue())
        index = self.colorpick.index(self.sender())

        # Set the background color
        palette = self.labelbox[index].palette()
        palette.setColor(QtGui.QPalette.Base, QtGui.QColor(*rgb))
        self.labelbox[index].setPalette(palette) 

        self.changesMade.emit()
