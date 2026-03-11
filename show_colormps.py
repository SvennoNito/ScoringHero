import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtWidgets
import math

app = QtWidgets.QApplication([])

maps = pg.colormap.listMaps()
n_cols = 6
n_rows = math.ceil(len(maps) / n_cols)

w = pg.GraphicsLayoutWidget(show=True)

for i, name in enumerate(maps):
    row = i // n_cols
    col = i % n_cols

    cmap = pg.colormap.get(name)

    img = pg.ImageItem(np.linspace(0, 1, 256).reshape(1, -1))
    img.setLookupTable(cmap.getLookupTable(0.0, 1.0, 256))

    p = w.addPlot(row=row, col=col)
    p.addItem(img)
    p.setMenuEnabled(False)
    p.hideAxis('left')
    p.hideAxis('bottom')
    p.setTitle(name)

w.show()
app.exec()