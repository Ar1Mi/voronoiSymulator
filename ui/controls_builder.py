from PyQt6.QtWidgets import (
    QHBoxLayout, QVBoxLayout, QLabel, QLineEdit, QPushButton, QCheckBox,
    QComboBox, QSpinBox, QDoubleSpinBox, QSlider
)
from PyQt6.QtCore import Qt


class ControlsBuilder:
    def __init__(self):
        self.controls = {}

    def build_controls1(self):
        layout = QHBoxLayout()

        checkbox_grid = QCheckBox("Pokaż siatkę")
        checkbox_grid.setChecked(True)
        self.controls['checkbox_grid'] = checkbox_grid
        layout.addWidget(checkbox_grid)

        w_in = QLineEdit("20")
        w_in.setFixedWidth(40)
        h_in = QLineEdit("20")
        h_in.setFixedWidth(40)
        self.controls['w_in'] = w_in
        self.controls['h_in'] = h_in
        layout.addWidget(QLabel("W:"))
        layout.addWidget(w_in)
        layout.addWidget(QLabel("H:"))
        layout.addWidget(h_in)

        b1 = QPushButton("Odnow rozmiar")
        layout.addWidget(b1)
        self.controls['set_size_btn'] = b1

        b2 = QPushButton("Czysty")
        b3 = QPushButton("Brudny")
        layout.addWidget(b2)
        layout.addWidget(b3)
        self.controls['clean_btn'] = b2
        self.controls['polluted_btn'] = b3

        b_auto = QPushButton("Auto")
        layout.addWidget(b_auto)
        self.controls['auto_place_btn'] = b_auto

        return layout

    def build_controls2(self):
        layout = QHBoxLayout()

        layout.addWidget(QLabel("Kierunek wiatru:"))

        wind_dir_combo = QComboBox()
        wind_dir_combo.addItems([
            "Wschód (→)",
            "Południowy wschód (↘)",
            "Południe (↓)",
            "Południowy zachód (↙)",
            "Zachód (←)",
            "Północny zachód (↖)",
            "Północ (↑)",
            "Północny wschód (↗)"
        ])
        self.controls['wind_dir_combo'] = wind_dir_combo
        layout.addWidget(wind_dir_combo)

        layout.addWidget(QLabel("Siła wiatru:"))
        wind_strength_spin = QSpinBox()
        wind_strength_spin.setMinimum(0)
        wind_strength_spin.setMaximum(5)
        wind_strength_spin.setValue(0)
        self.controls['wind_strength_spin'] = wind_strength_spin
        layout.addWidget(wind_strength_spin)

        layout.addStretch()

        b4 = QPushButton("Run")
        b5 = QPushButton("Wyczyść")
        layout.addWidget(b4)
        layout.addWidget(b5)
        self.controls['run_sim_btn'] = b4
        self.controls['clear_btn'] = b5

        return layout

    def build_controls3(self):
        layout = QHBoxLayout()

        checkbox_var_wind = QCheckBox("Zmienny wiatr")
        self.controls['checkbox_var_wind'] = checkbox_var_wind
        layout.addWidget(checkbox_var_wind)

        layout.addWidget(QLabel("Min:"))
        min_wind_spin = QSpinBox()
        min_wind_spin.setMinimum(0)
        min_wind_spin.setMaximum(5)
        min_wind_spin.setValue(0)
        min_wind_spin.setEnabled(False)
        self.controls['min_wind_spin'] = min_wind_spin
        layout.addWidget(min_wind_spin)

        layout.addWidget(QLabel("Max:"))
        max_wind_spin = QSpinBox()
        max_wind_spin.setMinimum(0)
        max_wind_spin.setMaximum(5)
        max_wind_spin.setValue(5)
        max_wind_spin.setEnabled(False)
        self.controls['max_wind_spin'] = max_wind_spin
        layout.addWidget(max_wind_spin)

        layout.addWidget(QLabel("Tempo:"))
        change_rate_spin = QDoubleSpinBox()
        change_rate_spin.setMinimum(0.1)
        change_rate_spin.setMaximum(2.0)
        change_rate_spin.setSingleStep(0.1)
        change_rate_spin.setValue(0.5)
        change_rate_spin.setEnabled(False)
        self.controls['change_rate_spin'] = change_rate_spin
        layout.addWidget(change_rate_spin)

        layout.addStretch()

        run_realtime_btn = QPushButton("Uruchom RT")
        run_realtime_btn.setEnabled(False)
        self.controls['run_realtime_btn'] = run_realtime_btn
        layout.addWidget(run_realtime_btn)

        stop_realtime_btn = QPushButton("Stop RT")
        stop_realtime_btn.setEnabled(False)
        self.controls['stop_realtime_btn'] = stop_realtime_btn
        layout.addWidget(stop_realtime_btn)

        return layout

    def build_slider_and_label(self):
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setMinimum(0)
        slider.setMaximum(0)
        self.controls['slider'] = slider

        label = QLabel("Poziom: 0 | Wiatr: 0")
        self.controls['label'] = label

        return slider, label

    def build_all(self):
        layout = QVBoxLayout()
        layout.addLayout(self.build_controls1())
        layout.addLayout(self.build_controls2())
        layout.addLayout(self.build_controls3())
        return layout
