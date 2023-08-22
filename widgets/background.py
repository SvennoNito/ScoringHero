from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont
import pyqtgraph as pg
import numpy as np

class BackgroundWidget(QWidget):
    changesMade = Signal()

    def __init__(self, centralWidget):
        super().__init__()

        # Plot axes
        self.axes = pg.PlotWidget(centralWidget)
        self.axes.setObjectName("BackgroundWidget")
        self.axes.setBackground('w')        
        self.axes.getAxis('left').setTicks([]) 
        self.axes.getAxis('bottom').setTicks([]) 

        # Text showing current epoch
        self.textfield = QLabel(self.axes)
        self.textfield.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        font = QFont()
        font.setBold(True)
        font.Weight(75)
        self.textfield.setFont(font)
        self.textfield.setObjectName("textfield")
        self.textfield.setText("Test")
        #self.textfield.setStyleSheet("QLabel { color: red; font-size: 20px; text-align: center; }")

        # Layout
        layout = QVBoxLayout(self.axes)
        layout.addWidget(self.textfield)   

        # Pens
        self.pen_grid = pg.mkPen(color=(25, 25, 25, 15), style=Qt.DashLine) 
        self.pen_border = pg.mkPen(color=(0, 0, 0), style=Qt.DotLine, width=3) 

    def draw_background(self, eeg_data, times, this_epoch):

        # Invisible line
        self.axes.plot(times[0][0], times[0][0], pen=pg.mkPen(color=(0,0,0,0)))

        # Vertical line grid (4 seconds)
        times_pieces        = np.array_split(times[0][0], 5)
        grid_start_times    = [piece[0] for piece in times_pieces[1:]]
        for start_time in grid_start_times:    
            grid_line = pg.InfiniteLine(pos=start_time, angle=90, pen=self.pen_grid)
            self.axes.addItem(grid_line)  

        # Epoch border
        border_line = pg.InfiniteLine(angle=90, pos=times[0][0][0], pen=self.pen_border); self.axes.addItem(border_line)                 
        border_line = pg.InfiniteLine(angle=90, pos=times[1][0][0], pen=self.pen_border); self.axes.addItem(border_line)                 

        """ # 1s grid
        y_range = self.axes.getAxis('left').range
        for s in range(self.epolen):
            s = (s + self.epolen*(this_epoch-1)) /self.timesby
            self.axes.plot([s, s], [y_range[0], y_range[1]], pen=self.pen_grid)

        # grid parts
        for d in range(1, 6+1):
            partlen = self.epolen/6/self.timesby
            s = self.epolen*(this_epoch-1)/self.timesby + partlen*d
            self.axes.plot( [s, s], [y_range[0], y_range[1]], pen=div_pen) """