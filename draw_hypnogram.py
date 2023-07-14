def draw_hypnogram(MainWindow, grid=False, ascolor=False,
                colors={1: '#8bbf56', 0: '#56bf8b', -1: '#aabcce',
                                   -2: '#405c79', -3: '#0b1c2c', -4: '#bf5656'}):
    """Draw hypnogram.

    Parameters
    ----------
    data : array_like
        Hypnogram vector
    grid : bool | False
        Plot X and Y grid.
    ascolor : bool | False
        Plot in color
    color : dict | {}
        Color for each sleep stage. Default is : {-1: '#8bbf56', 0: '#56bf8b',
        1: '#aabcce', 2: '#405c79', 3: '#0b1c2c', 4: '#bf5656'}
    """
    import matplotlib.pyplot as plt
    import datetime
    import numpy as np
    import pyqtgraph as pg

    # Internal copy :
    hypno = MainWindow.sleepStages.copy()
    hypno = [val[1] for key, val in hypno.items()]
    hypno = np.array(hypno)
    
    # Start plotting
    lhyp = len(hypno) / 60
    if lhyp < 60:
        xticks = np.arange(0, len(hypno), 10 * 60)
    elif lhyp < 180 and lhyp > 60:
        xticks = np.arange(0, len(hypno), 30 * 60)
    else:
        xticks = np.arange(0, len(hypno), 60 * 60)

    # Time vector
    xt = np.arange(1, len(hypno)+1)
    xt = xt*MainWindow.epochLen_sec/3600
    xt = np.repeat(xt, 2)

    for stage, color in colors.items():
        data    = np.zeros(len(hypno))
        data[:] = np.nan
        data[hypno == stage] = stage
        data    = np.concatenate(np.column_stack((data, data-1)))
        pen     = pg.mkPen(color=color, width=4)
        MainWindow.hypnogram.plot(xt, data, pen=pen)

    # red line
    pen  = pg.mkPen(color='#FA8072', width=1)
    xt   = np.repeat(MainWindow.epochDisplay*MainWindow.epochLen_sec/3600, 2)
    data = [-4, 1]
    MainWindow.hypnogram.plot(xt, data, pen=pen)

    # Make pretty
    MainWindow.hypnogram.setYRange(-4, 1, padding=0) 
    ay = MainWindow.hypnogram.getAxis('left')    
    ticks  = [.5, -.5, -1.5, -2.5, -3.5]
    labels = ['W', 'REM', 'N1', 'N2', 'N3']
    ay.setTicks([[(ticks[count], label) for count, label in enumerate(labels)]])                                    
            