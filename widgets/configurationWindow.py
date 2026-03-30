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
    QScrollArea,
    QGridLayout,
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QColor, QFont
import copy


class ConfigurationWindow(QDialog):
    changesMade = Signal()

    def __init__(self, config, AnnotationContainer, allow_staging, channel_labels=None):
        super().__init__()
        self.setWindowTitle("Configuration Window")
        self.resize(575, 460)

        self.layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)

        # Create the pages
        self.channel_page = ChannelConfiguration(config[1], config[0])
        self.general_page = GeneralConfiguration(config[0], allow_staging, channel_labels or [])
        self.events_page = EventConfiguration(AnnotationContainer)
        self.spectrogram_page = SpectrogramConfiguration(config[0], channel_labels or [])
        self.wavelet_page = WaveletConfiguration(config[0], channel_labels or [])
        self.periodogram_page = PeriodogramConfiguration(config[0], channel_labels or [])
        # self.layout_page = PanelLayout(config[0])

        # Add the pages to the tabs
        self.tabs.addTab(self.general_page, "Configuration")
        self.tabs.addTab(self.channel_page, "Channels")
        self.tabs.addTab(self.events_page, "Events")
        self.tabs.addTab(self.spectrogram_page, "Spectrogram")
        self.tabs.addTab(self.periodogram_page, "Periodogram")
        self.tabs.addTab(self.wavelet_page, "Wavelet")
        # self.tabs.addTab(self.events_page, "Layout")

    def return_page(self):
        return self.channel_page, self.general_page, self.events_page, self.wavelet_page, self.spectrogram_page, self.periodogram_page
    

""" class PanelLayout(QDialog):
    changesMade = Signal(list)

   def __init__(self, general_config, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        self.width_label = 200
        self.spinboxes = {} """   


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

    def __init__(self, general_config, allow_staging, channel_labels=None, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        self.width_label = 200
        self.spinboxes = {}
        self.optionboxes = {}
        self.checkboxes = {}

        legend = {
            "Sampling_rate_hz": {"label": "Sampling rate", "unit": " Hz"},
            "Epoch_length_s": {"label": "Epoch length", "unit": " s"},
            "Distance_between_channels_muV": {
                "label": "Vertical distance between channels",
                "unit": " \u03BCV",
            },
            "Reference_amplitude_line_muV": {"label": "Reference amplitude line", "unit": " \u03BCV"},
            "Extension_epoch_s": {"label": "Extent epoch", "unit": " s"},
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
                # Use decimals for TF frequency limits, integers for others
                if config_parameter_name == "Wavelet_frequency_limits_hz":
                    spinbox.setDecimals(2)
                else:
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

        ### Configuration paramters that have options
        box_options = {
            "EEG_panel_time_unit": {"label": "EEG time unit in", "options": ["Seconds", "Minutes", "Hours"]},
        }

        for config_parameter_name, specs in box_options.items():
            self.optionboxes[config_parameter_name] = []

            labelbox = QLabel(specs["label"])
            labelbox.setAlignment(Qt.AlignRight)
            labelbox.setFixedWidth(self.width_label)

            row_layout = QHBoxLayout()
            row_layout.addWidget(labelbox)

            optionbox = None
            optionbox = QComboBox(self)

            for option in specs["options"]:
                optionbox.addItem(option)
            optionbox.setCurrentText(general_config[config_parameter_name])
            self.optionboxes[config_parameter_name].append(optionbox)

            row_layout.addWidget(optionbox)
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
                # Use float for TF frequency limits, int for others
                value = spinbox.value()
                if id == "Wavelet_frequency_limits_hz":
                    value = float(value)
                else:
                    value = int(value)

                if isinstance(general_config[id], list):
                    general_config[id][index] = value
                else:
                    general_config[id] = value

        for id, optionbox_list in self.optionboxes.items():
              for index, optionbox in enumerate(optionbox_list):
                  general_config[id] = optionbox.currentText()

        for id, checkbox in self.checkboxes.items():
            general_config[id] = checkbox.isChecked()

        changed_config_settings = self.config_keys_which_changed(old_config, general_config)
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


class SpectrogramConfiguration(QDialog):
    changesMade = Signal(list)

    def __init__(self, general_config, channel_labels=None, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.width_label = 200
        self.spinboxes = {}
        self.optionboxes = {}

        # Description
        description = QLabel(
            "\u24d8 " \
            "Pwelch is computed for every epoch and displayed in the spectrogram panel " \
            "at the top left. Configure spectrogram parameters here." \
        )
        description.setWordWrap(True)
        layout.addWidget(description)

        form_layout = QFormLayout()

        # Channel selector (label dropdown)
        if channel_labels:
            chan_label = QLabel("Channel")
            chan_label.setAlignment(Qt.AlignRight)
            chan_label.setFixedWidth(self.width_label)
            row_layout = QHBoxLayout()
            row_layout.addWidget(chan_label)
            chan_box = QComboBox(self)
            for label in channel_labels:
                chan_box.addItem(label)
            chan_box.setCurrentText(general_config.get("Channel_for_spectogram", channel_labels[0]))
            chan_box.currentIndexChanged.connect(lambda: self.apply_changes(general_config))
            self.optionboxes["Channel_for_spectogram"] = [chan_box]
            row_layout.addWidget(chan_box)
            form_layout.addRow(row_layout)

        # Frequency limits spinboxes
        freq_label = QLabel("Frequency limits")
        freq_label.setAlignment(Qt.AlignRight)
        freq_label.setFixedWidth(self.width_label)
        row_layout = QHBoxLayout()
        row_layout.addWidget(freq_label)
        self.spinboxes["Spectogram_limit_hz"] = []
        value_in_list = (
            general_config["Spectogram_limit_hz"]
            if isinstance(general_config["Spectogram_limit_hz"], list)
            else [general_config["Spectogram_limit_hz"]]
        )
        for value in value_in_list:
            spinbox = QDoubleSpinBox(self)
            spinbox.setMinimum(0)
            spinbox.setMaximum(10000)
            spinbox.setDecimals(0)
            spinbox.setValue(value)
            spinbox.setSuffix(" Hz")
            spinbox.editingFinished.connect(lambda: self.apply_changes(general_config))
            self.spinboxes["Spectogram_limit_hz"].append(spinbox)
            row_layout.addWidget(spinbox)
        form_layout.addRow(row_layout)

        # Colorbar limits
        power_label = QLabel("Colorbar limits")
        power_label.setAlignment(Qt.AlignRight)
        power_label.setFixedWidth(self.width_label)
        row_layout = QHBoxLayout()
        row_layout.addWidget(power_label)
        current_limits = general_config.get("Spectrogram_power_limits", [-1, 3])
        self.spinboxes["Spectrogram_power_limits"] = []
        for value in current_limits:
            spinbox = QDoubleSpinBox(self)
            spinbox.setMinimum(-1000)
            spinbox.setMaximum(1000)
            spinbox.setDecimals(1)
            spinbox.setValue(value)
            spinbox.editingFinished.connect(lambda: self.apply_changes(general_config))
            self.spinboxes["Spectrogram_power_limits"].append(spinbox)
            row_layout.addWidget(spinbox)
        form_layout.addRow(row_layout)

        layout.addLayout(form_layout)
        layout.addStretch(1)

    def apply_changes(self, general_config):
        old_config = copy.deepcopy(general_config)
        for id, spinbox_list in self.spinboxes.items():
            for index, spinbox in enumerate(spinbox_list):
                value = float(spinbox.value()) if id == "Spectrogram_power_limits" else int(spinbox.value())
                if isinstance(general_config[id], list):
                    general_config[id][index] = value
                else:
                    general_config[id] = value
        for id, optionbox_list in self.optionboxes.items():
            for optionbox in optionbox_list:
                general_config[id] = optionbox.currentText()
        changed_config_settings = self.config_keys_which_changed(old_config, general_config)
        self.changesMade.emit(changed_config_settings)

    def config_keys_which_changed(self, config1, config2):
        differing_keys = []
        for key in config1.keys():
            if config1[key] != config2[key]:
                differing_keys.append(key)
        return differing_keys


class PeriodogramConfiguration(QDialog):
    changesMade = Signal(list)

    def __init__(self, general_config, channel_labels=None, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.width_label = 200
        self.spinboxes = {}
        self.optionboxes = {}

        # Description
        description = QLabel(
            "\u24d8 "
            "Pwelch is computed on a given epoch or on selected parts of an EEG signal "
            "and displayed in the Periodogram panel on the top right. "
            "Configure periodogram parameters here."
        )
        description.setWordWrap(True)
        layout.addWidget(description)

        form_layout = QFormLayout()

        # Channel selector
        if channel_labels:
            chan_label = QLabel("Channel")
            chan_label.setAlignment(Qt.AlignRight)
            chan_label.setFixedWidth(self.width_label)
            row_layout = QHBoxLayout()
            row_layout.addWidget(chan_label)
            chan_box = QComboBox(self)
            for label in channel_labels:
                chan_box.addItem(label)
            chan_box.setCurrentText(general_config.get("Periodogram_channel", channel_labels[0]))
            chan_box.currentIndexChanged.connect(lambda: self.apply_changes(general_config))
            self.optionboxes["Periodogram_channel"] = [chan_box]
            row_layout.addWidget(chan_box)
            form_layout.addRow(row_layout)

        # Frequency limits spinboxes
        freq_label = QLabel("Frequency limits")
        freq_label.setAlignment(Qt.AlignRight)
        freq_label.setFixedWidth(self.width_label)
        row_layout = QHBoxLayout()
        row_layout.addWidget(freq_label)
        self.spinboxes["Periodogram_limit_hz"] = []
        value_in_list = (
            general_config["Periodogram_limit_hz"]
            if isinstance(general_config["Periodogram_limit_hz"], list)
            else [general_config["Periodogram_limit_hz"]]
        )
        for value in value_in_list:
            spinbox = QDoubleSpinBox(self)
            spinbox.setMinimum(0)
            spinbox.setMaximum(10000)
            spinbox.setDecimals(0)
            spinbox.setValue(value)
            spinbox.setSuffix(" Hz")
            spinbox.editingFinished.connect(lambda: self.apply_changes(general_config))
            self.spinboxes["Periodogram_limit_hz"].append(spinbox)
            row_layout.addWidget(spinbox)
        form_layout.addRow(row_layout)

        # Display mode
        mode_label = QLabel("Display mode")
        mode_label.setAlignment(Qt.AlignRight)
        mode_label.setFixedWidth(self.width_label)
        row_layout = QHBoxLayout()
        row_layout.addWidget(mode_label)
        mode_box = QComboBox(self)
        for option in ["Raw Power", "dB", "1/f Removed"]:
            mode_box.addItem(option)
        mode_box.setCurrentText(general_config.get("Periodogram_display_mode", "1/f Removed"))
        mode_box.currentIndexChanged.connect(lambda: self.apply_changes(general_config))
        self.optionboxes["Periodogram_display_mode"] = [mode_box]
        row_layout.addWidget(mode_box)
        form_layout.addRow(row_layout)

        layout.addLayout(form_layout)
        layout.addStretch(1)

    def apply_changes(self, general_config):
        old_config = copy.deepcopy(general_config)
        for id, spinbox_list in self.spinboxes.items():
            for index, spinbox in enumerate(spinbox_list):
                value = int(spinbox.value())
                if isinstance(general_config[id], list):
                    general_config[id][index] = value
                else:
                    general_config[id] = value
        for id, optionbox_list in self.optionboxes.items():
            for optionbox in optionbox_list:
                general_config[id] = optionbox.currentText()
        changed_config_settings = self.config_keys_which_changed(old_config, general_config)
        self.changesMade.emit(changed_config_settings)

    def config_keys_which_changed(self, config1, config2):
        differing_keys = []
        for key in config1.keys():
            if config1[key] != config2[key]:
                differing_keys.append(key)
        return differing_keys


class WaveletConfiguration(QDialog):
    changesMade = Signal(list)

    def __init__(self, general_config, channel_labels=None, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.width_label = 200
        self.spinboxes = {}
        self.optionboxes = {}
        self.checkboxes = {}

        # Description
        description = QLabel(
            "\u24d8 " \
            "A wavelet decomposition is computed for a given epoch and displayed in the " \
            "time-frequency panel at the bottom. Configure available Morlet wavelet time-frequency " \
            "decomposition parameters here." \
        )
        description.setWordWrap(True)
        layout.addWidget(description)

        form_layout = QFormLayout()

        # Channel selector
        if channel_labels:
            labelbox = QLabel("Channel")
            labelbox.setAlignment(Qt.AlignRight)
            labelbox.setFixedWidth(self.width_label)
            row_layout = QHBoxLayout()
            row_layout.addWidget(labelbox)
            tf_channel_box = QComboBox(self)
            for label in channel_labels:
                tf_channel_box.addItem(label)
            tf_channel_box.setCurrentText(general_config.get("Wavelet_channel", channel_labels[0]))
            tf_channel_box.currentIndexChanged.connect(lambda: self.apply_changes(general_config))
            self.optionboxes["Wavelet_channel"] = [tf_channel_box]
            row_layout.addWidget(tf_channel_box)
            form_layout.addRow(row_layout)

        # Frequency scale
        scale_label = QLabel("Frequency scale")
        scale_label.setAlignment(Qt.AlignRight)
        scale_label.setFixedWidth(self.width_label)
        row_layout = QHBoxLayout()
        row_layout.addWidget(scale_label)
        scale_box = QComboBox(self)
        for option in ["Logarithmic", "Linear"]:
            scale_box.addItem(option)
        scale_box.setCurrentText(general_config["Wavelet_frequency_scale"])
        scale_box.currentIndexChanged.connect(lambda: self.apply_changes(general_config))
        self.optionboxes["Wavelet_frequency_scale"] = [scale_box]
        row_layout.addWidget(scale_box)
        form_layout.addRow(row_layout)

        # Frequency limits spinboxes
        freq_label = QLabel("Frequency limits")
        freq_label.setAlignment(Qt.AlignRight)
        freq_label.setFixedWidth(self.width_label)
        row_layout = QHBoxLayout()
        row_layout.addWidget(freq_label)
        self.spinboxes["Wavelet_frequency_limits_hz"] = []
        value_in_list = general_config["Wavelet_frequency_limits_hz"] if isinstance(general_config["Wavelet_frequency_limits_hz"], list) else [general_config["Wavelet_frequency_limits_hz"]]
        for value in value_in_list:
            spinbox = QDoubleSpinBox(self)
            spinbox.setMinimum(0)
            spinbox.setMaximum(10000)
            spinbox.setDecimals(2)
            spinbox.setValue(value)
            spinbox.setSuffix(" Hz")
            spinbox.editingFinished.connect(lambda: self.apply_changes(general_config))
            self.spinboxes["Wavelet_frequency_limits_hz"].append(spinbox)
            row_layout.addWidget(spinbox)
        form_layout.addRow(row_layout)

        # Normalization
        norm_label = QLabel("Normalization")
        norm_label.setAlignment(Qt.AlignRight)
        norm_label.setFixedWidth(self.width_label)
        row_layout = QHBoxLayout()
        row_layout.addWidget(norm_label)
        norm_box = QComboBox(self)
        for option in ["Raw Power", "L2-Normalized Power", "Z-Standardized Power", "dB (median baseline)"]:
            norm_box.addItem(option)
        norm_box.setCurrentText(general_config["Wavelet_display_mode"])
        self.optionboxes["Wavelet_display_mode"] = [norm_box]
        row_layout.addWidget(norm_box)
        form_layout.addRow(row_layout)

        # Colorbar limits (one row; values update when normalization changes)
        power_label = QLabel("Colorbar limits")
        power_label.setAlignment(Qt.AlignRight)
        power_label.setFixedWidth(self.width_label)
        row_layout = QHBoxLayout()
        row_layout.addWidget(power_label)
        current_norm = general_config.get("Wavelet_display_mode", "Raw Power")
        power_limits_dict = general_config.get("Wavelet_power_limits", {})
        _fallback = {"Raw Power": [-1, 3], "L2-Normalized Power": [-1, 3],
                     "Z-Standardized Power": [-3, 3], "dB (median baseline)": [0, 20]}
        current_limits = power_limits_dict.get(current_norm, _fallback.get(current_norm, [-1, 3]))
        self._power_min_spin = QDoubleSpinBox(self)
        self._power_min_spin.setMinimum(-1000)
        self._power_min_spin.setMaximum(1000)
        self._power_min_spin.setDecimals(1)
        self._power_min_spin.setValue(current_limits[0])
        self._power_min_spin.editingFinished.connect(lambda: self._on_power_limits_changed(general_config))
        self._power_max_spin = QDoubleSpinBox(self)
        self._power_max_spin.setMinimum(-1000)
        self._power_max_spin.setMaximum(1000)
        self._power_max_spin.setDecimals(1)
        self._power_max_spin.setValue(current_limits[1])
        self._power_max_spin.editingFinished.connect(lambda: self._on_power_limits_changed(general_config))
        row_layout.addWidget(self._power_min_spin)
        row_layout.addWidget(self._power_max_spin)
        form_layout.addRow(row_layout)

        # Connect normalization dropdown after power spinboxes are created
        self._norm_box = norm_box
        norm_box.currentIndexChanged.connect(lambda: self._on_norm_changed(general_config))

        # Ridge checkbox
        ridge_label = QLabel("Show ridge")
        ridge_label.setAlignment(Qt.AlignRight)
        ridge_label.setFixedWidth(self.width_label)
        ridge_checkbox = QCheckBox(self)
        ridge_checkbox.setChecked(general_config.get("Wavelet_show_ridge", False))
        ridge_checkbox.stateChanged.connect(lambda: self.apply_changes(general_config))
        self.checkboxes["Wavelet_show_ridge"] = ridge_checkbox
        row_layout = QHBoxLayout()
        row_layout.addWidget(ridge_label)
        row_layout.addWidget(ridge_checkbox)
        form_layout.addRow(row_layout)

        # Visibility checkbox
        labelbox = QLabel("Show wavelet decomposition")
        labelbox.setAlignment(Qt.AlignRight)
        labelbox.setFixedWidth(self.width_label)
        tf_visible_checkbox = QCheckBox(self)
        tf_visible_checkbox.setChecked(general_config.get("Wavelet_panel_visible", True))
        tf_visible_checkbox.stateChanged.connect(lambda: self.apply_changes(general_config))
        self.checkboxes["Wavelet_panel_visible"] = tf_visible_checkbox
        row_layout = QHBoxLayout()
        row_layout.addWidget(labelbox)
        row_layout.addWidget(tf_visible_checkbox)
        form_layout.addRow(row_layout)

        layout.addLayout(form_layout)
        layout.addStretch(1)

    def _on_norm_changed(self, general_config):
        """Normalization dropdown changed: save current spinbox values under old mode, then switch."""
        old_norm = general_config.get("Wavelet_display_mode", "Raw Power")
        general_config.setdefault("Wavelet_power_limits", {})[old_norm] = [
            float(self._power_min_spin.value()),
            float(self._power_max_spin.value()),
        ]
        self.apply_changes(general_config)
        new_norm = self._norm_box.currentText()
        _fallback = {"Raw Power": [-1, 3], "L2-Normalized Power": [-1, 3],
                     "Z-Standardized Power": [-3, 3], "dB (median baseline)": [0, 20]}
        limits = general_config.get("Wavelet_power_limits", {}).get(
            new_norm, _fallback.get(new_norm, [-1, 3]))
        self._power_min_spin.blockSignals(True)
        self._power_max_spin.blockSignals(True)
        self._power_min_spin.setValue(limits[0])
        self._power_max_spin.setValue(limits[1])
        self._power_min_spin.blockSignals(False)
        self._power_max_spin.blockSignals(False)

    def _on_power_limits_changed(self, general_config):
        """Power limit spinbox edited: save under current normalization mode."""
        current_norm = self._norm_box.currentText()
        general_config.setdefault("Wavelet_power_limits", {})[current_norm] = [
            float(self._power_min_spin.value()),
            float(self._power_max_spin.value()),
        ]
        self.apply_changes(general_config)

    def apply_changes(self, general_config):
        old_config = copy.deepcopy(general_config)
        for id, spinbox_list in self.spinboxes.items():
            for index, spinbox in enumerate(spinbox_list):
                value = float(spinbox.value())
                if isinstance(general_config[id], list):
                    general_config[id][index] = value
                else:
                    general_config[id] = value
        for id, optionbox_list in self.optionboxes.items():
            for optionbox in optionbox_list:
                general_config[id] = optionbox.currentText()
        for id, checkbox in self.checkboxes.items():
            general_config[id] = checkbox.isChecked()
        changed_config_settings = self.config_keys_which_changed(old_config, general_config)
        self.changesMade.emit(changed_config_settings)

    def config_keys_which_changed(self, config1, config2):
        differing_keys = []
        for key in config1.keys():
            if config1[key] != config2[key]:
                differing_keys.append(key)
        return differing_keys


class ChannelConfiguration(QDialog):
    changesMade = Signal()

    def __init__(self, channel_config, general_config=None, parent=None):
        super().__init__(parent)
        self.general_config = general_config
        layout = QVBoxLayout(self)
        self.scale = []
        self.display = []
        self.color = []
        self.label = []
        self.shift = []

        # Top checkboxes in 2x2 grid layout
        top_checkbox_layout = QGridLayout()
        self.apply_all_checkbox = QCheckBox("Apply changes to all channels")
        self.select_all_checkbox = QCheckBox("Select/deselect all channels")
        self.select_all_checkbox.setChecked(True)
        self.select_all_checkbox.stateChanged.connect(lambda: self._on_select_all_changed(channel_config))
        self.stack_channels_checkbox = QCheckBox("Stack channels")
        self.stack_channels_checkbox.setChecked(
            general_config.get("Stack_channels", False) if general_config is not None else False
        )
        self.stack_channels_checkbox.stateChanged.connect(self._on_stack_changed)
        self.z_standardize_checkbox = QCheckBox("Robustly z-standardize channels")
        self.z_standardize_checkbox.setChecked(
            general_config.get("Robust_z_standardize", False) if general_config is not None else False
        )
        self.z_standardize_checkbox.stateChanged.connect(self._on_z_standardize_changed)
        top_checkbox_layout.addWidget(self.apply_all_checkbox, 0, 0)
        top_checkbox_layout.addWidget(self.stack_channels_checkbox, 0, 1)
        top_checkbox_layout.addWidget(self.select_all_checkbox, 1, 0)
        top_checkbox_layout.addWidget(self.z_standardize_checkbox, 1, 1)
        layout.addLayout(top_checkbox_layout)

        # Create a scroll area
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)  # Allow the widget to resize within the scroll area
        layout.addWidget(scroll_area)

        # Create a widget to hold the form layout
        form_widget = QWidget()
        form_layout = QFormLayout(form_widget)  # Set the form layout on the widget
        scroll_area.setWidget(form_widget)     # Set the widget as the scroll area's content

        # Channel name width
        channel_name_widget_width = max(len(chaninfo["Channel_name"]) for chaninfo in channel_config) * 8 + 10
        channel_number_widget_width = len(str(len(channel_config))) * 6 *2

        # Bold font
        bold_font = QFont()
        bold_font.setBold(True)

        # Create header 
        placeholder0 = QLabel("#")
        placeholder0.setFixedWidth(channel_number_widget_width)      
        placeholder0.setFont(bold_font)
        placeholder0.setAlignment(Qt.AlignRight)   
        placeholder1 = QLabel("")
        placeholder1.setFixedWidth(channel_name_widget_width)
        placeholder2 = QLabel("")
        placeholder2.setFixedWidth(QCheckBox().sizeHint().width())  # Set width of the placeholder to match the checkbox below
        labelbox1 = QLabel("Scaling factor")
        labelbox1.setAlignment(Qt.AlignLeft) 
        labelbox1.setFont(bold_font)           
        labelbox2 = QLabel("Vertical shift")
        labelbox2.setAlignment(Qt.AlignLeft)  
        labelbox2.setFont(bold_font)          
        labelbox3 = QLabel("Channel color")
        labelbox3.setAlignment(Qt.AlignLeft)   
        labelbox3.setFont(bold_font)

        row_layout = QHBoxLayout()
        row_layout.addWidget(placeholder0)
        row_layout.addWidget(placeholder1)
        row_layout.addWidget(placeholder2)
        row_layout.addWidget(labelbox1)
        row_layout.addWidget(labelbox2)
        row_layout.addWidget(labelbox3)
        form_layout.addRow(row_layout)
        
        # Loop through channels
        for count, chaninfo in enumerate(channel_config):

            # Channel number
            numberbox = QLabel(str(count+1))
            numberbox.setAlignment(Qt.AlignRight)             
            numberbox.setFixedWidth(channel_number_widget_width)
            numberbox.setFont(bold_font)   

            # Channel label
            labelbox = QLineEdit(chaninfo["Channel_name"])
            labelbox.setAlignment(Qt.AlignLeft)
            labelbox.setFixedWidth(channel_name_widget_width)
            labelbox.textChanged.connect(lambda text, i=count: self.change_event(channel_config, i, "label"))

            # Value by which EEG is multiplied
            spinbox = QDoubleSpinBox(self)
            spinbox.setMinimum(0)
            spinbox.setMaximum(10000)
            spinbox.setDecimals(0)
            spinbox.setValue(chaninfo["Scaling_factor"])
            spinbox.setSuffix(" %")
            spinbox.valueChanged.connect(lambda val, i=count: self.change_event(channel_config, i, "scale"))

            # Vertical shift
            shiftbox = QDoubleSpinBox(self)
            shiftbox.setMinimum(0)
            shiftbox.setMaximum(10000)
            shiftbox.setDecimals(0)
            shiftbox.setValue(chaninfo["Vertical_shift"])
            shiftbox.valueChanged.connect(lambda val, i=count: self.change_event(channel_config, i, "shift"))

            # Whether channel is displayed or not
            checkbox = QCheckBox(self)
            checkbox.setChecked(chaninfo["Display_on_screen"])
            checkbox.setMaximumWidth(checkbox.sizeHint().width())
            checkbox.clicked.connect(lambda checked, i=count: self.change_event(channel_config, i, "display"))

            # Channel color
            colorbox = QComboBox(self)
            colorbox.addItem("Black")
            colorbox.addItem("Blue")
            colorbox.addItem("Green")
            colorbox.addItem("Magenta")
            colorbox.addItem("Orange")
            colorbox.addItem("Cyan")
            colorbox.setCurrentText(chaninfo["Channel_color"])
            colorbox.currentIndexChanged.connect(lambda idx, i=count: self.change_event(channel_config, i, "color"))

            # Layout
            row_layout = QHBoxLayout()
            row_layout.addWidget(numberbox)
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

    def _on_select_all_changed(self, channel_config):
        checked = self.select_all_checkbox.isChecked()
        for i, cb in enumerate(self.display):
            cb.blockSignals(True)
            cb.setChecked(checked)
            cb.blockSignals(False)
            channel_config[i]["Display_on_screen"] = checked
        self.changesMade.emit()

    def _on_stack_changed(self):
        if self.general_config is not None:
            self.general_config["Stack_channels"] = self.stack_channels_checkbox.isChecked()
        self.changesMade.emit()

    def _on_z_standardize_changed(self):
        if self.general_config is not None:
            self.general_config["Robust_z_standardize"] = self.z_standardize_checkbox.isChecked()
        self.changesMade.emit()

    def change_event(self, channel_config, chan_idx=None, prop=None):
        if self.apply_all_checkbox.isChecked() and chan_idx is not None and prop is not None:
            if prop == "scale":
                val = self.scale[chan_idx].value()
                for s in self.scale:
                    s.blockSignals(True)
                    s.setValue(val)
                    s.blockSignals(False)
            elif prop == "shift":
                val = self.shift[chan_idx].value()
                for s in self.shift:
                    s.blockSignals(True)
                    s.setValue(val)
                    s.blockSignals(False)
            elif prop == "color":
                val = self.color[chan_idx].currentText()
                for c in self.color:
                    c.blockSignals(True)
                    c.setCurrentText(val)
                    c.blockSignals(False)

        for counter, chaninfo in enumerate(channel_config):
            chaninfo["Channel_name"] = self.label[counter].text()
            chaninfo["Channel_color"] = self.color[counter].currentText()
            chaninfo["Display_on_screen"] = self.display[counter].isChecked()
            chaninfo["Scaling_factor"] = int(self.scale[counter].value())
            chaninfo["Vertical_shift"] = int(self.shift[counter].value())
        self.changesMade.emit()
