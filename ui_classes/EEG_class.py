from PyQt5 import QtCore, QtWidgets, QtGui
import pyqtgraph as pg
import numpy as np

"""         # Widget in which EEG data is displayed
self.widgetEEG = PlotWidget(self.centralwidget)
self.widgetEEG.setObjectName("widgetEEG")
self.widgetEEG.setBackground('w')
styles = {'color':'r', 'font-size':'20px'}
#self.widgetEEG.setLabel('left', 'Amplitude (\u03BCV)', **styles)
self.widgetEEG.setLabel('bottom', 'Time (s)', **styles)
self.widgetEEG.getAxis('left').setTickSpacing(1, 0) """

class EEG_class(QtWidgets.QWidget):
    changesMade = QtCore.pyqtSignal()

    def __init__(self, centralWidget):
        super().__init__()
        self.data           = []
        self.display_data   = []
        self.nchans         = []
        self.points         = []
        self.srate          = []
        self.numepo         = []
        self.epolen         = 30
        self.shift          = 25
        self.artefacts      = []
        self.timesby        = 1     
        self.chaninfo       = {}
        self.times          = []
        self.duration_h     = []
        self.extend_l       = 0
        self.extend_r       = 0
        self.configuration  = []

        # Widget for plotting
        self.axes = pg.PlotWidget(centralWidget)
        self.axes.setObjectName("widgetEEG")
        self.axes.setBackground('w')
        #self.axes.getAxis('left').setTickSpacing(1, 0)
        self.axes.getAxis('left').setTicks([]) 
        #self.axes.setLabel('bottom', 'Time (min)', **{'color':'r', 'font-size':'20px'}) 
        self.channelColorPalette    = { 'Black': (0,0,0), 
                                        'Blue': (100, 149, 237), 
                                        'Magenta': (233, 30, 99)}
        
        # Widget for showing current epoch
        self.textfield = QtWidgets.QLabel(self.axes)
        self.textfield.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignTop)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.textfield.setFont(font)
        self.textfield.setObjectName("textfield")
        #self.textfield.setStyleSheet("QLabel { color: red; font-size: 20px; text-align: center; }")

        # Layout
        layout = QtWidgets.QVBoxLayout(self.axes)
        layout.addWidget(self.textfield)


    def add_info(self, configuration):     
        self.configuration  = configuration
        self.srate          = configuration['Sampling_rate_hz']
        self.epolen         = configuration['Epoch_length_s']
        self.extend_l       = configuration['Extension_epoch_left_s']
        self.extend_r       = configuration['Extension_epoch_right_s']
        self.chan_main      = configuration['Channel_index_for_spectogram'] - 1

    def return_extension(self):
        return [self.extend_l, self.extend_r]
    
    def add_chaninfo(self, chaninfo):
        self.chaninfo = chaninfo

    def edit_extension(self, this_epoch, optionbox):
        self.extend_l, self.extend_r = optionbox.get_extensions()
        self.showEEG(this_epoch)

    def update(self):
        self.nchans     = len(self.data)
        self.points     = len(self.data[0])
        self.numepo     = int(np.floor(self.points / self.srate / self.epolen))
        self.duration_h = self.points/self.srate/60/60
        self.data, self.times, self.rest = self.epoch_data(self.data)

    def update2(self):
        self.numepo = int(np.floor(self.points / self.srate / self.epolen))
        self.flatten_then_epoch_again(self.data)

    def flatten_then_epoch_again(self, data):
        import time
        start_time      = time.time()
        flat_data       = np.empty((self.nchans, self.epolen*self.srate*self.numepo))
        flat_data       = np.vstack([channel.flatten() for channel in data])
        flat_data       = np.hstack((flat_data, self.rest))
        elapsed_time    = time.time() - start_time; print(elapsed_time)            
        self.data, self.times, self.rest = self.epoch_data(flat_data)
        elapsed_time    = time.time() - start_time; print(elapsed_time)

    def epoch_data(self, data):
        data_epoched    = np.empty((self.nchans, self.numepo, self.epolen*self.srate));
        times           = np.empty((self.numepo, self.epolen*self.srate))
        epoch_range     = np.arange(self.numepo)
        time_range      = np.linspace(0, self.epolen, self.epolen*self.srate) / self.timesby

        for epoch in range(self.numepo):
            start                       = epoch * self.epolen
            stop                        = (epoch + 1) * self.epolen
            data_epoched[:, epoch, :]   = data[:, start*self.srate:stop*self.srate]
            times[epoch, :]             = time_range + start
            
        data_rest = data[:, stop*self.srate+1:]

        return data_epoched, times, data_rest
            
    def add_extension(self):
        ext_data        = [[[], []] for _ in range(self.nchans)]
        ext_times       = [[], []]
        ndx_l, ndx_r    = int(self.srate*self.extend_l), int(self.srate*self.extend_r)
        for channel_count, epoched_data in enumerate(self.data):
            for epoch_count, epoch in enumerate(epoched_data):
                if epoch_count == 0:
                    ext_data[channel_count][0].append( np.full( ndx_l, np.nan) )
                    ext_data[channel_count][1].append( epoched_data[epoch_count+1][0: ndx_r ] )
                elif epoch_count == self.numepo-1:
                    ext_data[channel_count][0].append( epoched_data[epoch_count-1][0: ndx_l ] )
                    ext_data[channel_count][1].append( np.full( ndx_r, np.nan) )
                else:
                    ext_data[channel_count][0].append( epoched_data[epoch_count-1][0: ndx_l ] )
                    ext_data[channel_count][1].append( epoched_data[epoch_count+1][0: ndx_r ] )
                if channel_count == 0:
                    if epoch_count == 0:             
                        ext_times[0].append( np.linspace(-ndx_l/self.srate, 0, ndx_l) / self.timesby )
                        ext_times[1].append( self.times[epoch_count+1][0: ndx_r ] )
                    elif epoch_count == self.numepo-1:
                        ext_times[0].append( self.times[epoch_count-1][-ndx_l: ] )
                        ext_times[1].append( np.linspace(self.times[-1][-1]+1, self.times[-1][-1]+1+ndx_r/self.srate, ndx_r) / self.timesby )  
                    else:
                        ext_times[0].append( self.times[epoch_count-1][-ndx_l: ] )
                        ext_times[1].append( self.times[epoch_count+1][0: ndx_r ] )
        return ext_data, ext_times


        """ data_epoched = [[] for _ in range(self.nchans)]
            times        = []
            for epoch in range(1, self.numepo+1):
                start      = epoch*epolen - epolen
                stop       = epoch*epolen
                for channel in range(0, self.nchans):
                    data_epoched[channel].append(data[channel][start*self.srate:stop*self.srate])
                times.append( np.linspace(start, stop, epolen*self.srate) / self.timesby) 

            return data_epoched, times """
        
    
    def get_extension(self, this_epoch):
        ext_data        = [[[], []] for _ in range(self.nchans)]
        ext_times       = [[], []]        
        ndx_l, ndx_r    = int(self.srate*self.extend_l), int(self.srate*self.extend_r)
        for channel_count, epoched_data in enumerate(self.data):
            if this_epoch == 1:
                ext_data[channel_count][0] = ( np.full( ndx_l, np.nan) )
                ext_data[channel_count][1] = ( epoched_data[this_epoch][0: ndx_r ] )
            elif this_epoch == self.numepo:
                ext_data[channel_count][0] = ( epoched_data[this_epoch-2][0: ndx_l ] )
                ext_data[channel_count][1] = ( np.full( ndx_r, np.nan) )
            else:
                ext_data[channel_count][0] = ( epoched_data[this_epoch-2][0: ndx_l ] )
                ext_data[channel_count][1] = ( epoched_data[this_epoch][0: ndx_r ] )
            if channel_count == 0:
                if this_epoch == 1:             
                    ext_times[0] = ( np.linspace(-ndx_l/self.srate, -self.times[this_epoch-1][1], ndx_l) / self.timesby )
                    ext_times[1] = ( self.times[this_epoch][1: ndx_r+1 ] )
                elif this_epoch == self.numepo:
                    ext_times[0] = ( self.times[this_epoch-2][-ndx_l-1: -1 ] )
                    ext_times[1] = ( np.linspace(self.times[-1][-1]+1, self.times[-1][-1]+1+ndx_r/self.srate, ndx_r) / self.timesby )  
                else:
                    ext_times[0] = ( self.times[this_epoch-2][-ndx_l-1: -1] )
                    ext_times[1] = ( self.times[this_epoch][1: ndx_r+1 ] )   
        return ext_data, ext_times
     
    def return_active_channels(self):
        active_channels = [chaninfo['Channel_name'] for chaninfo in self.chaninfo if chaninfo['Display_on_screen'] == 1]
        return active_channels

    def showEEG(self, this_epoch):
 
        # Build dotted line
        hard_pen    = pg.mkPen(color=(0, 0, 0), style=QtCore.Qt.DotLine, width=3) 
        dotted_pen  = pg.mkPen(color=(0, 0, 0), style=QtCore.Qt.DotLine)  
        dashed_pen  = pg.mkPen(color=(0, 0, 0, 25), style=QtCore.Qt.DashLine) 
        dotted_line = np.zeros(len(self.times[0]))
        grid_pen    = pg.mkPen(color=(0, 0, 0, 15), style=QtCore.Qt.DashLine) 
        div_pen     = pg.mkPen(color=(100, 149, 237), style=QtCore.Qt.DotLine) 
   
        # Channel counter
        channelCount = 0
        visibleChannels = sum([chaninfo['Display_on_screen'] for chaninfo in self.chaninfo])

        # EEG extensions
        ext_data, ext_times = self.get_extension(this_epoch)        

        # Loop through channels
        self.axes.clear()
        for count, channel in enumerate(self.data):
            pen = pg.mkPen(color=self.channelColorPalette[self.chaninfo[count]['Channel_color']])
            if self.chaninfo[count]['Display_on_screen']:

                # Add extension
                times = np.concatenate([ext_times[0], self.times[this_epoch-1], ext_times[1]])
                data  = np.concatenate([ext_data[count][0], channel[this_epoch-1], ext_data[count][1]])
                
                # Plot EEG
                self.axes.plot(times, data*self.chaninfo[count]['Scaling_factor'] - self.shift*visibleChannels*channelCount, pen=pen, tag='EEG')

                # Set pen style to DotLine
                amplitude_line = pg.InfiniteLine(angle=0, pos=0-self.shift*visibleChannels*channelCount + 37.5*self.chaninfo[count]['Scaling_factor'], pen=dotted_pen); self.axes.addItem(amplitude_line)                 
                amplitude_line = pg.InfiniteLine(angle=0, pos=0-self.shift*visibleChannels*channelCount - 37.5*self.chaninfo[count]['Scaling_factor'], pen=dotted_pen); self.axes.addItem(amplitude_line)                 
                amplitude_line = pg.InfiniteLine(angle=0, pos=0-self.shift*visibleChannels*channelCount + 0*self.chaninfo[count]['Scaling_factor'], pen=dotted_pen); self.axes.addItem(amplitude_line)                 

                #self.axes.plot(times, dotted_line - self.shift*visibleChannels*channelCount + 37.5*self.chaninfo[count]['Scaling_factor'], pen=dotted_pen)
                #self.axes.plot(times, dotted_line - self.shift*visibleChannels*channelCount - 37.5*self.chaninfo[count]['Scaling_factor'], pen=dotted_pen)
                #self.axes.plot(times, dotted_line - self.shift*visibleChannels*channelCount - 0, pen=dashed_pen)
                
                # Add +37.5 muV text on the first channel
                if channelCount == 0 and this_epoch == 1:
                    text1 = pg.TextItem(text="+37.5 \u03BCV", color=(150,150,150), anchor=(0, 0.5))
                    text2 = pg.TextItem(text="-37.5 \u03BCV", color=(150,150,150), anchor=(0, 0.5))
                    text1.setPos(times[0], 0-self.shift*visibleChannels*channelCount + 37.5*self.chaninfo[count]['Scaling_factor'])
                    text2.setPos(times[0], 0-self.shift*visibleChannels*channelCount - 37.5*self.chaninfo[count]['Scaling_factor'])  
                    font = QtGui.QFont(); font.setPixelSize(18)
                    text1.setFont(font)
                    text2.setFont(font)
                    self.axes.addItem(text1)
                    self.axes.addItem(text2)

                # Add channel labels
                text = pg.TextItem(text=self.chaninfo[count]['Channel_name'], color=(150,150,150), anchor=(0, 0.5))
                text.setPos(times[0], 0-self.shift*visibleChannels*channelCount)  
                font = QtGui.QFont(); font.setPixelSize(20)
                text.setFont(font)
                self.axes.addItem(text)

                # Next channel
                channelCount += 1

        # Epoch border
        border_line = pg.InfiniteLine(angle=90, pos=self.times[this_epoch-1][0], pen=hard_pen); self.axes.addItem(border_line)                 
        border_line = pg.InfiniteLine(angle=90, pos=self.times[this_epoch-1][-1], pen=hard_pen); self.axes.addItem(border_line)                 
        #print([value for value in times if times.tolist().count(value) > 1])
        #print(len(times))
        #print(len(set(times)))

        # Adjust axis
        self.axes.setXRange(times[0]/self.timesby, times[-1]/self.timesby, padding=0)    
        self.axes.setYRange(-channelCount*self.shift*(visibleChannels-0.5), self.shift*(visibleChannels-0.5)/1.2, padding=0)  
        if self.timesby == 1:
            ticklabels = [(tick, f'{tick} s') for tick in np.round(np.arange(0, 10000, 5), 1)]
        elif self.timesby == 60:
            ticklabels = [(tick, f'{tick} min') for tick in np.round(np.arange(0.1, 2000, 0.1), 1)]

        self.axes.getAxis('bottom').setTicks([ticklabels]) 
        

        # 1s grid
        y_range = self.axes.getAxis('left').range
        for s in range(self.epolen):
            s = (s + self.epolen*(this_epoch-1)) /self.timesby
            self.axes.plot([s, s], [y_range[0], y_range[1]], pen=grid_pen)

        # grid parts
        for d in range(1, 6+1):
            partlen = self.epolen/6/self.timesby
            s = self.epolen*(this_epoch-1)/self.timesby + partlen*d
            self.axes.plot([s, s], [y_range[0], y_range[1]], pen=div_pen)
        

        # Show artefacts
        self.changesMade.emit()

    def update_text(self, this_epoch, this_stage, uncertain):
        if uncertain == 1:
            self.textfield.setText(f'Epoch {this_epoch}/{self.numepo}: {this_stage} (not sure)')
        else: 
            self.textfield.setText(f'Epoch {this_epoch}/{self.numepo}: {this_stage}') 
        

    def scaleChannels(self, chaninfo, this_epoch):
        self.chaninfo = chaninfo
        self.showEEG(this_epoch)       

