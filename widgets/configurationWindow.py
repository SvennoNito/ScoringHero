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
    QGridLayout,
    QListWidget,
    QListWidgetItem,
    QAbstractItemView,
    QMessageBox,
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QColor, QFont
import copy


class ConfigurationWindow(QDialog):
    changesMade = Signal()

    def __init__(self, config, AnnotationContainer, allow_staging, channel_labels=None):
        super().__init__()
        self.setWindowTitle("Configuration Window")
        self.resize(630, 500)

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

        # Ridge checkbox
        ridge_label = QLabel("Show ridge")
        ridge_label.setAlignment(Qt.AlignRight)
        ridge_label.setFixedWidth(self.width_label)
        ridge_checkbox = QCheckBox(self)
        ridge_checkbox.setChecked(general_config.get("Wavelet_show_ridge", False))
        wavelet_visible = general_config.get("Wavelet_panel_visible", True)
        ridge_checkbox.setEnabled(wavelet_visible)
        ridge_label.setEnabled(wavelet_visible)
        ridge_checkbox.stateChanged.connect(lambda: self.apply_changes(general_config))
        self.checkboxes["Wavelet_show_ridge"] = ridge_checkbox
        tf_visible_checkbox.stateChanged.connect(lambda state: (
            ridge_checkbox.setEnabled(bool(state)),
            ridge_label.setEnabled(bool(state)),
        ))
        row_layout = QHBoxLayout()
        row_layout.addWidget(ridge_label)
        row_layout.addWidget(ridge_checkbox)
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


class _DraggableList(QListWidget):
    """QListWidget that selects the item under the cursor on mouse-press so that
    drag starts immediately on the first click+drag (no prior selection needed)."""

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            item = self.itemAt(event.pos())
            if item is not None:
                self.setCurrentItem(item)
        super().mousePressEvent(event)


class ChannelConfiguration(QDialog):
    changesMade = Signal()
    displayOnlyChanged = Signal()       # visibility/color/scale/shift — no signal rebuild needed
    signalRebuildNeeded = Signal(int)   # reref/flip/label changed — rebuild display; chan_idx passed
                                        # so caller can skip spectrogram recompute if unrelated channel
    channelMoved = Signal(int, int)     # (from_index, to_index)
    channelAdded = Signal(str, str)     # (channel_a_name, channel_b_name)
    channelDeleted = Signal(int)        # channel index to delete

    def __init__(self, channel_config, general_config=None, parent=None):
        super().__init__(parent)
        self.general_config = general_config
        self.channel_config = channel_config
        layout = QVBoxLayout(self)
        self.scale = []
        self.display = []
        self.color = []
        self.label = []
        self.shift = []
        self.reref = []
        self.flip = []
        self.number_labels = []
        self.trash_buttons = []

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

        # Channel name width
        channel_name_widget_width = max(len(chaninfo["Channel_name"]) for chaninfo in channel_config) * 8 + 10
        channel_number_widget_width = len(str(len(channel_config))) * 6 * 2

        # All channel names (for re-reference dropdown)
        all_channel_names = [ch["Channel_name"] for ch in channel_config]

        # Fixed widths for each column so header labels align with data widgets
        _dummy_spinbox = QDoubleSpinBox()
        _dummy_spinbox.setSuffix(" %")
        spinbox_w = _dummy_spinbox.sizeHint().width()
        _dummy_colorbox = QComboBox()
        for _c in ["Black", "Blue", "Green", "Magenta", "Orange", "Cyan"]:
            _dummy_colorbox.addItem(_c)
        colorbox_w = _dummy_colorbox.sizeHint().width()
        rerefbox_w = max(len(n) for n in all_channel_names + ["None"]) * 8 + 35
        grip_w = 20  # width for drag handle column
        trash_w = 28  # width for trash button column
        # flip column: wide enough to show bold "Flip" label AND the bare checkbox
        _dummy_flip_label = QLabel("Flip")
        _dummy_flip_label.setFont(QFont())
        flip_col_w = max(_dummy_flip_label.sizeHint().width() + 4, QCheckBox().sizeHint().width())

        # Bold font
        bold_font = QFont()
        bold_font.setBold(True)

        # Fixed header row (sits above the list, not draggable)
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(6, 2, 6, 2)
        header_layout.setSpacing(6)
        h0 = QLabel("#")
        h0.setFixedWidth(channel_number_widget_width)
        h0.setFont(bold_font)
        h0.setAlignment(Qt.AlignRight)
        h_grip = QLabel("")
        h_grip.setFixedWidth(grip_w)
        h1 = QLabel("")
        h1.setFixedWidth(channel_name_widget_width)
        h2 = QLabel("")
        h2.setFixedWidth(QCheckBox().sizeHint().width())
        h3 = QLabel("Scaling factor")
        h3.setFixedWidth(spinbox_w)
        h3.setFont(bold_font)
        h4 = QLabel("Vertical shift")
        h4.setFixedWidth(spinbox_w)
        h4.setFont(bold_font)
        h5 = QLabel("Channel color")
        h5.setFixedWidth(colorbox_w)
        h5.setFont(bold_font)
        h6 = QLabel("Re-reference")
        h6.setFixedWidth(rerefbox_w)
        h6.setFont(bold_font)
        h7 = QLabel("Flip")
        h7.setFixedWidth(flip_col_w)
        h7.setFont(bold_font)
        h8 = QLabel("")
        h8.setFixedWidth(trash_w)
        for hw in [h0, h_grip, h1, h2, h3, h4, h5, h6, h7, h8]:
            header_layout.addWidget(hw)
        header_layout.addStretch()
        layout.addWidget(header_widget)

        # Draggable channel list
        self.channel_list = _DraggableList()
        self.channel_list.setDragDropMode(QAbstractItemView.InternalMove)
        self.channel_list.setDefaultDropAction(Qt.MoveAction)
        self.channel_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.channel_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.channel_list.model().rowsMoved.connect(
            lambda src_parent, src_start, src_end, dst_parent, dst_row:
                self._on_rows_moved(channel_config, src_start, dst_row)
        )
        layout.addWidget(self.channel_list)

        # "+" add-channel row below the list
        add_row_widget = QWidget()
        add_row_layout = QHBoxLayout(add_row_widget)
        add_row_layout.setContentsMargins(6, 2, 6, 2)
        add_row_layout.setSpacing(6)
        add_btn = QPushButton("+")
        add_btn.setFixedWidth(28)
        add_btn.setToolTip("Add re-referenced channel")
        add_btn.clicked.connect(self._on_add_channel)
        add_row_layout.addWidget(add_btn)
        add_row_layout.addStretch()
        layout.addWidget(add_row_widget)

        # Loop through channels
        for count, chaninfo in enumerate(channel_config):

            # Channel number
            numberbox = QLabel(str(count + 1))
            numberbox.setAlignment(Qt.AlignRight)
            numberbox.setFixedWidth(channel_number_widget_width)
            numberbox.setFont(bold_font)

            # Drag handle — QLabel passes mouse events to the QListWidget, initiating drag
            grip = QLabel("⠿")
            grip.setFixedWidth(grip_w)
            grip.setAlignment(Qt.AlignCenter)
            grip.setToolTip("Drag to reorder")

            # Channel label
            labelbox = QLineEdit(chaninfo["Channel_name"])
            labelbox.setAlignment(Qt.AlignLeft)
            labelbox.setFixedWidth(channel_name_widget_width)
            labelbox.textChanged.connect(lambda text, i=count: self.change_event(channel_config, i, "label"))

            # Value by which EEG is multiplied
            spinbox = QDoubleSpinBox()
            spinbox.setMinimum(0)
            spinbox.setMaximum(10000)
            spinbox.setDecimals(0)
            spinbox.setValue(chaninfo["Scaling_factor"])
            spinbox.setSuffix(" %")
            spinbox.setFixedWidth(spinbox_w)
            spinbox.valueChanged.connect(lambda val, i=count: self.change_event(channel_config, i, "scale"))

            # Vertical shift
            shiftbox = QDoubleSpinBox()
            shiftbox.setMinimum(0)
            shiftbox.setMaximum(10000)
            shiftbox.setDecimals(0)
            shiftbox.setValue(chaninfo["Vertical_shift"])
            shiftbox.setFixedWidth(spinbox_w)
            shiftbox.valueChanged.connect(lambda val, i=count: self.change_event(channel_config, i, "shift"))

            # Whether channel is displayed or not
            checkbox = QCheckBox()
            checkbox.setChecked(chaninfo["Display_on_screen"])
            checkbox.setMaximumWidth(checkbox.sizeHint().width())
            checkbox.clicked.connect(lambda checked, i=count: self.change_event(channel_config, i, "display"))

            # Channel color
            colorbox = QComboBox()
            colorbox.addItem("Black")
            colorbox.addItem("Blue")
            colorbox.addItem("Green")
            colorbox.addItem("Magenta")
            colorbox.addItem("Orange")
            colorbox.addItem("Cyan")
            colorbox.setCurrentText(chaninfo["Channel_color"])
            colorbox.setFixedWidth(colorbox_w)
            colorbox.currentIndexChanged.connect(lambda idx, i=count: self.change_event(channel_config, i, "color"))

            # Re-reference dropdown
            rerefbox = QComboBox()
            rerefbox.addItem("None")
            for name in all_channel_names:
                if name != chaninfo["Channel_name"]:
                    rerefbox.addItem(name)
            rerefbox.setCurrentText(chaninfo.get("Re_reference", "None"))
            rerefbox.setFixedWidth(rerefbox_w)
            rerefbox.currentIndexChanged.connect(lambda idx, i=count: self.change_event(channel_config, i, "reref"))

            # Flip polarity checkbox
            flipbox = QCheckBox()
            flipbox.setFixedWidth(flip_col_w)
            flipbox.setChecked(chaninfo.get("Flip_polarity", False))
            flipbox.clicked.connect(lambda checked, i=count: self.change_event(channel_config, i, "flip"))

            # Trash button (delete channel)
            trash_btn = QPushButton("🗑")
            trash_btn.setFixedWidth(trash_w)
            trash_btn.setToolTip("Delete channel")
            trash_btn.setStyleSheet(
                "QPushButton { color: #c0392b; border: none; background: transparent; font-size: 14px; }"
                "QPushButton:hover { background-color: rgba(192, 57, 43, 40); border-radius: 3px; }"
                "QPushButton:pressed { background-color: rgba(192, 57, 43, 80); }"
            )
            self.trash_buttons.append(trash_btn)
            trash_btn.clicked.connect(lambda checked, b=trash_btn: self._on_delete_channel_btn(b))

            # Row widget (becomes the list item's widget)
            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(2, 1, 2, 1)
            row_layout.setSpacing(6)
            row_layout.addWidget(numberbox)
            row_layout.addWidget(grip)
            row_layout.addWidget(labelbox)
            row_layout.addWidget(checkbox)
            row_layout.addWidget(spinbox)
            row_layout.addWidget(shiftbox)
            row_layout.addWidget(colorbox)
            row_layout.addWidget(rerefbox)
            row_layout.addWidget(flipbox)
            row_layout.addWidget(trash_btn)
            row_layout.addStretch()

            item = QListWidgetItem(self.channel_list)
            item.setSizeHint(row_widget.sizeHint())
            self.channel_list.setItemWidget(item, row_widget)

            self.label.append(labelbox)
            self.scale.append(spinbox)
            self.display.append(checkbox)
            self.color.append(colorbox)
            self.shift.append(shiftbox)
            self.reref.append(rerefbox)
            self.flip.append(flipbox)
            self.number_labels.append(numberbox)

    def _on_select_all_changed(self, channel_config):
        checked = self.select_all_checkbox.isChecked()
        for i, cb in enumerate(self.display):
            cb.blockSignals(True)
            cb.setChecked(checked)
            cb.blockSignals(False)
            channel_config[i]["Display_on_screen"] = checked
        self.displayOnlyChanged.emit()

    def _on_stack_changed(self):
        if self.general_config is not None:
            self.general_config["Stack_channels"] = self.stack_channels_checkbox.isChecked()
        self.displayOnlyChanged.emit()

    def _on_z_standardize_changed(self):
        if self.general_config is not None:
            self.general_config["Robust_z_standardize"] = self.z_standardize_checkbox.isChecked()
        self.displayOnlyChanged.emit()

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
            chaninfo["Re_reference"] = self.reref[counter].currentText()
            chaninfo["Flip_polarity"] = self.flip[counter].isChecked()
        # Display-only props: only a cheap redraw needed.
        # Signal props (reref, flip, label): need to rebuild eeg_data_display, but
        # spectrogram recomputation is only needed if this channel feeds the spectrogram
        # or wavelet panel — caller decides via the emitted index.
        display_only_props = {"display", "color", "scale", "shift"}
        signal_rebuild_props = {"reref", "flip", "label"}
        if prop in display_only_props:
            self.displayOnlyChanged.emit()
        elif prop in signal_rebuild_props:
            self.signalRebuildNeeded.emit(chan_idx if chan_idx is not None else -1)
        else:
            self.changesMade.emit()

    def _on_rows_moved(self, channel_config, src_start, dst_row):
        """Called when a channel row is drag-dropped to a new position.

        Qt rowsMoved semantics: the item at src_start is inserted before dst_row
        in the destination. After the removal of src_start, the final index is:
          - dst_row - 1  if dst_row > src_start
          - dst_row      otherwise
        """
        new_pos = dst_row - 1 if dst_row > src_start else dst_row

        # Update config list to match the new visual order
        moved_config = channel_config.pop(src_start)
        channel_config.insert(new_pos, moved_config)

        # Keep our widget reference lists in sync with the new order so that
        # change_event's enumerate(channel_config) loop stays correct.
        for widget_list in [self.label, self.scale, self.shift,
                             self.display, self.color, self.reref, self.flip,
                             self.number_labels, self.trash_buttons]:
            moved_widget = widget_list.pop(src_start)
            widget_list.insert(new_pos, moved_widget)

        # Update the displayed position numbers to reflect the new order
        for i, lbl in enumerate(self.number_labels):
            lbl.setText(str(i + 1))

        # Rebuild all reref dropdowns (channel positions have changed)
        all_names = [self.label[k].text() for k in range(len(self.label))]
        for k in range(len(self.label)):
            current_reref = self.reref[k].currentText()
            self.reref[k].blockSignals(True)
            self._rebuild_reref_combo(k, all_names)
            self.reref[k].setCurrentText(current_reref)
            self.reref[k].blockSignals(False)

        # Notify connection layer to move the eeg_data row and do a lightweight redraw.
        # changesMade is intentionally NOT emitted here — reordering channels does not
        # require recomputing spectrograms; the connection layer handles everything.
        self.channelMoved.emit(src_start, new_pos)

    def _rebuild_reref_combo(self, idx, all_channel_names):
        """Rebuild the re-reference combobox items for channel idx."""
        self.reref[idx].clear()
        self.reref[idx].addItem("None")
        for k, name in enumerate(all_channel_names):
            if k != idx:
                self.reref[idx].addItem(name)

    def _on_add_channel(self):
        """Show a popup to select two channels whose difference becomes a new channel."""
        all_names = [lb.text() for lb in self.label]
        if len(all_names) < 2:
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Add Re-referenced Channel")
        dlayout = QVBoxLayout(dialog)

        desc = QLabel("Create a new channel as:  Channel A \u2212 Channel B")
        dlayout.addWidget(desc)

        form = QFormLayout()
        combo_a = QComboBox()
        combo_b = QComboBox()
        for name in all_names:
            combo_a.addItem(name)
            combo_b.addItem(name)
        combo_a.setCurrentIndex(0)
        combo_b.setCurrentIndex(1)
        form.addRow("Channel A:", combo_a)
        form.addRow("Channel B:", combo_b)
        dlayout.addLayout(form)

        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("Add Channel")
        cancel_btn = QPushButton("Cancel")
        ok_btn.clicked.connect(dialog.accept)
        cancel_btn.clicked.connect(dialog.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        dlayout.addLayout(btn_layout)

        if dialog.exec() == QDialog.Accepted:
            a = combo_a.currentText()
            b = combo_b.currentText()
            self.channelAdded.emit(a, b)

    def _on_delete_channel_btn(self, btn):
        """Called when a trash button is clicked — resolve current index then confirm."""
        idx = self.trash_buttons.index(btn)
        self._on_delete_channel(idx)

    def _on_delete_channel(self, idx):
        """Show a confirmation dialog and emit channelDeleted if confirmed."""
        channel_name = self.label[idx].text()
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("Delete Channel")
        msg.setText(f"Delete channel \u2018{channel_name}\u2019?")
        msg.setInformativeText("This action cannot be reversed.")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
        msg.setDefaultButton(QMessageBox.Cancel)
        if msg.exec() == QMessageBox.Yes:
            self.channelDeleted.emit(idx)
