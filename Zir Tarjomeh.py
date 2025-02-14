import sys, os, time, json
from PyQt5 import QtWidgets, QtCore, QtGui
from gemini_srt_translator.main import GeminiSRTTranslator

class ModelSelectDialog(QtWidgets.QDialog):
    def __init__(self, api_key, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Model")
        self.setFixedWidth(400)
        layout = QtWidgets.QVBoxLayout(self)
        
        self.list_widget = QtWidgets.QListWidget(self)
        self.list_widget.setStyleSheet("""
            QListWidget {
                background-color: #333;
                border-radius: 4px;
                padding: 5px;
            }
            QListWidget::item {
                color: white;
                padding: 8px;
                border-bottom: 1px solid #444;
            }
            QListWidget::item:selected {
                background-color: #2196f3;
            }
        """)
        
        layout.addWidget(QtWidgets.QLabel("Available Models:"))
        layout.addWidget(self.list_widget)
        
        btn_layout = QtWidgets.QHBoxLayout()
        select_btn = QtWidgets.QPushButton("Select", self)
        cancel_btn = QtWidgets.QPushButton("Cancel", self)
        select_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(select_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        
        self.load_models(api_key)
        self.setStyleSheet(SettingsDialog.dialog_style)

    def load_models(self, api_key):
        try:
            translator = GeminiSRTTranslator(gemini_api_key=api_key)
            # Redirect stdout to capture models output
            from io import StringIO
            import sys
            old_stdout = sys.stdout
            sys.stdout = mystdout = StringIO()
            translator.listmodels()
            sys.stdout = old_stdout
            
            # Parse models from output
            models = [line.strip() for line in mystdout.getvalue().split('\n') 
                     if line.strip().startswith('gemini-')]
            
            self.list_widget.addItems(models)
            
            # Select current model
            settings = QtCore.QSettings("SubtitleTranslator", "Settings")
            current_model = settings.value("model", "gemini-2.0-flash")
            matching_items = self.list_widget.findItems(current_model, QtCore.Qt.MatchExactly)
            if matching_items:
                self.list_widget.setCurrentItem(matching_items[0])
            
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Error", f"Could not load models: {str(e)}")

    def selected_model(self):
        if self.list_widget.currentItem():
            return self.list_widget.currentItem().text()
        return None

class SettingsDialog(QtWidgets.QDialog):
    dialog_style = """
        QDialog {
            background-color: #2b2b2b;
            color: #ffffff;
        }
        QLabel {
            color: #ffffff;
        }
        QLineEdit {
            padding: 8px;
            border: 1px solid #555;
            border-radius: 4px;
            background-color: #333;
            color: #fff;
        }
        QPushButton {
            background-color: #0d47a1;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #1565c0;
        }
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setFixedWidth(400)
        layout = QtWidgets.QVBoxLayout(self)
        
        # API Key
        form = QtWidgets.QFormLayout()
        self.apiKeyEdit = QtWidgets.QLineEdit(self)
        form.addRow("API Key:", self.apiKeyEdit)
        layout.addLayout(form)
        
        # Output Location
        output_layout = QtWidgets.QHBoxLayout()
        self.output_path = QtWidgets.QLineEdit(self)
        self.output_path.setPlaceholderText("Same as input file location")
        browse_btn = QtWidgets.QPushButton("Browse", self)
        browse_btn.clicked.connect(self.browse_output)
        output_layout.addWidget(self.output_path)
        output_layout.addWidget(browse_btn)
        form.addRow("Output Location:", output_layout)
        
        # Model Selection
        model_layout = QtWidgets.QHBoxLayout()
        self.model_label = QtWidgets.QLabel("Current Model: ")
        self.model_value = QtWidgets.QLabel()
        model_btn = QtWidgets.QPushButton("Change Model", self)
        model_btn.clicked.connect(self.select_model)
        model_layout.addWidget(self.model_label)
        model_layout.addWidget(self.model_value)
        model_layout.addWidget(model_btn)
        layout.addLayout(model_layout)
        
        # Save Button
        saveBtn = QtWidgets.QPushButton("Save", self)
        saveBtn.clicked.connect(self.save_settings)
        layout.addWidget(saveBtn)
        
        self.load_settings()
        self.setStyleSheet(self.dialog_style)
    
    def browse_output(self):
        folder = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Select Output Directory", "",
            QtWidgets.QFileDialog.ShowDirsOnly | QtWidgets.QFileDialog.DontResolveSymlinks
        )
        if folder:
            self.output_path.setText(folder)
    
    def load_settings(self):
        settings = QtCore.QSettings("SubtitleTranslator", "Settings")
        self.apiKeyEdit.setText(settings.value("apiKey", ""))
        self.output_path.setText(settings.value("outputPath", ""))
        self.model_value.setText(settings.value("model", "gemini-2.0-flash"))
    
    def save_settings(self):
        settings = QtCore.QSettings("SubtitleTranslator", "Settings")
        settings.setValue("apiKey", self.apiKeyEdit.text().strip())
        settings.setValue("outputPath", self.output_path.text().strip())
        settings.setValue("model", self.model_value.text())
        self.accept()

    def select_model(self):
        api_key = self.apiKeyEdit.text().strip()
        dlg = ModelSelectDialog(api_key, self)
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            selected_model = dlg.selected_model()
            if selected_model:
                self.model_value.setText(selected_model)

class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Subtitle Translator")
        self.setMinimumSize(600, 400)
        
        # Main layout
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(20)
        
        # Header with logo and settings
        header = QtWidgets.QHBoxLayout()
        logo_label = QtWidgets.QLabel("🎬 Subtitle Translator")
        logo_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #fff;")
        header.addWidget(logo_label)
        
        settings_btn = QtWidgets.QPushButton("⚙️", self)
        settings_btn.setFixedSize(40, 40)
        settings_btn.clicked.connect(self.open_settings)
        header.addWidget(settings_btn)
        layout.addLayout(header)
        
        # Drop zone for files
        self.drop_zone = DropZone(self)
        layout.addWidget(self.drop_zone)
        
        # Replace single file label with list widget
        self.files_list = QtWidgets.QListWidget(self)
        self.files_list.setStyleSheet("""
            QListWidget {
                background-color: #2b2b2b;
                border-radius: 4px;
                padding: 5px;
            }
            QListWidget::item {
                color: white;
                padding: 4px;
                border-bottom: 1px solid #444;
            }
        """)
        layout.addWidget(self.files_list)
        
        # Add clear list button
        clear_btn = QtWidgets.QPushButton("Clear List", self)
        clear_btn.clicked.connect(self.clear_files)
        layout.addWidget(clear_btn)
        
        self.input_files = []  # Store multiple file paths
        
        # Translate button
        self.translate_btn = QtWidgets.QPushButton("Translate to Persian", self)
        self.translate_btn.clicked.connect(self.translate_file)
        layout.addWidget(self.translate_btn)
        
        # Progress bar (hidden by default)
        self.progress = QtWidgets.QProgressBar(self)
        self.progress.setVisible(False)
        layout.addWidget(self.progress)
        
        self.settings_dialog = None  # Add this line to store the dialog instance
        self.setup_style()
    
    def setup_style(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QPushButton {
                background-color: #2196f3;
                color: white;
                border: none;
                padding: 12px;
                border-radius: 6px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976d2;
            }
            QPushButton:pressed {
                background-color: #0d47a1;
            }
            QProgressBar {
                border: 2px solid #555;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #2196f3;
            }
        """)
    
    def open_settings(self):
        self.settings_dialog = SettingsDialog(self)
        self.settings_dialog.exec_()
    
    def clear_files(self):
        self.input_files.clear()
        self.files_list.clear()

    def translate_file(self):
        if not self.input_files:
            QtWidgets.QMessageBox.warning(self, "Error", "Please select files first!")
            return
            
        settings = QtCore.QSettings("SubtitleTranslator", "Settings")
        api_key = settings.value("apiKey")
        model = settings.value("model", "gemini-2.0-flash")
        output_path = settings.value("outputPath", "").strip()
        
        if not api_key:
            QtWidgets.QMessageBox.warning(self, "Error", "Please set your API key in settings!")
            return

        self.progress.setVisible(True)
        self.progress.setRange(0, len(self.input_files))
        self.progress.setValue(0)

        for i, input_file in enumerate(self.input_files):
            try:
                # Update progress
                self.progress.setValue(i)
                self.files_list.item(i).setForeground(QtGui.QColor("#ffeb3b"))  # Yellow - in progress
                
                # Determine output file location
                if output_path:
                    output_file = os.path.join(output_path, os.path.basename(input_file))
                    output_file = os.path.splitext(output_file)[0] + "_fa.srt"
                else:
                    output_file = os.path.splitext(input_file)[0] + "_fa.srt"
                
                translator = GeminiSRTTranslator(
                    gemini_api_key=api_key,
                    target_language="Persian",
                    input_file=input_file,
                    output_file=output_file,
                    model_name=model,
                    batch_size=30,
                    free_quota=True
                )
                
                translator.translate()
                self.files_list.item(i).setForeground(QtGui.QColor("#4caf50"))  # Green - success
                
            except Exception as e:
                self.files_list.item(i).setForeground(QtGui.QColor("#f44336"))  # Red - error
                QtWidgets.QMessageBox.critical(self, "Error", f"Error translating {os.path.basename(input_file)}: {str(e)}")
                continue

        self.progress.setValue(len(self.input_files))
        self.progress.setVisible(False)
        QtWidgets.QMessageBox.information(self, "Success", "Translation of all files complete!")

class DropZone(QtWidgets.QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(QtCore.Qt.AlignCenter)
        self.setText("\n\n🎬\nDrag & Drop SRT files here\nor click to browse")
        self.setStyleSheet("""
            QLabel {
                border: 2px dashed #555;
                border-radius: 10px;
                padding: 20px;
                background-color: #2b2b2b;
                font-size: 16px;
            }
            QLabel:hover {
                border-color: #2196f3;
                background-color: #333;
            }
        """)
        self.setMinimumSize(400, 200)
        self.setAcceptDrops(True)
        self.setCursor(QtCore.Qt.PointingHandCursor)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.browse_file()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        for file in files:
            self.handle_file(file)

    def browse_file(self):
        fnames, _ = QtWidgets.QFileDialog.getOpenFileNames(
            self, "Select SRT Files", "", "SRT Files (*.srt);;All Files (*)")
        for fname in fnames:
            self.handle_file(fname)

    def handle_file(self, file_path):
        if file_path.lower().endswith('.srt'):
            try:
                # Verify and convert file encoding if needed
                final_path = self.ensure_utf8_encoding(file_path)
                if final_path not in self.parent().input_files:
                    self.parent().input_files.append(final_path)
                    self.parent().files_list.addItem(os.path.basename(file_path))
            except Exception as e:
                QtWidgets.QMessageBox.warning(
                    self, 
                    "Error", 
                    f"Error processing file: {str(e)}"
                )
        else:
            QtWidgets.QMessageBox.warning(self, "Error", "Please select SRT files only!")

    def ensure_utf8_encoding(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                f.read()
            return file_path
        except UnicodeDecodeError:
            for encoding in ['utf-16', 'iso-8859-1', 'cp1252']:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                        output_path = file_path + '.utf8.srt'
                        with open(output_path, 'w', encoding='utf-8') as out:
                            out.write(content)
                        return output_path
                except UnicodeDecodeError:
                    continue
            raise Exception("Could not determine file encoding")

def main():
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("Fusion")  # Modern look
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
