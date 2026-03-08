from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *
import os, shutil

from ingest import ingest_file, VECTOR_DIR


class LibraryPage(QWidget):
    document_selected = Signal(list)

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20,20,20,20)

        # Top bar
        top = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search documents…")
        self.search.textChanged.connect(self.filter)

        self.import_btn = QPushButton("➕ Import")
        self.import_btn.clicked.connect(self.import_docs)
        
        self.compare_btn = QPushButton("⚖ Compare Selected")
        self.compare_btn.clicked.connect(self.compare_selected)

        self.delete_btn = QPushButton("🗑 Delete")
        self.delete_btn.clicked.connect(self.delete_docs)

        top.addWidget(self.compare_btn)
        top.addWidget(self.delete_btn)
        top.addWidget(self.search)
        top.addWidget(self.import_btn)

        layout.addLayout(top)

        # Grid
        self.grid = QListWidget()
        self.grid.setViewMode(QListView.IconMode)
        self.grid.setIconSize(QSize(140,180))
        self.grid.setResizeMode(QListWidget.Adjust)
        # prevent the user from dragging/reordering items; keep a consistent grid
        self.grid.setMovement(QListView.Static)
        self.grid.setDragDropMode(QAbstractItemView.NoDragDrop)
        self.grid.setSelectionMode(QAbstractItemView.MultiSelection)
        self.grid.itemDoubleClicked.connect(self.open)

        self.grid.setStyleSheet("""
            QListWidget::item {
                margin:12px;
                padding:10px;
                border-radius:8px;
                background:#1e1e1e;
                color:white;
            }
            QListWidget::item:selected {
                background:#5ca9ff;
                color:black;
            }
        """)

        layout.addWidget(self.grid)

        self.load_library()

    # -----------------------------
    # Import
    # -----------------------------
    def import_docs(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Import", "", "PDF (*.pdf);;Text (*.txt)")
        os.makedirs("documents", exist_ok=True)
        
        if not files:
            return
        
        os.makedirs("documents", exist_ok=True)

        for src in files:
            name = os.path.basename(src)
            dst = os.path.join("documents", name)
            
            shutil.copy(src, dst)
            ingest_file(dst)

        self.load_library()


    # -----------------------------
    # Load
    # -----------------------------
    def load_library(self):
        self.grid.clear()
        os.makedirs("documents", exist_ok=True)
        
        for f in sorted(os.listdir("documents")):
            item = QListWidgetItem(QIcon("pdf.png"), f)
            item.setData(Qt.UserRole, f)
            self.grid.addItem(item)
    # -----------------------------
    # Filtering
    # -----------------------------
    def filter(self, text):
        for i in range(self.grid.count()):
            item = self.grid.item(i)
            item.setHidden(text.lower() not in item.text().lower())

    # -----------------------------
    # Open
    # -----------------------------
    def open(self, item):
        filename = item.data(Qt.UserRole)
        self.document_selected.emit([filename])
    
    # -----------------------------
    # Compare
    # -----------------------------
        
    def compare_selected(self):
        selected = self.grid.selectedItems()
        if len(selected) < 2:
            QMessageBox.warning(self, "Compare", "Select at least two documents.")
            return

        files = [item.data(Qt.UserRole) for item in selected]
        self.document_selected.emit(files)

    def delete_docs(self):
        selected = self.grid.selectedItems()
        if not selected:
            return
        
        if QMessageBox.question(self, "Delete", f"Delete {len(selected)} document(s)?") != QMessageBox.Yes:
            return

        for item in selected:
            filename = item.data(Qt.UserRole)
            
            # Remove source file
            doc_path = os.path.join("documents", filename)
            if os.path.exists(doc_path):
                os.remove(doc_path)
            
            # Remove index files
            index_path = os.path.join(VECTOR_DIR, f"{filename}.index")
            json_path = os.path.join(VECTOR_DIR, f"{filename}.json")
            
            if os.path.exists(index_path):
                os.remove(index_path)
            if os.path.exists(json_path):
                os.remove(json_path)
        
        self.load_library()

    def clear_selection(self):
        self.grid.clearSelection()
