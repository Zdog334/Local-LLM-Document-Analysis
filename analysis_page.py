from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *


from PySide6.QtPdf import QPdfDocument
from PySide6.QtPdfWidgets import QPdfView

import os
from app import query_knowledge


class AnalysisPage(QWidget):
    def __init__(self):
        super().__init__()
        self.active_documents = []

        main = QVBoxLayout(self)

        # -------------------------
        # TOOLBAR
        # -------------------------
        toolbar = QHBoxLayout()

        self.page_label = QLabel("Viewer")

        self.zoom_out = QPushButton("➖")
        self.zoom_in = QPushButton("➕")
        self.fit_width = QPushButton("Fit Width")
        self.fit_page = QPushButton("Fit Page")

        toolbar.addWidget(self.zoom_out)
        toolbar.addWidget(self.zoom_in)
        toolbar.addWidget(self.fit_width)
        toolbar.addWidget(self.fit_page)
        toolbar.addStretch()
        toolbar.addWidget(self.page_label)

        main.addLayout(toolbar)

        # -------------------------
        # VIEWERS
        # -------------------------
        self.viewer_stack = QStackedWidget()
        
        # PDF Viewer
        self.pdf_doc = QPdfDocument(self)
        self.pdf_view = QPdfView(self)
        self.pdf_view.setDocument(self.pdf_doc)
        self.pdf_view.setPageMode(QPdfView.MultiPage)

        # TXT Viewer
        self.text_viewer = QTextEdit()
        self.text_viewer.setReadOnly(True)
        self.text_viewer.setFont(QFont("Consolas", 10))
        
        self.viewer_stack.addWidget(self.pdf_view)
        self.viewer_stack.addWidget(self.text_viewer)
        
        # -------------------------
        # CHAT 
        # -------------------------
        self.chat = QTextEdit()
        self.chat.setReadOnly(True)

        self.input = QLineEdit()
        self.input.setPlaceholderText("Ask about the selected documents…")
        self.input.returnPressed.connect(self.ask)

        # -------------------------
        # SOURCES
        # -------------------------
        self.sources = QTextEdit()
        self.sources.setReadOnly(True)
        self.sources.setMaximumHeight(200)

        # -------------------------
        # SPLITTER
        # -------------------------
        splitter = QSplitter(Qt.Vertical)
        splitter.addWidget(self.viewer_stack)
        splitter.addWidget(self.chat)
        splitter.addWidget(self.sources)
        splitter.setSizes([500, 300, 200])

        main.addWidget(splitter)
        main.addWidget(self.input)

        # -------------------------
        # EVENTS
        # -------------------------
        self.zoom_in.clicked.connect(self.apply_zoom_in)
        self.zoom_out.clicked.connect(self.apply_zoom_out)
        self.fit_width.clicked.connect(lambda: self.pdf_view.setZoomMode(QPdfView.ZoomMode.FitToWidth))
        self.fit_page.clicked.connect(lambda: self.pdf_view.setZoomMode(QPdfView.ZoomMode.FitInView))

        self.navigator = self.pdf_view.pageNavigator()
        self.navigator.currentPageChanged.connect(self.update_page)
        
    # -------------------------
    # Zoom methods
    # ------------------------- 
    def apply_zoom_in(self):
        self.pdf_view.setZoomMode(QPdfView.ZoomMode.Custom)
        self.pdf_view.setZoomFactor(self.pdf_view.zoomFactor() * 1.2)
        
    def apply_zoom_out(self):
        self.pdf_view.setZoomMode(QPdfView.ZoomMode.Custom)
        self.pdf_view.setZoomFactor(self.pdf_view.zoomFactor() / 1.2)
        
    # -------------------------
    # Load document (Multi-format)
    # -------------------------
    def load_document(self, path):
        if not os.path.exists(path):
            return
        
        ext = os.path.splitext(path)[1].lower()
        
        if ext == ".pdf":
            self.viewer_stack.setCurrentIndex(0)
            self.pdf_doc.load(path)
            self.navigator = self.pdf_view.pageNavigator()
            self.navigator.jump(0, QPointF(0,0))
            self.update_page()
        
        elif ext in [".txt", ".md", ".py", ".log"]:
            self.viewer_stack.setCurrentIndex(1)
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    self.text_viewer.setPlainText(f.read())
                self.page_label.setText(f"File: {os.path.basename(path)}")
            except Exception as e:
                self.text_viewer.setPlainText(f"Error reading file: {e}")
                self.page_label.setText(f"Error loading {os.path.basename(path)}")
        else:
            self.chat.append(f"⚠ Format '{ext}' not supported for view.")

    # -------------------------
    # Update page indicator
    # -------------------------
    def update_page(self, *_):
        if self.viewer_stack.currentIndex() == 0:
            if self.pdf_doc.status() != QPdfDocument.Status.Ready:
                return
            total = self.pdf_doc.pageCount()
            current = self.navigator.currentPage() + 1
            self.page_label.setText(f"Page {current} / {total}")


    # -------------------------
    # Ask LLM
    # -------------------------
    def ask(self):
        q = self.input.text().strip()
        if not q:
            return

        self.chat.append(f"🧑 {q}")

        try:
            answer, chunks = query_knowledge(q, self.active_documents)
            self.chat.append(f"🤖 {answer}")

            # `query_knowledge` returns a list of dicts for retrieved passages.
            # Convert that list into a displayable string for the sources widget.
            if isinstance(chunks, list) and chunks:
                formatted = []
                for c in chunks:
                    formatted.append(f"<b>[{c.get('file', '?')}]</b> (score:{c.get('score', 0): .4f})<br>{c.get('content','')}")
                self.sources.setHtml("<br><br>".join(formatted)) 
            else:
                self.sources.clear()
                
        except Exception as e:
            self.chat.append(f"❌ Error: {e}")

        self.input.clear()
        
    def set_active_documents(self, paths):
        # This just sets the context for the LLM. The UI is responsible
        # for calling `load_document` to display the file.
        self.active_documents = [paths] if isinstance(paths, str) else paths
