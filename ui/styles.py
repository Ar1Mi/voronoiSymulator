def get_main_stylesheet():
    return """
        QMainWindow {
            background-color: #121212;
        }
        QWidget {
            color: #e0e0e0;
            font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            font-size: 14px;
        }
        QFrame#Sidebar {
            background-color: #1e1e1e;
            border-right: 1px solid #333;
        }
        QPushButton {
            background-color: #0d47a1;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #1565c0;
        }
        QPushButton:pressed {
            background-color: #0d47a1;
        }
        QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
            background-color: #2c2c2c;
            border: 1px solid #444;
            padding: 6px;
            color: white;
            border-radius: 4px;
        }
        QComboBox::drop-down {
            border: none;
        }
        QCheckBox {
            spacing: 8px;
        }
        QSlider::groove:horizontal {
            border: 1px solid #444;
            height: 6px;
            background: #2c2c2c;
            margin: 2px 0;
            border-radius: 3px;
        }
        QSlider::handle:horizontal {
            background: #2196f3;
            border: 1px solid #2196f3;
            width: 16px;
            height: 16px;
            margin: -5px 0;
            border-radius: 8px;
        }
        QLabel {
            color: #bdbdbd;
        }
        QToolBox::tab {
            background: #2c2c2c;
            border-radius: 4px;
            color: #bbb;
            font-weight: bold;
            padding: 5px;
        }
        QToolBox::tab:selected {
            background: #383838;
            color: white;
            font-style: italic;
        }
        QGraphicsView {
            border: none;
            background-color: #121212;
        }
    """
