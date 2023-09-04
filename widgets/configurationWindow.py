from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QTabWidget, QDialog, QFormLayout, QDoubleSpinBox, QCheckBox, QComboBox, QHBoxLayout, QLineEdit
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
    changesMade = Signal(str)

    def __init__(self, general_config, parent=None):
        super().__init__(parent)
        layout              = QVBoxLayout(self)
        form_layout         = QFormLayout()
        self.width_label    = 200
        self.spinboxes      = {}

        legend = {
            'Sampling_rate_hz': {
                'label': 'Sampling rate',
                'unit': ' Hz'
            },   
            'Epoch_length_s': {
                'label': 'Epoch length',
                'unit': ' s'
            },     
            'Distance_between_channels_muV': {
                'label': 'Vertical distance between channels',
                'unit': ' \u03BCV'
            },                                         
            'Channel_for_spectogram': {
                'label': 'Channel for spectogram',
                'unit': ' (considered after restart)'
            },
            'Extension_epoch_s': {
                'label': 'Extent epoch',
                'unit': ' s'
            },                      
            'Spectogram_limit_hz': {
                'label': 'Spectogram limits',
                'unit': ' Hz'
            },  
            'Periodogram_limit_hz': {
                'label': 'Periodogram limits',
                'unit': ' Hz'
            }                  
        }
   
        for config_parameter_name, specs in legend.items():

            labelbox = QLabel(specs['label'])
            labelbox.setAlignment(Qt.AlignRight)
            labelbox.setFixedWidth(self.width_label)

            row_layout = QHBoxLayout()
            row_layout.addWidget(labelbox)    
 
            value_in_list       = [general_config[config_parameter_name]] if not isinstance(general_config[config_parameter_name], list) else general_config[config_parameter_name]
            self.spinboxes[config_parameter_name] = []

            for value in value_in_list:
                spinbox = None
                spinbox = QDoubleSpinBox(self)
                spinbox.setMinimum(0)
                spinbox.setMaximum(10000)
                spinbox.setDecimals(0)
                spinbox.setValue(value) 
                spinbox.setSuffix(specs['unit'])     
                print(config_parameter_name)
                spinbox.valueChanged.connect(lambda var1=value, var2=config_parameter_name, var3=general_config: self.change_event(var1, var2, var3))              
                self.spinboxes[config_parameter_name].append(spinbox)
                
                row_layout.addWidget(spinbox)                      

            form_layout.addRow(row_layout) 
                           
        # Final layout
        layout.addLayout(form_layout)    

    def change_event(self, value, config_parameter_name, general_config):
        for id, spinbox_list in self.spinboxes.items():
            for index, spinbox in enumerate(spinbox_list):
                if isinstance(general_config[id], list):
                    general_config[id][index] = int(spinbox.value())
                else:
                    general_config[id] = int(spinbox.value())                    
        self.changesMade.emit(config_parameter_name)                  


class ChannelConfiguration(QDialog):
    changesMade = Signal()

    def __init__(self, channel_config, parent=None):
        super().__init__(parent)
        layout          = QVBoxLayout(self)
        form_layout     = QFormLayout()
        self.scale      = []
        self.display    = []
        self.color      = []
        self.label      = []

        # Loop through channels
        for count, chaninfo in enumerate(channel_config):

            # Channe label
            labelbox = QLineEdit(chaninfo['Channel_name'])
            labelbox.setAlignment(Qt.AlignRight)
            labelbox.setFixedWidth(max(len(chaninfo['Channel_name']) for chaninfo in channel_config)*8 + 10)
            labelbox.textChanged.connect(lambda: self.change_event(channel_config))  

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

            self.label.append(labelbox) 
            self.scale.append(spinbox)
            self.display.append(checkbox)
            self.color.append(colorbox)

        layout.addLayout(form_layout)     

    def change_event(self, channel_config):
        for counter, chaninfo in enumerate(channel_config):
            chaninfo['Channel_name']       = self.label[counter].text()
            chaninfo['Channel_color']      = self.color[counter].currentText()
            chaninfo['Display_on_screen']  = self.display[counter].isChecked()
            chaninfo['Scaling_factor']     = int(self.scale[counter].value())
        self.changesMade.emit()        