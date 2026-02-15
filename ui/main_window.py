from PyQt6.QtWidgets import (
    QMainWindow, QVBoxLayout, QHBoxLayout, 
    QWidget, QMessageBox, QFileDialog, QInputDialog, QApplication, QFrame, QLabel,
    QProgressDialog
)
from PyQt6.QtCore import Qt, QTimer
from constants import DEFAULT_GRID_SIZE
from .controls_builder import ControlsBuilder
from .grid_renderer import GridRenderer
from .simulation_controller import SimulationController


# New Imports
from .styles import get_main_stylesheet
from .grid_input_handler import GridInputHandler
from .grid_viewport import GridViewport


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Symulator Voronoi (Full Screen)")
        
        # Set dark theme stylesheet
        self._apply_stylesheet()

        self.grid_width = DEFAULT_GRID_SIZE
        self.grid_height = DEFAULT_GRID_SIZE
        self.sensors = []
        self.wind_direction = 0
        self.wind_strength = 0
        self.show_grid = True
        self.show_sensor_values = False
        self.show_data_coverage = False
        self.show_true_source = False


        self.sim_controller = SimulationController(
            self.grid_width, self.grid_height, self.sensors,
            self.wind_direction, self.wind_strength
        )

        self.controls_builder = ControlsBuilder()
        
        # Renderer is now managed by Viewport, but we create it here or inside viewport
        # The Viewport takes a renderer.
        self.grid_renderer = GridRenderer(
            None, self.grid_width, self.grid_height
        )
        self.viewport = GridViewport(self.grid_renderer)
        self.input_handler = GridInputHandler(self)

        self.current_step = 0
        self.placing_mode = None

        self._init_ui()
        self._connect_signals()
        self.showMaximized()
        
        # Import tracking state
        self.import_source_path = None
        self.import_type = None # "csv" or "sim"
        self.is_data_modified = False

        # Delay initial update and fit to ensure geometry is ready
        QTimer.singleShot(100, self._update_and_fit)

    def _apply_stylesheet(self):
        self.setStyleSheet(get_main_stylesheet())

    def _init_ui(self):
        # We use self.viewport instead of creating a fresh QGraphicsView/Scene
        
        # Wire up event filter for grid interactions
        self.viewport.viewport().installEventFilter(self)
        
        # Use property for backward compatibility if needed, or just self.viewport.scene
        # self.scene = self.viewport.scene
        # self.view = self.viewport
        
        # For GridInputHandler compatibility which uses self.mw.view
        self.view = self.viewport

        # --- Sidebar ---
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(320)
        
        controls_layout = self.controls_builder.build_all()
        
        # Wrap controls in a layout for the sidebar
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(10, 20, 10, 20)
        sidebar_layout.setSpacing(15)
        
        sidebar_title = QLabel("PANEL STEROWANIA")
        sidebar_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #fff; margin-bottom: 10px;")
        sidebar_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        sidebar_layout.addWidget(sidebar_title)
        sidebar_layout.addWidget(controls_layout)
        
        # --- Main Content Area ---
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(10)

        # Viewport Container
        content_layout.addWidget(self.viewport, stretch=1)

        # Bottom Controls (Slider + Label)
        slider_container = QFrame()
        slider_container.setStyleSheet("background-color: #1e1e1e; border-radius: 10px; padding: 10px;")
        slider_layout = QVBoxLayout(slider_container)
        
        self.slider, self.label = self.controls_builder.build_slider_and_label()
        self.label.setStyleSheet("font-size: 16px; font-weight: bold; color: #2196f3;")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        slider_layout.addWidget(self.label)
        slider_layout.addWidget(self.slider)
        
        content_layout.addWidget(slider_container)

        # --- Final Layout ---
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        main_layout.addWidget(sidebar)
        main_layout.addWidget(content_widget)

        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    def _connect_signals(self):
        controls = self.controls_builder.controls

        controls['checkbox_grid'].stateChanged.connect(self._on_toggle_grid)
        controls['set_size_btn'].clicked.connect(self._on_set_grid_size)
        controls['set_size_btn'].clicked.connect(self._on_set_grid_size)
        controls['add_sensor_btn'].clicked.connect(lambda: self._on_set_place_mode("sensor"))
        controls['remove_sensor_btn'].clicked.connect(lambda: self._on_set_place_mode("remove"))
        controls['auto_place_btn'].clicked.connect(self._on_auto_place)
        
        # Wind Direction Connections
        # Sync Dial and SpinBox with inverted direction (counter-clockwise = increasing angle)
        # Dial internal: 0 = bottom, 270 = right. User angle: 0 = right.
        # QDial increases clockwise, but trig angles increase counter-clockwise.
        # Conversion: dial_internal = (270 - user_angle) % 360
        #             user_angle = (270 - dial_internal) % 360
        controls['wind_dir_dial'].valueChanged.connect(
            lambda v: controls['wind_dir_spin'].setValue((270 - v) % 360)
        )
        controls['wind_dir_spin'].valueChanged.connect(
            lambda v: controls['wind_dir_dial'].setValue((270 - v) % 360)
        )
        
        # Update simulation on change (only from spinbox, to avoid double triggers)
        controls['wind_dir_spin'].valueChanged.connect(self._on_wind_changed)

        controls['wind_strength_spin'].valueChanged.connect(self._on_wind_changed)
        controls['run_sim_btn'].clicked.connect(self._on_run_sim)
        controls['clear_sim_btn'].clicked.connect(self._on_clear_sim_results)
        controls['clear_btn'].clicked.connect(self._on_clear_all)

        controls['import_csv_btn'].clicked.connect(self._on_import_csv)
        controls['save_sim_btn'].clicked.connect(self._on_save_sim)
        controls['import_csv_btn'].clicked.connect(self._on_import_csv)
        controls['save_sim_btn'].clicked.connect(self._on_save_sim)
        controls['load_sim_btn'].clicked.connect(self._on_load_sim)
        
        # Real world inputs
        controls['cell_size_spin'].valueChanged.connect(self._update_real_world_info)
        controls['unit_combo'].currentIndexChanged.connect(self._update_real_world_info)
        controls['w_in'].textChanged.connect(self._update_real_world_info)
        controls['h_in'].textChanged.connect(self._update_real_world_info)
        
        # Also trigger update when wind changes
        controls['wind_strength_spin'].valueChanged.connect(self._update_real_world_info)

        controls['slider'].valueChanged.connect(self._on_slider_changed)
        controls['cycle_combo'].currentIndexChanged.connect(self._on_cycle_changed)
        controls['checkbox_sensor_values'].stateChanged.connect(self._on_toggle_sensor_values)
        controls['checkbox_data_coverage'].stateChanged.connect(self._on_toggle_data_coverage)
        controls['checkbox_true_source'].stateChanged.connect(self._on_toggle_true_source)
        controls['checkbox_error_vector'].stateChanged.connect(self._on_toggle_error_vector)

        
        self.sim_controller.sim_finished.connect(self._on_sim_finished)
        self.sim_controller.sim_error.connect(self._on_sim_error)
        self.sim_controller.sim_progress.connect(self._on_sim_progress)

    def _update_and_fit(self):
        self._update_view()
        self._fit_grid_to_view()
        self._update_real_world_info()

    def _update_real_world_info(self):
        controls = self.controls_builder.controls
        
        try:
            w_str = controls['w_in'].text()
            h_str = controls['h_in'].text()
            w = int(w_str) if w_str else 0
            h = int(h_str) if h_str else 0
        except ValueError:
            w, h = 0, 0
            
        cell_size = controls['cell_size_spin'].value()
        unit = controls['unit_combo'].currentText()
        
        real_w = w * cell_size
        real_h = h * cell_size
        area = real_w * real_h
        
        controls['real_dim_label'].setText(f"Wymiary pola: {real_w:.2f} {unit} x {real_h:.2f} {unit}")
        controls['area_label'].setText(f"Powierzchnia: {area:.2f} {unit}²")
        
        # Wind offset
        strength_percent = controls['wind_strength_spin'].value()
        # Wind offset logic from simulation.py: (strength / 100) * max(w, h) in pixels
        # In real world units: (strength / 100) * max(real_w, real_h)
        # Assuming grid dimensions roughly map to physical space linearly.
        
        max_dim = max(real_w, real_h)
        offset_dist = (strength_percent / 100.0) * max_dim
        
        controls['wind_offset_label'].setText(f"Przesunięcie: {offset_dist:.2f} {unit}")

    def _fit_grid_to_view(self):
        self.viewport.fit_to_grid(self.grid_width, self.grid_height)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._fit_grid_to_view()

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(0, self._fit_grid_to_view)

    def _update_view(self):
        controls = self.controls_builder.controls
        cycle_idx = controls['cycle_combo'].currentIndex()
        
        grid_to_draw = None
        is_accumulated = False

        if self.sim_controller.cycle_results and controls['cycle_combo'].isEnabled():
            num_cycles = len(self.sim_controller.cycle_results)
            if cycle_idx < num_cycles:
                # On-the-fly calculation for steps
                grid_to_draw = self.sim_controller.get_cycle_grid(cycle_idx, self.current_step)
            else:
                grid_to_draw = self.sim_controller.accumulated_grid
                is_accumulated = True
        else:
            if self.sim_controller.sim and self.sim_controller.sim.steps:
                step = min(self.current_step, len(self.sim_controller.sim.steps) - 1)
                grid_to_draw = self.sim_controller.sim.steps[step]

        # Calculate used CSV indices if coverage overlay is enabled and CSV is loaded
        used_csv_indices = set()
        csv_grid = self.sim_controller.csv_grid
        max_source_pos = None
        
        if self.show_data_coverage and csv_grid:
            # Get max source pos for highlighting
            source_stats = self.sim_controller.get_max_pollution_source()
            if source_stats:
                max_source_pos = source_stats['pos']

            csv_height = len(csv_grid)
            csv_width = len(csv_grid[0]) if csv_height > 0 else 0
            if csv_width > 0 and csv_height > 0:
                for s in self.sensors:
                    cx = int(s.x * csv_width / self.grid_width)
                    cy = int(s.y * csv_height / self.grid_height)
                    cx = max(0, min(cx, csv_width - 1))
                    cy = max(0, min(cy, csv_height - 1))
                    used_csv_indices.add((cx, cy))

        # Get predicted centroid if error vector is enabled
        predicted_pos = None
        if self.controls_builder.controls['checkbox_error_vector'].isChecked():
             metrics = self.sim_controller.calculate_accuracy_metrics()
             if metrics and metrics.get('centroid'):
                 predicted_pos = metrics['centroid']

        self.viewport.update_view(
            grid_to_draw, self.show_grid, self.sensors, 
            is_accumulated=is_accumulated, show_values=self.show_sensor_values,
            csv_grid=csv_grid if self.show_data_coverage else None,
            used_csv_indices=used_csv_indices,
            max_source_pos=max_source_pos,
            true_source_pos=self.sim_controller.true_source_pos if self.show_true_source else None,
            predicted_pos=predicted_pos
        )

        
        # Sync scene rect just in case
        # (Managed by viewport now, but calling fit again if needed)
        # self.viewport.fit_to_grid(self.grid_width, self.grid_height)

    def _on_toggle_grid(self, state):
        self.show_grid = self.controls_builder.controls['checkbox_grid'].isChecked()
        self._update_view()

    def _on_toggle_sensor_values(self, state):
        self.show_sensor_values = self.controls_builder.controls['checkbox_sensor_values'].isChecked()
        self._update_view()

    def _on_toggle_data_coverage(self, state):
        self.show_data_coverage = self.controls_builder.controls['checkbox_data_coverage'].isChecked()
        self._update_view()

    def _on_toggle_true_source(self, state):
        is_checked = self.controls_builder.controls['checkbox_true_source'].isChecked()
        self.show_true_source = is_checked
        
        # Enable/Disable sub-checkbox
        self.controls_builder.controls['checkbox_error_vector'].setEnabled(is_checked)
        if not is_checked:
            self.controls_builder.controls['checkbox_error_vector'].setChecked(False)
            
        self._update_view()

    def _on_toggle_error_vector(self, state):
        self._update_view()


    def _on_set_place_mode(self, mode):
        # Toggle off if clicking the same mode
        if self.placing_mode == mode:
            self.placing_mode = None
        else:
            self.placing_mode = mode

        # Update button states
        controls = self.controls_builder.controls
        
        is_sensor = (self.placing_mode == "sensor")
        is_remove = (self.placing_mode == "remove")
        
        controls['add_sensor_btn'].setChecked(is_sensor)
        controls['remove_sensor_btn'].setChecked(is_remove)

    def _on_auto_place(self):
        count = self.controls_builder.controls['sensor_count_spin'].value()
        self.sim_controller.auto_place_sensors(count)
        self.sensors = self.sim_controller.sensors
        self.current_step = 0
        self.slider.setMaximum(0)
        self.slider.setValue(0)
        self.is_data_modified = False
        self._handle_data_modification(force_clear=True)
        self._update_and_fit()

    def _on_wind_changed(self):
        # directions = [0, 45, 90, 135, 180, 225, 270, 315]
        # self.wind_direction = directions[self.controls_builder.controls['wind_dir_combo'].currentIndex()]
        
        # New logic: read direct degrees
        self.wind_direction = self.controls_builder.controls['wind_dir_spin'].value()
        self.wind_strength = self.controls_builder.controls['wind_strength_spin'].value()
        self.sim_controller.update_wind(self.wind_direction, self.wind_strength)
        self._handle_data_modification()

    def _on_run_sim(self):
        self.placing_mode = None
        
        # Block controls
        self.controls_builder.controls['run_sim_btn'].setEnabled(False)
        self.controls_builder.controls['clear_sim_btn'].setEnabled(False)
        self.controls_builder.controls['clear_btn'].setEnabled(False)
        self.controls_builder.controls['cycle_combo'].setEnabled(False)
        
        # Setup Progress Dialog
        self.progress_dialog = QProgressDialog("Trwają obliczenia symulacji...", "Anuluj", 0, 100, self)
        self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress_dialog.setMinimumDuration(0) # Show immediately
        self.progress_dialog.setValue(0)
        self.progress_dialog.setCancelButton(None) # Disable cancel for now
        self.progress_dialog.show()
        
        self.sim_controller.run_async()

    def _on_sim_progress(self, val):
        if hasattr(self, 'progress_dialog') and self.progress_dialog:
            self.progress_dialog.setValue(val)

    def _on_sim_finished(self, cycle_results, accumulated_grid, accumulation_details, duration):
        if hasattr(self, 'progress_dialog') and self.progress_dialog:
             self.progress_dialog.close()
             self.progress_dialog = None
        
        self.controls_builder.controls['run_sim_btn'].setEnabled(True)
        self.controls_builder.controls['clear_sim_btn'].setEnabled(True)
        self.controls_builder.controls['clear_btn'].setEnabled(True)
        
        # Update time label
        self.controls_builder.controls['sim_time_label'].setText(f"Czas obliczeń: {duration:.4f} s")
        
        combo = self.controls_builder.controls['cycle_combo']
        combo.clear()
        
        num_cycles = len(cycle_results)
        for i in range(num_cycles):
            combo.addItem(f"Poziom {i + 1}")
        combo.addItem("Suma Ważona")
        
        combo.setEnabled(True)
        combo.setCurrentIndex(0)
        

        
        # Update accuracy stats (Dirtiest Sensor vs Most Polluted Area)
        metrics = self.sim_controller.calculate_accuracy_metrics()
        
        if metrics:
             ec = metrics['ec']
             ea = metrics['ea']
             rel = metrics['relevance']
             
             self.controls_builder.controls['lbl_error_classification'].setText(
                 f"Błąd Klasyfikacji (Ec): {ec:.4f}"
             )
             
             if ea is not None:
                 self.controls_builder.controls['lbl_error_accuracy'].setText(
                     f"Błąd Dokładności (Ea): {ea:.2f} px"
                 )
             else:
                 self.controls_builder.controls['lbl_error_accuracy'].setText("Błąd Dokładności (Ea): N/A (brak źródła)")
                 
             rel_text = "TAK (1)" if rel == 1 else "NIE (0)"
             if self.sim_controller.true_source_pos is None:
                 rel_text = "N/A (brak źródła)"
                 
             self.controls_builder.controls['lbl_relevance'].setText(
                 f"Trafność (Relevance): {rel_text}"
             )
             
             es = metrics.get('es')
             rank = metrics.get('source_rank')
             if es is not None:
                 rank_str = f" (Odnaleziono w: {rank})" if rank is not None else ""
                 self.controls_builder.controls['lbl_error_search'].setText(f"Błąd Szukania (Es): {es:.4f}{rank_str}")
             else:
                 self.controls_builder.controls['lbl_error_search'].setText("Błąd Szukania (Es): N/A (brak źródła)")
        else:
             self.controls_builder.controls['lbl_error_classification'].setText("Błąd Klasyfikacji (Ec): -")
             self.controls_builder.controls['lbl_error_accuracy'].setText("Błąd Dokładności (Ea): -")
             self.controls_builder.controls['lbl_relevance'].setText("Trafność (Relevance): -")
             self.controls_builder.controls['lbl_error_search'].setText("Błąd Szukania (Es): -")

             
        self._update_view()
        QMessageBox.information(self, "Symulacja", "Obliczenia zakończone.")

    def _on_sim_error(self, msg):
        if hasattr(self, 'progress_dialog') and self.progress_dialog:
             self.progress_dialog.close()
             self.progress_dialog = None
        self.controls_builder.controls['run_sim_btn'].setEnabled(True)
        self.controls_builder.controls['clear_sim_btn'].setEnabled(True)
        self.controls_builder.controls['clear_btn'].setEnabled(True)
        QMessageBox.critical(self, "Błąd Symulacji", f"Wystąpił błąd podczas symulacji:\n{msg}")

    def _on_import_csv(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Importuj dane CSV", "", "CSV Files (*.csv);;All Files (*)"
        )
        if file_name:
            try:
                self.slider.blockSignals(True)
                
                self.sim_controller.import_csv_data(file_name)
                self.sensors = self.sim_controller.sensors
                self.current_step = 0
                self.slider.setMaximum(0)
                self.slider.setValue(0)
                
                self.slider.blockSignals(False)
                
                self._update_and_fit()
                
                # Show import hint
                import os
                self.import_source_path = file_name
                self.import_type = "csv"
                self.is_data_modified = False
                self._update_import_hint_ui()

                self._update_import_hint_ui()

                self._update_import_hint_ui()

                # Clear accuracy metrics on import (require simulation run)
                self.controls_builder.controls['lbl_error_classification'].setText("Błąd Klasyfikacji (Ec): -")
                self.controls_builder.controls['lbl_error_accuracy'].setText("Błąd Dokładności (Ea): -")
                self.controls_builder.controls['lbl_relevance'].setText("Trafność (Relevance): -")
                self.controls_builder.controls['lbl_error_search'].setText("Błąd Szukania (Es): -")


                QApplication.processEvents()
                QMessageBox.information(self, "Sukces", "Dane z CSV zaimportowane pomyślnie.")
            except Exception as e:
                self.slider.blockSignals(False)
                QMessageBox.critical(self, "Błąd", f"Nie udało się заimportować CSV:\n{str(e)}")

    def _on_save_sim(self):
        file_name, _ = QFileDialog.getSaveFileName(
            self, "Zapisz Symulację", "", "JSON Files (*.json);;All Files (*)"
        )
        if file_name:
            if not file_name.endswith('.json'):
                file_name += '.json'
            try:
                self.sim_controller.save_simulation(file_name)
                QMessageBox.information(self, "Sukces", "Symulacja zapisana pomyślnie.")
            except Exception as e:
                QMessageBox.critical(self, "Błąd", f"Nie udało się zapisać symulacji:\n{str(e)}")

    def _on_load_sim(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Wczytaj Symulację", "", "JSON Files (*.json);;All Files (*)"
        )
        if file_name:
            try:
                self.slider.blockSignals(True)
                
                info = self.sim_controller.load_simulation(file_name)
                
                # Update UI elements
                controls = self.controls_builder.controls
                controls['w_in'].setText(str(info['grid_width']))
                controls['h_in'].setText(str(info['grid_height']))
                
                # Find wind direction index
                # directions = [0, 45, 90, 135, 180, 225, 270, 315]
                # try:
                #     wind_idx = directions.index(info['wind_direction'])
                #     controls['wind_dir_combo'].setCurrentIndex(wind_idx)
                # except ValueError:
                #     pass # Keep default if not found
                
                # New Logic: Set simple degrees
                wind_deg = info.get('wind_direction', 0)
                controls['wind_dir_spin'].setValue(int(wind_deg))
                    
                controls['wind_strength_spin'].setValue(int(info['wind_strength']))
                
                # Update internal state
                self.grid_width = info['grid_width']
                self.grid_height = info['grid_height']
                self.sensors = self.sim_controller.sensors
                self.wind_direction = info['wind_direction']
                self.wind_strength = info['wind_strength']
                
                # Update Renderer/Viewport
                self.grid_renderer.update_dimensions(self.grid_width, self.grid_height)
                
                # Reset simulation state
                self.current_step = 0
                self.slider.setMaximum(0)
                self.slider.setValue(0)
                controls['slider'].setEnabled(True)
                controls['cycle_combo'].setEnabled(False)
                
                self.slider.blockSignals(False)
                
                self._update_and_fit()
                
                # Show import hint
                import os
                self.import_source_path = file_name
                self.import_type = "sim"
                self.is_data_modified = False
                self._update_import_hint_ui()

                QMessageBox.information(self, "Sukces", "Symulacja wczytana pomyślnie.")
            except Exception as e:
                self.slider.blockSignals(False)
                QMessageBox.critical(self, "Błąd", f"Nie udało się wczytać symulacji:\n{str(e)}")


    def _update_import_hint_ui(self):
        hint_lbl = self.controls_builder.controls['import_hint_label']
        if not self.import_source_path:
            hint_lbl.hide()
            hint_lbl.setText("")
            return

        import os
        basename = os.path.basename(self.import_source_path)
        prefix = "Zaimportowano z" if self.import_type == "csv" else "Wczytano z"
        text = f"{prefix}: {basename}"
        
        if self.is_data_modified:
            text += " (zmieniono)"
            hint_lbl.setStyleSheet("font-style: italic; color: #ffeb3b; font-size: 11px;")
        else:
            hint_lbl.setStyleSheet("font-style: italic; color: #4caf50; font-size: 11px;")
        
        hint_lbl.setText(text)
        hint_lbl.show()

    def _handle_data_modification(self, force_clear=False):
        if force_clear:
            self.import_source_path = None
            self.import_type = None
            self.is_data_modified = False
            self._update_import_hint_ui()
            return

        if self.import_source_path and not self.is_data_modified:
            self.is_data_modified = True
            self._update_import_hint_ui()
        elif not self.import_source_path:
            # If no import, just hide (if it was somehow visible)
            self._update_import_hint_ui()

    def _on_cycle_changed(self):
        controls = self.controls_builder.controls
        cycle_idx = controls['cycle_combo'].currentIndex()
        
        if self.sim_controller.cycle_results:
            num_cycles = len(self.sim_controller.cycle_results)
            if cycle_idx < num_cycles:
                cycle_data = self.sim_controller.cycle_results[cycle_idx]
                max_step = cycle_data['step_count']
                
                controls['slider'].setEnabled(True)
                controls['slider'].setMaximum(max_step)
                
                # If we switched cycle, maybe reset to 0 or keep current step?
                # Usually better to reset or clamp.
                new_step = min(self.current_step, max_step)
                if new_step != self.current_step:
                     self.current_step = new_step
                     controls['slider'].setValue(new_step)
                else:
                    controls['slider'].setValue(new_step)
                    
                # Force update view immediately
                self._update_view()
            else:
                controls['slider'].setEnabled(False)
        
        self._update_view()

    def _on_clear_all(self):
        self.sim_controller.clear_sensors()
        self.current_step = 0
        self.slider.setMaximum(0)
        self.slider.setValue(0)
        self.controls_builder.controls['slider'].setEnabled(True)
        self.controls_builder.controls['slider'].setEnabled(True)
        self.controls_builder.controls['wind_dir_dial'].setEnabled(True)
        self.controls_builder.controls['wind_dir_spin'].setEnabled(True)
        self.controls_builder.controls['wind_strength_spin'].setEnabled(True)
        self.controls_builder.controls['cycle_combo'].setEnabled(False)
        self.controls_builder.controls['sim_time_label'].setText("Czas obliczeń: -")
        
        # Clear stats
        # Clear stats
        self.controls_builder.controls['lbl_error_classification'].setText("Błąd Klasyfikacji (Ec): -")
        self.controls_builder.controls['lbl_error_accuracy'].setText("Błąd Dokładności (Ea): -")
        self.controls_builder.controls['lbl_relevance'].setText("Trafność (Relevance): -")
        self.controls_builder.controls['lbl_error_search'].setText("Błąd Szukania (Es): -")

        
        self._handle_data_modification(force_clear=True)
        self._update_and_fit()

    def _on_clear_sim_results(self):
        self.sim_controller.clear_simulation_results()
        self.current_step = 0
        self.slider.setMaximum(0)
        self.slider.setValue(0)
        self.controls_builder.controls['slider'].setEnabled(True)
        self.controls_builder.controls['slider'].setEnabled(True)
        self.controls_builder.controls['wind_dir_dial'].setEnabled(True)
        self.controls_builder.controls['wind_dir_spin'].setEnabled(True)
        self.controls_builder.controls['wind_strength_spin'].setEnabled(True)
        self.controls_builder.controls['cycle_combo'].setEnabled(False)
        self.controls_builder.controls['sim_time_label'].setText("Czas obliczeń: -")
        
        # Clear sim stats only
        self.controls_builder.controls['lbl_error_classification'].setText("Błąd Klasyfikacji (Ec): -")
        self.controls_builder.controls['lbl_error_accuracy'].setText("Błąd Dokładności (Ea): -")
        self.controls_builder.controls['lbl_relevance'].setText("Trafność (Relevance): -")
        self.controls_builder.controls['lbl_error_search'].setText("Błąd Szukania (Es): -")

        
        self._handle_data_modification(force_clear=True)
        self._update_and_fit()

    def _on_slider_changed(self, v):
        self.current_step = v
        wind_str = f"{self.sim_controller.sim.wind_strength:.1f}" if hasattr(self.sim_controller.sim, 'wind_strength') else "0"
        self.label.setText(f"Krok: {v} | Wiatr: {wind_str}")
        self._update_view()

    def _on_set_grid_size(self):
        try:
            controls = self.controls_builder.controls
            w = int(controls['w_in'].text())
            h = int(controls['h_in'].text())
            if not (1 <= w <= 200 and 1 <= h <= 200):
                raise ValueError("Wymiary muszą być w zakresie 1-200.")
            self.grid_width, self.grid_height = w, h
            self.sim_controller.set_grid_size(w, h)
            self.sensors = self.sim_controller.sensors
            self.grid_renderer.update_dimensions(w, h)
            
            self.slider.setMaximum(0)
            self.slider.setValue(0)
            self.current_step = 0
            self.controls_builder.controls['slider'].setEnabled(True)
            self.controls_builder.controls['slider'].setEnabled(True)
            self.controls_builder.controls['wind_dir_dial'].setEnabled(True)
            self.controls_builder.controls['wind_dir_spin'].setEnabled(True)
            self.controls_builder.controls['wind_strength_spin'].setEnabled(True)
            self.controls_builder.controls['cycle_combo'].setEnabled(False)
            self._handle_data_modification()
            self._update_and_fit()
        except ValueError as e:
            QMessageBox.warning(self, "Error", str(e) if str(e) else "Liczby muszą być w zakresie 1-200.")

    def _open_edit_dialog(self, sensor):
        dialog = QInputDialog(self)
        dialog.setWindowTitle("Edytuj Wartość")
        dialog.setLabelText(f"Podaj wartość zanieczyszczenia (można użyć notation e, np. 1.23e-108):")
        dialog.setTextValue(f"{sensor.pollution_value:g}")
        
        if dialog.exec():
            val_str = dialog.textValue().replace(',', '.')
            try:
                val = float(val_str)
                self.sim_controller.update_sensor_value(sensor.x, sensor.y, val)
                self._handle_data_modification()
                self._update_view()
            except ValueError:
                QMessageBox.warning(self, "Błąd", "Nieprawidłowy format liczby.")



    def eventFilter(self, src, ev):
        return self.input_handler.eventFilter(src, ev)
