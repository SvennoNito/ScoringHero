from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QTabWidget, QDialog, QFormLayout, QDoubleSpinBox, QCheckBox, QComboBox, QHBoxLayout
from PySide6.QtCore import Signal, Qt

class ConfigurationWindow(QDialog):
    changesMade = Signal()
    def __init__(self, config):
        super().__init__()
        self.setWindowTitle("Configuration Window")  
        self.resize(500, 400)        

        self.layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)

        # Create the pages
        self.channel_page = ChannelConfiguration(config[1])
        self.general_page = GeneralConfiguration(config[0])
        events_page = QLabel("Events Content")

        # Add the pages to the tabs
        self.tabs.addTab(self.channel_page, "Select Channels")
        self.tabs.addTab(self.general_page, "Configuration")
        self.tabs.addTab(events_page, "Events")

    def return_page(self):
        return self.channel_page, self.general_page


class GeneralConfiguration(QDialog):
    changesMade = Signal()

    def __init__(self, general_config, parent=None):
        super().__init__(parent)
        layout              = QVBoxLayout(self)
        form_layout         = QFormLayout()
        self.width_label    = 200
        self.spinboxes      = {}

        legend = {
            'Sampling_rate_hz': {
                'name_pair': None,
                'label': 'Sampling rate',
                'unit': ' Hz'
            },   
            'Epoch_length_s': {
                'name_pair': None,
                'label': 'Epoch length',
                'unit': ' s'
            },     
            'Distance_between_channels_muV': {
                'name_pair': None,
                'label': 'Vertical distance between channels',
                'unit': ' \u03BCV'
            },                                         
            'Channel_index_for_spectogram': {
                'name_pair': None,
                'label': 'Channel for spectogram',
                'unit': ''
            },
            'Extension_epoch_left_s': {
                'name_pair': 'Extension_epoch_right_s',
                'label': 'Extent epoch',
                'unit': ' s'
            },                      
            'Spectogram_lower_limit_hz': {
                'name_pair': 'Spectogram_upper_limit_hz',
                'label': 'Spectogram limits',
                'unit': ' Hz'
            },  
            'Area_power_lower_limit_hz': {
                'name_pair': 'Area_power_upper_limit_hz',
                'label': 'Periodogram limits',
                'unit': ' Hz'
            }                  
        }
   
        for key, value in legend.items():

            labelbox = QLabel(value['label'])
            labelbox.setAlignment(Qt.AlignRight)
            labelbox.setFixedWidth(self.width_label)

            spinbox = QDoubleSpinBox(self)
            spinbox.setMinimum(0)
            spinbox.setMaximum(10000)
            spinbox.setDecimals(0)
            spinbox.setValue(general_config[key]) 
            spinbox.setSuffix(value['unit'])     
            spinbox.valueChanged.connect(lambda: self.change_event(general_config))              
            self.spinboxes[key] = spinbox

            row_layout = QHBoxLayout()
            row_layout.addWidget(labelbox)
            row_layout.addWidget(spinbox)            

            if value['name_pair'] is not None:
                spinbox = QDoubleSpinBox(self)
                spinbox.setMinimum(0)
                spinbox.setMaximum(10000)
                spinbox.setDecimals(0)
                spinbox.setValue(general_config[value['name_pair']]) 
                spinbox.setSuffix(value['unit'])    
                spinbox.valueChanged.connect(lambda: self.change_event(general_config))              
                self.spinboxes[value['name_pair']] = spinbox    
                row_layout.addWidget(spinbox)            

            form_layout.addRow(row_layout) 
                           
        # Final layout
        layout.addLayout(form_layout)    

    def change_event(self, general_config):
        for id, spinbox in self.spinboxes.items():
            general_config[id] = int(spinbox.value())
        self.changesMade.emit()                  


class ChannelConfiguration(QDialog):
    changesMade = Signal()

    def __init__(self, channel_config, parent=None):
        super().__init__(parent)
        layout          = QVBoxLayout(self)
        form_layout     = QFormLayout()
        self.scale      = []
        self.display    = []
        self.color      = []

        # Loop through channels
        for count, chaninfo in enumerate(channel_config):

            # Channe label
            labelbox = QLabel(chaninfo['Channel_name'])
            labelbox.setAlignment(Qt.AlignRight)
            labelbox.setFixedWidth(max(len(chaninfo['Channel_name']) for chaninfo in channel_config)*8)

            # Value by which EEG is multiplied
            spinbox = QDoubleSpinBox(self)
            spinbox.setMinimum(0)
            spinbox.setMaximum(10000)
            spinbox.setDecimals(0)
            spinbox.setValue(chaninfo['Scaling_factor'])
            spinbox.valueChanged.connect(lambda: self.change_event(channel_config))  

            # Whether channel is displayed or not
            checkbox = QCheckBox(self)
            checkbox.setChecked(chaninfo['Display_on_screen']) 
            checkbox.setMaximumWidth(checkbox.sizeHint().width()) 
            checkbox.clicked.connect(lambda: self.change_event(channel_config))

            # Channel color
            colorbox = QComboBox(self)
            colorbox.addItem("Black")
            colorbox.addItem("Blue")
            colorbox.addItem("Magenta")
            colorbox.setCurrentText(chaninfo['Channel_color'])
            colorbox.currentIndexChanged.connect(lambda: self.change_event(channel_config))

            # Layout
            row_layout = QHBoxLayout()
            row_layout.addWidget(labelbox)
            row_layout.addWidget(checkbox)
            row_layout.addWidget(spinbox)
            row_layout.addWidget(colorbox)
            form_layout.addRow(row_layout)

            self.scale.append(spinbox) # append  
            self.display.append(checkbox)
            self.color.append(colorbox)

        layout.addLayout(form_layout)     

    def change_event(self, channel_config):
        for counter, chaninfo in enumerate(channel_config):
            chaninfo['Channel_color']       = self.color[counter].currentText()
            chaninfo['Display_on_screen']   = self.display[counter].isChecked()
            chaninfo['Scaling_factor']      = int(self.scale[counter].value())
        self.changesMade.emit()        