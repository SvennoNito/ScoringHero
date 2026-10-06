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
    QTimeEdit,
)
from PySide6.QtCore import Signal, Qt, QTime, QTimer
from PySide6.QtGui import QColor, QFont, QFontMetrics
import copy

from config.default_config import DEFAULT_LINE_WIDTH


class ConfigurationWindow(QDialog):
    changesMade = Signal()
    settingsApplied = Signal(list)

    def __init__(self, config, AnnotationContainer, allow_staging, channel_labels=None):
        super().__init__()
        self.setWindowTitle("Configuration Window")
        self.resize(630, 500)

        # General/Spectrogram/Periodogram/Wavelet pages edit `pending`; Channels and
        # Events pages edit the live config directly.
        self.live = config[0]
        self.base = copy.deepcopy(config[0])  # snapshot of what was last applied
        self.pending = copy.deepcopy(config[0])

        self.layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)

        # Create the pages
        self.channel_page = ChannelConfiguration(config[1], config[0])
        self.general_page = GeneralConfiguration(self.pending, allow_staging, channel_labels or [])
        self.events_page = EventConfiguration(AnnotationContainer)
        self.spectrogram_page = SpectrogramConfiguration(self.pending, channel_labels or [])
        self.wavelet_page = WaveletConfiguration(self.pending, channel_labels or [])
        self.periodogram_page = PeriodogramConfiguration(self.pending, channel_labels or [])
        for page in (self.general_page, self.spectrogram_page, self.wavelet_page, self.periodogram_page):
            page.changesMade.connect(self._update_apply_state)

        self.apply_button = QPushButton("Apply")
        self.apply_button.setFixedWidth(100)
        self.apply_button.setEnabled(False)
        self.apply_button.clicked.connect(self.apply_pending)
        button_row = QHBoxLayout()
        button_row.addStretch(1)
        button_row.addWidget(self.apply_button)
        self.layout.addLayout(button_row)
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

    def reject(self):
        # Esc and the close button both end up here (QDialog.closeEvent calls reject).
        # A channel rename that is still sitting in the debounce timer would
        # otherwise be dropped when the window closes, leaving
        # ui.channel_name_to_idx pointing at the pre-rename name.
        self.channel_page.flush_pending_rename()
        keys = self.resolve_pending()
        if keys is None:
            return  # Cancel: keep window open with edits intact
        if keys:
            self.settingsApplied.emit(keys)
        super().reject()

    def resolve_pending(self):
        """Ask Apply / Discard / Cancel if General/Spectrogram/Periodogram/Wavelet edits
        are unapplied. Apply commits them into the live config WITHOUT emitting
        settingsApplied; the caller must apply the returned keys. Returns the committed
        keys ([] if nothing pending or discarded), or None on Cancel."""
        if not self._changed_keys():
            return []
        box = QMessageBox(self)
        box.setWindowTitle("Unapplied changes")
        box.setText("There are pending changes. Apply them first?")
        apply_btn = box.addButton("Apply", QMessageBox.AcceptRole)
        discard_btn = box.addButton("Discard", QMessageBox.DestructiveRole)
        box.addButton("Cancel", QMessageBox.RejectRole)
        box.exec()
        clicked = box.clickedButton()
        if clicked is apply_btn:
            return self._commit_pending()
        if clicked is discard_btn:
            for k in self._changed_keys():
                self.pending[k] = copy.deepcopy(self.base[k])
            self._update_apply_state()
            return []
        return None

    def _changed_keys(self):
        return [k for k in self.pending if self.pending[k] != self.base.get(k)]

    def _update_apply_state(self, *_):
        self.apply_button.setEnabled(bool(self._changed_keys()))

    def _commit_pending(self):
        """Copy pending edits into the live config; return the changed keys."""
        keys = self._changed_keys()
        for k in keys:
            self.live[k] = copy.deepcopy(self.pending[k])
            self.base[k] = copy.deepcopy(self.pending[k])
        self._update_apply_state()
        return keys

    def apply_pending(self):
        """Commit pending edits into the live config; one settingsApplied emit for all keys."""
        keys = self._commit_pending()
        if keys:
            self.settingsApplied.emit(keys)


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
    eventDeleted = Signal(int)

    def __init__(self, AnnotationContainer, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.label = []
        self.remove_buttons = []

        color_w  = 24
        remove_w = 28

        bold_font = QFont()
        bold_font.setBold(True)
        fm = QFontMetrics(bold_font)
        count_w  = fm.horizontalAdvance("# events") + 4
        dur_w    = max(fm.horizontalAdvance("Total dur."), fm.horizontalAdvance("9999.9 s")) + 4

        # Header row
        header_layout = QHBoxLayout()
        h_label = QLabel("Label")
        h_label.setFont(bold_font)
        h_label.setAlignment(Qt.AlignLeft)
        header_layout.addWidget(h_label, 1)  # stretch=1: takes remaining space
        for text, width, align in [
            ("",           color_w,  Qt.AlignLeft),
            ("# events",   count_w,  Qt.AlignRight),
            ("Total dur.", dur_w,    Qt.AlignRight),
            ("",           remove_w, Qt.AlignLeft),
        ]:
            h = QLabel(text)
            h.setFont(bold_font)
            h.setAlignment(align)
            h.setFixedWidth(width)
            header_layout.addWidget(h)
        layout.addLayout(header_layout)

        # Data rows
        for count, container in enumerate(AnnotationContainer):
            qcolor = QColor(
                container.facecolor[0],
                container.facecolor[1],
                container.facecolor[2],
                container.facecolor[3],
            )

            # Label
            labelbox = QLineEdit(container.label)
            labelbox.setAlignment(Qt.AlignRight)
            labelbox.textChanged.connect(lambda: self.change_event(AnnotationContainer))

            # Color swatch
            colorbutton = QPushButton()
            colorbutton.setFixedWidth(color_w)
            colorbutton.setStyleSheet(f"background-color: {qcolor.name()};")

            # Event count
            count_label = QLabel(str(len(container.borders)))
            count_label.setFixedWidth(count_w)
            count_label.setAlignment(Qt.AlignRight)

            # Total duration
            total_s = sum(b[1] - b[0] for b in container.borders)
            dur_label = QLabel(f"{total_s:.1f} s")
            dur_label.setFixedWidth(dur_w)
            dur_label.setAlignment(Qt.AlignRight)

            # Remove button
            remove_btn = QPushButton("🗑")
            remove_btn.setFixedWidth(remove_w)
            remove_btn.setToolTip("Remove all events of this type")
            remove_btn.setStyleSheet(
                "QPushButton { color: #c0392b; border: none; background: transparent; font-size: 14px; }"
                "QPushButton:hover { background-color: rgba(192, 57, 43, 40); border-radius: 3px; }"
                "QPushButton:pressed { background-color: rgba(192, 57, 43, 80); }"
            )
            remove_btn.clicked.connect(lambda checked, b=remove_btn: self._on_remove_event_btn(b))
            self.remove_buttons.append(remove_btn)

            row_layout = QHBoxLayout()
            row_layout.addWidget(labelbox, 1)  # stretch=1: takes remaining space
            row_layout.addWidget(colorbutton)
            row_layout.addWidget(count_label)
            row_layout.addWidget(dur_label)
            row_layout.addWidget(remove_btn)
            layout.addLayout(row_layout)

            self.label.append(labelbox)

        layout.addStretch()

    def _on_remove_event_btn(self, btn):
        idx = self.remove_buttons.index(btn)
        label = self.label[idx].text()
        msg = QMessageBox(self)
        msg.setWindowTitle("Remove events")
        msg.setText(f"Are you sure you want to remove all \"{label}\" events? This action is irreversible.")
        btn_continue = msg.addButton("Continue", QMessageBox.ButtonRole.DestructiveRole)
        msg.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)
        msg.exec()
        if msg.clickedButton() is btn_continue:
            self.eventDeleted.emit(idx)

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
            "EEG_panel_time_unit": {"label": "EEG time unit in", "options": ["Seconds", "Minutes", "Hours", "Clock Time"]},
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

        # Recording start time field (active only when "Clock Time" is selected)
        start_label = QLabel("Recording start time")
        start_label.setAlignment(Qt.AlignRight)
        start_label.setFixedWidth(self.width_label)
        self.start_time_edit = QTimeEdit(self)
        self.start_time_edit.setDisplayFormat("HH:mm")
        start_str = general_config.get("Recording_start_time", "00:00")
        try:
            h, m = map(int, start_str.split(":"))
            self.start_time_edit.setTime(QTime(h, m))
        except Exception:
            self.start_time_edit.setTime(QTime(0, 0))
        is_clock_mode = general_config.get("EEG_panel_time_unit", "Seconds") == "Clock Time"
        self.start_time_edit.setEnabled(is_clock_mode)
        start_label.setEnabled(is_clock_mode)
        time_unit_combo = self.optionboxes["EEG_panel_time_unit"][0]
        time_unit_combo.currentTextChanged.connect(
            lambda text, lbl=start_label: (
                self.start_time_edit.setEnabled(text == "Clock Time"),
                lbl.setEnabled(text == "Clock Time"),
            )
        )
        start_row = QHBoxLayout()
        start_row.addWidget(start_label)
        start_row.addWidget(self.start_time_edit)
        form_layout.addRow(start_row)

        # Edits write into the pending config; the window-level Apply commits them.
        for spinbox_list in self.spinboxes.values():
            for spinbox in spinbox_list:
                spinbox.valueChanged.connect(lambda _=None: self.apply_changes(general_config))
        for optionbox_list in self.optionboxes.values():
            for optionbox in optionbox_list:
                optionbox.currentTextChanged.connect(lambda _=None: self.apply_changes(general_config))
        self.start_time_edit.timeChanged.connect(lambda _=None: self.apply_changes(general_config))

        # Final layout
        layout.addLayout(form_layout)



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

        general_config["Recording_start_time"] = self.start_time_edit.time().toString("HH:mm")

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
    displayOnlyChanged = Signal()       # visibility/color/scale/shift/subtract median/line width — no signal rebuild
    signalRebuildNeeded = Signal(int)   # reref/flip changed — rebuild display; chan_idx passed (-1: all
                                        # channels) so caller can skip spectrogram recompute if unrelated channel
    channelRenamed = Signal()           # label changed — labels only, no signal rebuild (debounced)
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
        self.subtract_median = []
        self.line_width = []
        self.number_labels = []
        self.trash_buttons = []

        # Channel names as of the last processed rename, so an edit can tell what
        # the old name was and re-point the references that used it.
        self._known_names = [ch["Channel_name"] for ch in channel_config]

        # Renaming is a per-keystroke event but only needs one GUI refresh, so
        # coalesce a burst of typing into a single emit.
        self._rename_timer = QTimer(self)
        self._rename_timer.setSingleShot(True)
        self._rename_timer.setInterval(300)
        self._rename_timer.timeout.connect(self._emit_rename)

        # Guard so flush_pending_rename() is a no-op unless a rename is really pending.
        self._rename_pending = False

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
        # Bold font
        bold_font = QFont()
        bold_font.setBold(True)

        # Re-reference column: wide enough for the bold header AND a combo box holding the longest option
        _dummy_reref_label = QLabel("Re-reference")
        _dummy_reref_label.setFont(bold_font)
        _dummy_rerefbox = QComboBox()
        _dummy_rerefbox.addItems(["None"] + all_channel_names)
        rerefbox_w = max(_dummy_reref_label.sizeHint().width() + 4, _dummy_rerefbox.sizeHint().width())
        grip_w = 20  # width for drag handle column
        trash_w = 28  # width for trash button column
        # flip column: wide enough to show bold "Flip" label AND the bare checkbox
        _dummy_flip_label = QLabel("Flip")
        _dummy_flip_label.setFont(QFont())
        flip_col_w = max(_dummy_flip_label.sizeHint().width() + 4, QCheckBox().sizeHint().width())

        # Subtract median column: wide enough for the two-row bold header AND the checkbox
        _dummy_subtract_median_label = QLabel("Subtract\nmedian")
        _dummy_subtract_median_label.setFont(bold_font)
        subtract_median_col_w = max(_dummy_subtract_median_label.sizeHint().width() + 4,
                                    QCheckBox().sizeHint().width())
        line_width_col_w = spinbox_w

        # Fixed header row (sits above the list, not draggable)
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(6, 2, 6, 2)
        header_layout.setSpacing(6)
        h0 = QLabel("#")
        h0.setFixedWidth(channel_number_widget_width)
        h0.setFont(bold_font)
        h0.setAlignment(Qt.AlignRight | Qt.AlignBottom)
        h_grip = QLabel("")
        h_grip.setFixedWidth(grip_w)
        h1 = QLabel("")
        h1.setFixedWidth(channel_name_widget_width)
        h2 = QLabel("")
        h2.setFixedWidth(QCheckBox().sizeHint().width())
        h3 = QLabel("Scaling\nfactor")
        h3.setFixedWidth(spinbox_w)
        h4 = QLabel("Vertical\nshift")
        h4.setFixedWidth(spinbox_w)
        h5 = QLabel("Channel\ncolor")
        h5.setFixedWidth(colorbox_w)
        h6 = QLabel("Re-reference")
        h6.setFixedWidth(rerefbox_w)
        h7 = QLabel("Flip")
        h7.setFixedWidth(flip_col_w)
        h_subtract_median = QLabel("Subtract\nmedian")
        h_subtract_median.setFixedWidth(subtract_median_col_w)
        h_line_width = QLabel("Line\nwidth")
        h_line_width.setFixedWidth(line_width_col_w)
        h8 = QLabel("")
        h8.setFixedWidth(trash_w)
        # Two-row headers: bottom-align every header so the text sits right above its column
        for hw in [h3, h4, h5, h6, h7, h_subtract_median, h_line_width]:
            hw.setFont(bold_font)
            hw.setAlignment(Qt.AlignLeft | Qt.AlignBottom)
        for hw in [h0, h_grip, h1, h2, h3, h4, h5, h6, h7, h_subtract_median, h_line_width, h8]:
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
            labelbox.textChanged.connect(lambda text, i=count: self._on_label_edited(channel_config, i))

            # Value by which EEG is multiplied
            spinbox = QDoubleSpinBox()
            spinbox.setMinimum(0)
            spinbox.setMaximum(1000000)
            spinbox.setDecimals(0)
            spinbox.setValue(chaninfo["Scaling_factor"])
            spinbox.setSuffix(" %")
            spinbox.setFixedWidth(spinbox_w)
            spinbox.valueChanged.connect(lambda val, i=count: self.change_event(channel_config, i, "scale"))

            # Vertical shift
            shiftbox = QDoubleSpinBox()
            shiftbox.setMinimum(-10000)
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

            # Subtract median checkbox
            subtract_median_box = QCheckBox()
            subtract_median_box.setFixedWidth(subtract_median_col_w)
            subtract_median_box.setChecked(chaninfo.get("Subtract_median", False))
            subtract_median_box.clicked.connect(
                lambda checked, i=count: self.change_event(channel_config, i, "subtract_median"))
            # Line width
            line_width_box = QDoubleSpinBox()
            line_width_box.setMinimum(0.5)
            line_width_box.setMaximum(5)
            line_width_box.setSingleStep(0.5)
            line_width_box.setDecimals(1)
            line_width_box.setSuffix(" px")
            line_width_box.setValue(chaninfo.get("Line_width", DEFAULT_LINE_WIDTH))
            line_width_box.setFixedWidth(line_width_col_w)
            line_width_box.valueChanged.connect(
                lambda val, i=count: self.change_event(channel_config, i, "line_width"))

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
            row_layout.addWidget(subtract_median_box)
            row_layout.addWidget(line_width_box)
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
            self.subtract_median.append(subtract_median_box)
            self.line_width.append(line_width_box)
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

    def _on_label_edited(self, channel_config, chan_idx):
        """Handle a channel rename.

        A rename does not change a single sample, so re-filtering and
        re-referencing the whole recording (what signalRebuildNeeded triggers) is
        pure waste — and it used to run on *every keystroke*.  All that actually
        has to happen is that the places storing a channel *name* follow the new
        one: the other channels' Re_reference, the spectrogram/wavelet/periodogram
        selectors, and the re-reference dropdown items.  That is cheap and done
        immediately; the GUI refresh is debounced into a single emit.
        """
        new_name = self.label[chan_idx].text()
        old_name = self._known_names[chan_idx] if chan_idx < len(self._known_names) else new_name
        if old_name == new_name:
            return

        channel_config[chan_idx]["Channel_name"] = new_name
        self._known_names[chan_idx] = new_name

        # Only re-point name references if no other channel still carries the old
        # name — otherwise those references still resolve to that other channel.
        # (A derived channel starts out sharing its source channel's name.)
        if old_name and not any(c["Channel_name"] == old_name for c in channel_config):
            for c in channel_config:
                if c.get("Re_reference", "None") == old_name:
                    c["Re_reference"] = new_name
            if self.general_config is not None:
                for key in ("Channel_for_spectogram", "Wavelet_channel", "Periodogram_channel"):
                    if self.general_config.get(key) == old_name:
                        self.general_config[key] = new_name

        # Keep the re-reference dropdowns on the current names, so a later
        # unrelated edit cannot write a stale name back into the config.
        all_names = [lb.text() for lb in self.label]
        for k in range(len(self.reref)):
            current = channel_config[k].get("Re_reference", "None")
            self.reref[k].blockSignals(True)
            self._rebuild_reref_combo(k, all_names)
            self.reref[k].setCurrentText(current)
            self.reref[k].blockSignals(False)

        self._rename_pending = True
        self._rename_timer.start()

    def _emit_rename(self):
        """Fire the coalesced rename and clear the pending flag."""
        self._rename_pending = False
        self.channelRenamed.emit()

    def flush_pending_rename(self):
        """Emit a rename that is still waiting in the debounce timer.

        A rename is coalesced into one delayed emit; if the window is closed (or
        another feature opened) before that 300 ms elapses, the emit — and with
        it the rebuild of ui.channel_name_to_idx — would be lost, so downstream
        features (Autoscore, the spectrogram/wavelet channel pickers, ...) would
        fail to resolve the renamed channel. Call this to make it take effect now.
        """
        if self._rename_pending or self._rename_timer.isActive():
            self._rename_timer.stop()
            self._emit_rename()

    def _propagate_to_all(self, chan_idx, prop):
        """Copy channel chan_idx's value of prop to every row without re-emitting the
        rows' change signals. Returns False if prop is not shared (e.g. re-reference)."""
        widgets = {
            "scale": self.scale,
            "shift": self.shift,
            "color": self.color,
            "flip": self.flip,
            "subtract_median": self.subtract_median,
            "line_width": self.line_width,
        }.get(prop)
        if widgets is None:
            return False
        source = widgets[chan_idx]
        for w in widgets:
            w.blockSignals(True)
            if isinstance(w, QComboBox):
                w.setCurrentText(source.currentText())
            elif isinstance(w, QCheckBox):
                w.setChecked(source.isChecked())
            else:
                w.setValue(source.value())
            w.blockSignals(False)
        return True

    def change_event(self, channel_config, chan_idx=None, prop=None):
        propagated = (
            self.apply_all_checkbox.isChecked()
            and chan_idx is not None
            and self._propagate_to_all(chan_idx, prop)
        )
        for counter, chaninfo in enumerate(channel_config):
            chaninfo["Channel_name"] = self.label[counter].text()
            chaninfo["Channel_color"] = self.color[counter].currentText()
            chaninfo["Display_on_screen"] = self.display[counter].isChecked()
            chaninfo["Scaling_factor"] = int(self.scale[counter].value())
            chaninfo["Vertical_shift"] = int(self.shift[counter].value())
            chaninfo["Re_reference"] = self.reref[counter].currentText()
            chaninfo["Flip_polarity"] = self.flip[counter].isChecked()
            chaninfo["Subtract_median"] = self.subtract_median[counter].isChecked()
            chaninfo["Line_width"] = self.line_width[counter].value()
        # Display-only props: only a cheap redraw needed.
        # Signal props (reref, flip): need to rebuild eeg_data_display, but
        # spectrogram recomputation is only needed if this channel feeds the spectrogram
        # or wavelet panel — caller decides via the emitted index (-1: all channels).
        # Renames never reach here; they go through _on_label_edited instead.
        display_only_props = {"display", "color", "scale", "shift", "subtract_median", "line_width"}
        signal_rebuild_props = {"reref", "flip"}
        if prop in display_only_props:
            self.displayOnlyChanged.emit()
        elif prop in signal_rebuild_props:
            self.signalRebuildNeeded.emit(-1 if propagated or chan_idx is None else chan_idx)
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
                             self.subtract_median, self.line_width, self.number_labels, self.trash_buttons]:
            moved_widget = widget_list.pop(src_start)
            widget_list.insert(new_pos, moved_widget)

        # Update the displayed position numbers to reflect the new order
        for i, lbl in enumerate(self.number_labels):
            lbl.setText(str(i + 1))

        # Names move with their rows
        self._known_names = [lb.text() for lb in self.label]

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
