from PyQt6.QtWidgets import (
    QHBoxLayout, QVBoxLayout, QLabel, QLineEdit, QPushButton, QCheckBox,
    QComboBox, QSpinBox, QDoubleSpinBox, QSlider, QToolBox, QWidget, QGroupBox
)
from PyQt6.QtCore import Qt


class ControlsBuilder:
    def __init__(self):
        self.controls = {}

    def _create_container(self, layout):
        widget = QWidget()
        widget.setLayout(layout)
        return widget

    def build_grid_settings(self):
        layout = QVBoxLayout()
        
        # Row 1: Checkbox
        checkbox_grid = QCheckBox("Pokaż siatkę")
        checkbox_grid.setChecked(True)
        self.controls['checkbox_grid'] = checkbox_grid
        layout.addWidget(checkbox_grid)

        # Row 2: Size inputs
        size_layout = QHBoxLayout()
        w_in = QLineEdit("100")
        w_in.setFixedWidth(40)
        h_in = QLineEdit("100")
        h_in.setFixedWidth(40)
        self.controls['w_in'] = w_in
        self.controls['h_in'] = h_in
        
        size_layout.addWidget(QLabel("W:"))
        size_layout.addWidget(w_in)
        size_layout.addWidget(QLabel("H:"))
        size_layout.addWidget(h_in)
        size_layout.addStretch()
        layout.addLayout(size_layout)

        # Row 3: Cell Size Label
        layout.addWidget(QLabel("Rozmiar komórki:"))
        
        # Row 4: Spinbox + Unit
        cell_size_inputs = QHBoxLayout()
        
        cell_size_spin = QDoubleSpinBox()
        cell_size_spin.setRange(0.0001, 100000.0)
        cell_size_spin.setValue(100.0)
        cell_size_spin.setDecimals(4)
        self.controls['cell_size_spin'] = cell_size_spin
        cell_size_inputs.addWidget(cell_size_spin)
        
        unit_combo = QComboBox()
        unit_combo.addItems(["m", "km"])
        unit_combo.setMinimumWidth(60) # Fix cutoff
        self.controls['unit_combo'] = unit_combo
        cell_size_inputs.addWidget(unit_combo)
        
        layout.addLayout(cell_size_inputs)
        
        # Row 5: Real World Info
        real_dim_label = QLabel("Wymiary pola: -")
        self.controls['real_dim_label'] = real_dim_label
        layout.addWidget(real_dim_label)
        
        area_label = QLabel("Powierzchnia: -")
        self.controls['area_label'] = area_label
        layout.addWidget(area_label)

        # Row 3: Resize button
        b1 = QPushButton("Zmień rozmiar")
        self.controls['set_size_btn'] = b1
        layout.addWidget(b1)
        
        layout.addStretch()
        return self._create_container(layout)

    def build_sensor_tools(self):
        layout = QVBoxLayout()

        # Placing modes
        modes_layout = QHBoxLayout()
        
        b_sensor = QPushButton("Dodaj Czujnik")
        b_sensor.setCheckable(True)
        self.controls['add_sensor_btn'] = b_sensor
        modes_layout.addWidget(b_sensor)
        
        b_remove = QPushButton("Usuń Czujnik")
        b_remove.setCheckable(True)
        self.controls['remove_sensor_btn'] = b_remove
        modes_layout.addWidget(b_remove)
        
        layout.addLayout(modes_layout)

        # Auto place
        auto_place_layout = QHBoxLayout()
        
        lbl_count = QLabel("Liczba sensorów:")
        self.controls['lbl_sensor_count'] = lbl_count
        auto_place_layout.addWidget(lbl_count)
        
        spin_count = QSpinBox()
        spin_count.setMinimum(1)
        spin_count.setMaximum(200)
        spin_count.setValue(8)
        self.controls['sensor_count_spin'] = spin_count
        auto_place_layout.addWidget(spin_count)
        
        layout.addLayout(auto_place_layout)

        b_auto = QPushButton("Auto Rozmieszczenie")
        self.controls['auto_place_btn'] = b_auto
        layout.addWidget(b_auto)

        # Clear buttons
        clear_layout = QHBoxLayout()
        
        b_clear_results = QPushButton("Wyczyść Wyniki")
        self.controls['clear_sim_btn'] = b_clear_results
        clear_layout.addWidget(b_clear_results)

        b_clear = QPushButton("Wyczyść Wszystko")
        self.controls['clear_btn'] = b_clear
        clear_layout.addWidget(b_clear)
        
        layout.addLayout(clear_layout)

        # Data Management (Save/Load/Import)
        data_layout = QVBoxLayout()
        data_title = QLabel("Zarządzanie Danymi:")
        data_layout.addWidget(data_title)

        data_buttons_layout = QHBoxLayout()
        b_save = QPushButton("Zapisz")
        self.controls['save_sim_btn'] = b_save
        data_buttons_layout.addWidget(b_save)

        b_load = QPushButton("Wczytaj")
        self.controls['load_sim_btn'] = b_load
        data_buttons_layout.addWidget(b_load)
        data_layout.addLayout(data_buttons_layout)

        # Highlight Sensors Checkbox (Visual)
        checkbox_highlight = QCheckBox("Wyróżnij sensory (czerwony)")
        self.controls['checkbox_highlight_sensors'] = checkbox_highlight
        data_layout.addWidget(checkbox_highlight)

        b_import = QPushButton("Importuj Zanieczyszczenie")
        self.controls['import_csv_btn'] = b_import
        data_layout.addWidget(b_import)
        
        # Import hint label
        import_hint = QLabel("")
        import_hint.setObjectName("ImportHint")
        import_hint.setStyleSheet("font-style: italic; color: #4caf50; font-size: 11px;")
        import_hint.setWordWrap(True)
        import_hint.hide()
        self.controls['import_hint_label'] = import_hint
        data_layout.addWidget(import_hint)

        layout.addLayout(data_layout)

        layout.addStretch()
        return self._create_container(layout)

    def build_step_simulation(self):
        layout = QVBoxLayout()

        # Checkbox for Sensor Values
        checkbox_sensor_values = QCheckBox("Pokaż wartości sensorów")
        self.controls['checkbox_sensor_values'] = checkbox_sensor_values
        layout.addWidget(checkbox_sensor_values)

        # Checkbox for Data Coverage
        checkbox_data_coverage = QCheckBox("Pokaż pokrycie danych")
        self.controls['checkbox_data_coverage'] = checkbox_data_coverage
        layout.addWidget(checkbox_data_coverage)

        # Checkbox for True Source (CSV)
        checkbox_true_source = QCheckBox("Pokaż rzeczywiste źródło")
        self.controls['checkbox_true_source'] = checkbox_true_source
        layout.addWidget(checkbox_true_source)

        # Sub-checkbox for Error Vector
        checkbox_error_vector = QCheckBox("   ↳ Pokaż wektor błędu")
        checkbox_error_vector.setEnabled(False) # Enabled only when parent is checked
        self.controls['checkbox_error_vector'] = checkbox_error_vector
        layout.addWidget(checkbox_error_vector)

        # Wind Direction
        layout.addWidget(QLabel("Kompensacja wiatru (stopnie):"))
        
        wind_dir_layout = QHBoxLayout()
        
        # Dial for visual checking
        from PyQt6.QtWidgets import QDial
        wind_dial = QDial()
        wind_dial.setRange(0, 359)
        wind_dial.setNotchesVisible(True)
        wind_dial.setWrapping(True)
        wind_dial.setValue(270)  # 0° user angle = dial internal 270 (pointer right)
        wind_dial.setFixedWidth(50)
        wind_dial.setFixedHeight(50)
        self.controls['wind_dir_dial'] = wind_dial
        wind_dir_layout.addWidget(wind_dial)
        
        # Spinbox for precise input
        wind_dir_spin = QSpinBox()
        wind_dir_spin.setRange(0, 359)
        wind_dir_spin.setValue(0)
        wind_dir_spin.setSuffix("°")
        self.controls['wind_dir_spin'] = wind_dir_spin
        wind_dir_layout.addWidget(wind_dir_spin)
        
        layout.addLayout(wind_dir_layout)

        # Wind Strength
        layout.addWidget(QLabel("Siła wiatru:"))
        wind_strength_spin = QSpinBox()
        wind_strength_spin.setMinimum(0)
        wind_strength_spin.setMaximum(100)
        wind_strength_spin.setSuffix("%")
        wind_strength_spin.setValue(0)
        self.controls['wind_strength_spin'] = wind_strength_spin
        layout.addWidget(wind_strength_spin)
        
        # Wind Offset Info
        offset_label = QLabel("Przesunięcie: -")
        self.controls['wind_offset_label'] = offset_label
        layout.addWidget(offset_label)

        # Cycle Selector
        layout.addWidget(QLabel("Poziom klasyfikacji:"))
        cycle_combo = QComboBox()
        cycle_combo.addItems([
            "Poziom 1",
            "Poziom 2",
            "Poziom 3",
            "Poziom 4",
            "Suma Ważona"
        ])
        cycle_combo.setEnabled(False)
        self.controls['cycle_combo'] = cycle_combo
        layout.addWidget(cycle_combo)

        # Elapsed Time Label
        time_label = QLabel("Czas obliczeń: -")
        time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        time_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.controls['sim_time_label'] = time_label
        layout.addWidget(time_label)

        # Accuracy Analysis Stats
        stats_group = QGroupBox("Analiza Dokładności")
        stats_layout = QVBoxLayout()
        
        lbl_ec = QLabel("Błąd Klasyfikacji (Ec): -")
        lbl_ec.setWordWrap(True)
        lbl_ec.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.controls['lbl_error_classification'] = lbl_ec
        stats_layout.addWidget(lbl_ec)
        
        lbl_ea = QLabel("Błąd Dokładności (Ea): -")
        lbl_ea.setWordWrap(True)
        lbl_ea.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.controls['lbl_error_accuracy'] = lbl_ea
        stats_layout.addWidget(lbl_ea)
        
        lbl_rel = QLabel("Trafność (Relevance): -")
        lbl_rel.setWordWrap(True)
        lbl_rel.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.controls['lbl_relevance'] = lbl_rel
        stats_layout.addWidget(lbl_rel)

        lbl_es = QLabel("Błąd Szukania (Es): -")
        lbl_es.setWordWrap(True)
        lbl_es.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.controls['lbl_error_search'] = lbl_es
        stats_layout.addWidget(lbl_es)
        
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)

        # Run Button
        b_run = QPushButton("Uruchom Symulację")
        self.controls['run_sim_btn'] = b_run
        layout.addWidget(b_run)

        layout.addStretch()
        return self._create_container(layout)

    def build_slider_and_label(self):
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setMinimum(0)
        slider.setMaximum(0)
        self.controls['slider'] = slider

        label = QLabel("Krok: 0 | Wiatr: 0")
        self.controls['label'] = label

        return slider, label

    def build_all(self):
        toolbox = QToolBox()
        
        toolbox.addItem(self.build_grid_settings(), "Ustawienia Siatki")
        toolbox.addItem(self.build_sensor_tools(), "Edycja i Czujniki")
        toolbox.addItem(self.build_step_simulation(), "Symulacja Krokowa")
        
        # Set the first item as current
        toolbox.setCurrentIndex(0)
        
        return toolbox
