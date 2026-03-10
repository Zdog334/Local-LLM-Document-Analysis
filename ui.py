import sys

# Fix for PyInstaller --noconsole mode where sys.stdout is None
# This prevents crashes in libraries like 'transformers' that check sys.stdout.isatty()
if sys.stdout is None:
    class NullWriter:
        def write(self, text): pass
        def flush(self): pass
        def isatty(self): return False
    sys.stdout = NullWriter()
    sys.stderr = NullWriter()

from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *

from library_page import LibraryPage
from analysis_page import AnalysisPage
from compare_page import ComparePage
from settings_page import SettingsPage 
import os

# Import modules for background tasks
import app
import models

class InitWorker(QObject):
    """
    Worker to handle slow initialization tasks in the background.
    """
    log_message = Signal(str)
    finished = Signal()

    def run(self):
        self.log_message.emit("Pre-loading embedding model...")
        # This can be slow, so it runs in the background
        models._load_embedder()
        self.log_message.emit("✔ Embedding model ready.")
        self.finished.emit()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Local AI Document Studio")
        self.resize(1500,900)

        # Add a status bar for feedback early
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.show_status_message("Initializing...")
        QApplication.processEvents() # Allow UI to update

        root = QWidget()
        layout = QHBoxLayout(root)
        layout.setContentsMargins(0,0,0,0)

        self.sidebar = Sidebar()
        self.stack = QStackedWidget()

        # --- Synchronous Ollama Model Fetching ---
        self.show_status_message("Fetching Ollama models...")
        QApplication.processEvents()
        ollama_models = app.initialize_and_get_models()
        self.show_status_message("✔ Ollama models loaded.")

        self.library = LibraryPage()
        self.analysis = AnalysisPage()
        self.compare = ComparePage()
        self.settings = SettingsPage(ollama_models)

        self.library.document_selected.connect(self.open_document)

        self.stack.addWidget(self.library)
        self.stack.addWidget(self.analysis)
        self.stack.addWidget(self.compare)
        self.stack.addWidget(self.settings)

        self.sidebar.page_changed.connect(self.attempt_page_switch)

        layout.addWidget(self.sidebar, 1)
        layout.addWidget(self.stack, 6)

        self.setCentralWidget(root)

        # --- Background Initialization ---
        self.init_thread = QThread()
        self.init_worker = InitWorker()
        self.init_worker.moveToThread(self.init_thread)

        # Connect signals
        self.init_thread.started.connect(self.init_worker.run)
        self.init_worker.finished.connect(self.init_thread.quit)
        self.init_worker.finished.connect(self.init_worker.deleteLater)
        self.init_thread.finished.connect(self.init_thread.deleteLater)
        
        self.init_worker.log_message.connect(self.show_status_message)

        # Start the background work
        self.init_thread.start()


    def open_document(self, selected_files):
        if not selected_files:
            return

        # update sidebar selection to match the destination page
        if len(selected_files) == 1:
            self.sidebar.switch(1)  # Analysis button

            filename = selected_files[0]
            full_path = os.path.join("documents", filename)

            self.analysis.set_active_documents(selected_files)
            self.analysis.load_document(full_path)
        else:
            self.sidebar.switch(2)  # Compare button
            self.compare.set_active_documents(selected_files)

        self.library.clear_selection()

    def attempt_page_switch(self, target_index):
        current_index = self.stack.currentIndex()
        if current_index == target_index:
            return

        current_widget = self.stack.currentWidget()

        if current_widget == self.settings and self.settings.has_unsaved_changes():
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Unsaved Changes")
            msg_box.setText("You have unsaved changes. What would you like to do?")
            msg_box.setIcon(QMessageBox.Question)
            save_button = msg_box.addButton("Save", QMessageBox.AcceptRole)
            discard_button = msg_box.addButton("Discard", QMessageBox.DestructiveRole)
            cancel_button = msg_box.addButton("Cancel", QMessageBox.RejectRole)
            
            msg_box.exec()
            clicked_button = msg_box.clickedButton()

            if clicked_button == save_button:
                self.settings.apply_changes()
            elif clicked_button == discard_button:
                self.settings.discard_changes()
            else: # Cancel
                self.sidebar.set_active_button(current_index)
                return

        self.stack.setCurrentIndex(target_index)
        self.sidebar.set_active_button(target_index)

    def show_status_message(self, message):
        self.statusBar.showMessage(message, 5000) # Show for 5 seconds

class Sidebar(QWidget):
    page_changed = Signal(int)

    def __init__(self):
        super().__init__()
        self.setStyleSheet("background:#111; color:white")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10,10,10,10)

        title = QLabel("📚 Local AI")
        title.setStyleSheet("font-size:22px; font-weight:bold;")
        layout.addWidget(title)

        layout.addSpacing(20)

        self.buttons = []
        names = ["Library", "Analysis", "Compare", "Settings"]

        for i,name in enumerate(names):
            btn = QPushButton(name)
            btn.setCheckable(True)
            btn.setStyleSheet(self.style())
            btn.clicked.connect(lambda _,x=i: self.switch(x))
            self.buttons.append(btn)
            layout.addWidget(btn)

        self.buttons[0].setChecked(True)
        layout.addStretch()

    def switch(self, index):
        self.page_changed.emit(index)

    def set_active_button(self, index):
        for i, button in enumerate(self.buttons):
            button.blockSignals(True)
            button.setChecked(i == index)
            button.blockSignals(False)

    def style(self):
        return """
        QPushButton {
            padding:12px;
            border:none;
            text-align:left;
            font-size:14px;
        }
        QPushButton:checked {
            background:#333;
            border-left:4px solid #5ca9ff;
        }
        QPushButton:hover {
            background:#222;
        }
        """
        

if __name__ == "__main__":
    q_application = QApplication([])
    window = MainWindow()
    window.show()
    q_application.exec()