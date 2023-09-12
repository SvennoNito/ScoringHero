from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QTabWidget,
    QDialog,
    QFormLayout,
    QDoubleSpinBox,
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLineEdit,
    QColorDialog,
    QPushButton,
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QIcon, QPixmap, QColor
import copy


class ConfigurationWindow(QDialog):
    changesMade = Signal()

    def __init__(self, config, AnnotationContainer, allow_staging):
        super().__init__()
        self.setWindowTitle("Configuration Window")
        self.resize(500, 400)

        self.layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)

        # Create the pages
        self.channel_page = ChannelConfiguration(config[1])
        self.general_page = GeneralConfiguration(config[0], allow_staging)
        self.events_page = EventConfiguration(AnnotationContainer)

        # Add the pages to the tabs
        self.tabs.addTab(self.general_page, "Configuration")
        self.tabs.addTab(self.channel_page, "Channels")
        self.tabs.addTab(self.events_page, "Events")

    def return_page(self):
        return self.channel_page, self.general_page, self.events_page


class EventConfiguration(QDialog):
    changesMade = Signal()

    def __init__(self, AnnotationContainer, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        self.scale = []
        self.display = []
        self.color = []
        self.label = []

        # Loop through channels
        for count, container in enumerate(AnnotationContainer):
            # QColor
            qcolor = QColor(
                container.facecolor[0],
                container.facecolor[1],
                container.facecolor[2],
                container.facecolor[3],
            )

            # Channe label
            labelbox = QLineEdit(container.label)
            labelbox.setAlignment(Qt.AlignRight)
            # labelbox.setFixedWidth(max(len(container.label) for container in AnnotationContainer)*8 + 10)
            # labelbox.setStyleSheet(f"background: {qcolor.name()};") # {container.facecolor};
            labelbox.textChanged.connect(lambda: self.change_event(AnnotationContainer))

            # Pushbutton
            colorbutton = QPushButton()
            colorbutton.setStyleSheet(
                f"background-color: {qcolor.name()};"
            )  # {container.facecolor};

            # Layout
            row_layout = QHBoxLayout()
            row_layout.addWidget(labelbox)
            row_layout.addWidget(colorbutton)
            form_layout.addRow(row_layout)

            self.label.append(labelbox)

        layout.addLayout(form_layout)

    def change_event(self, AnnotationContainer):
        for counter, container in enumerate(AnnotationContainer):
            container.label = self.label[counter].text()
        self.changesMade.emit()


class GeneralConfiguration(QDialog):
    changesMade = Signal(list)

    def __init__(self, general_config, allow_staging, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        self.width_label = 200
        self.spinboxes = {}

        legend = {
            "Sampling_rate_hz": {"label": "Sampling rate", "unit": " Hz"},
            "Epoch_length_s": {"label": "Epoch length", "unit": " s"},
            "Distance_between_channels_muV": {
                "label": "Vertical distance between channels",
                "unit": " \u03BCV",
            },
            "Channel_for_spectogram": {"label": "Channel for spectogram", "unit": ""},
            "Extension_epoch_s": {"label": "Extent epoch", "unit": " s"},
            "Spectogram_limit_hz": {"label": "Spectogram limits", "unit": " Hz"},
            "Periodogram_limit_hz": {"label": "Periodogram limits", "unit": " Hz"},
        }

        for config_parameter_name, specs in legend.items():
            labelbox = QLabel(specs["label"])
            labelbox.setAlignment(Qt.AlignRight)
            labelbox.setFixedWidth(self.width_label)

            row_layout = QHBoxLayout()
            row_layout.addWidget(labelbox)

            value_in_list = (
                [general_config[config_parameter_name]]
                if not isinstance(general_config[config_parameter_name], list)
                else general_config[config_parameter_name]
            )
            self.spinboxes[config_parameter_name] = []

            for value in value_in_list:
                spinbox = None
                spinbox = QDoubleSpinBox(self)
                spinbox.setMinimum(0)
                spinbox.setMaximum(10000)
                spinbox.setDecimals(0)
                spinbox.setValue(value)
                spinbox.setSuffix(specs["unit"])
                print(config_parameter_name)
                # spinbox.valueChanged.connect(lambda var1=value, var2=config_parameter_name, var3=general_config: self.change_event(var1, var2, var3))
                self.spinboxes[config_parameter_name].append(spinbox)

                if (
                    config_parameter_name in ["Epoch_length_s", "Sampling_rate_hz"]
                    and not allow_staging
                ):
                    spinbox.setDisabled(True)
                    spinbox.setToolTip(
                        "Disabled after scoring epochs.\nChanging this value would cause scored stages to become misaligned with epochs."
                    )

                row_layout.addWidget(spinbox)

            form_layout.addRow(row_layout)

        # Apply button
        apply_button = QPushButton("Apply")
        apply_button.setFixedWidth(100)
        apply_button.clicked.connect(lambda: self.apply_changes(general_config))

        button_layout = QHBoxLayout()
        button_layout.addStretch(1)  # Add stretch to push the button to the right
        button_layout.addWidget(apply_button)

        # Final layout
        layout.addLayout(form_layout)
        layout.addLayout(button_layout)

    def apply_changes(self, general_config):
        old_config = copy.deepcopy(general_config)
        # old_config = general_config.deepcopy()
        for id, spinbox_list in self.spinboxes.items():
            for index, spinbox in enumerate(spinbox_list):
                if isinstance(general_config[id], list):
                    general_config[id][index] = int(spinbox.value())
                else:
                    general_config[id] = int(spinbox.value())
        changed_config_settings = self.config_keys_which_changed(
            old_config, general_config
        )
        self.changesMade.emit(changed_config_settings)

    def config_keys_which_changed(self, config1, config2):
        differing_keys = []
        for key in config1.keys():
            if config1[key] != config2[key]:
                differing_keys.append(key)
        return differing_keys

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
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        self.scale = []
        self.display = []
        self.color = []
        self.label = []
        self.shift = []

        # Loop through channels
        for count, chaninfo in enumerate(channel_config):
            # Channe label
            labelbox = QLineEdit(chaninfo["Channel_name"])
            labelbox.setAlignment(Qt.AlignRight)
            labelbox.setFixedWidth(
                max(len(chaninfo["Channel_name"]) for chaninfo in channel_config) * 8
                + 10
            )
            labelbox.textChanged.connect(lambda: self.change_event(channel_config))

            # Value by which EEG is multiplied
            spinbox = QDoubleSpinBox(self)
            spinbox.setMinimum(0)
            spinbox.setMaximum(10000)
            spinbox.setDecimals(0)
            spinbox.setValue(chaninfo["Scaling_factor"])
            spinbox.valueChanged.connect(lambda: self.change_event(channel_config))

            # Value by which EEG is multiplied
            shiftbox = QDoubleSpinBox(self)
            shiftbox.setMinimum(0)
            shiftbox.setMaximum(10000)
            shiftbox.setDecimals(0)
            shiftbox.setValue(chaninfo["Vertical_shift"])
            shiftbox.valueChanged.connect(lambda: self.change_event(channel_config))

            # Whether channel is displayed or not
            checkbox = QCheckBox(self)
            checkbox.setChecked(chaninfo["Display_on_screen"])
            checkbox.setMaximumWidth(checkbox.sizeHint().width())
            checkbox.clicked.connect(lambda: self.change_event(channel_config))

            # Channel color
            colorbox = QComboBox(self)
            colorbox.addItem("Black")
            colorbox.addItem("Blue")
            colorbox.addItem("Green")
            colorbox.addItem("Magenta")
            colorbox.setCurrentText(chaninfo["Channel_color"])
            colorbox.currentIndexChanged.connect(
                lambda: self.change_event(channel_config)
            )

            # Layout
            row_layout = QHBoxLayout()
            row_layout.addWidget(labelbox)
            row_layout.addWidget(checkbox)
            row_layout.addWidget(spinbox)
            row_layout.addWidget(shiftbox)
            row_layout.addWidget(colorbox)
            form_layout.addRow(row_layout)

            self.label.append(labelbox)
            self.scale.append(spinbox)
            self.display.append(checkbox)
            self.color.append(colorbox)
            self.shift.append(shiftbox)

        layout.addLayout(form_layout)

    def change_event(self, channel_config):
        for counter, chaninfo in enumerate(channel_config):
            chaninfo["Channel_name"] = self.label[counter].text()
            chaninfo["Channel_color"] = self.color[counter].currentText()
            chaninfo["Display_on_screen"] = self.display[counter].isChecked()
            chaninfo["Scaling_factor"] = int(self.scale[counter].value())
            chaninfo["Vertical_shift"] = int(self.shift[counter].value())
        self.changesMade.emit()
