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
        # PDF TOOLBAR
        # -------------------------
        toolbar = QHBoxLayout()

        self.page_label = QLabel("Page 0 / 0")

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
        # PDF VIEW
        # -------------------------
        self.pdf_doc = QPdfDocument(self)
        self.pdf_view = QPdfView(self)
        self.pdf_view.setDocument(self.pdf_doc)

        self.pdf_view.setZoomMode(QPdfView.FitToWidth)
        self.pdf_view.setPageMode(QPdfView.MultiPage)

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
        splitter.addWidget(self.pdf_view)
        splitter.addWidget(self.chat)
        splitter.addWidget(self.sources)
        splitter.setSizes([500, 300, 200])

        main.addWidget(splitter)
        main.addWidget(self.input)

        # -------------------------
        # EVENTS
        # -------------------------
        self.zoom_in.clicked.connect(lambda: self.pdf_view.setZoomFactor(self.pdf_view.zoomFactor() * 1.2))
        self.zoom_out.clicked.connect(lambda: self.pdf_view.setZoomFactor(self.pdf_view.zoomFactor() / 1.2))
        self.fit_width.clicked.connect(lambda: self.pdf_view.setZoomMode(QPdfView.FitToWidth))
        self.fit_page.clicked.connect(lambda: self.pdf_view.setZoomMode(QPdfView.FitInView))

        self.navigator = self.pdf_view.pageNavigator()
        self.navigator.currentPageChanged.connect(self.update_page)
        

    # -------------------------
    # Load document
    # -------------------------
    def load_document(self, path):
        self.pdf_doc.load(path)
        self.pdf_view.setDocument(self.pdf_doc)
        
        self.navigator = self.pdf_view.pageNavigator()
        self.navigator.jump(0, QPointF(0,0))
        
        self.update_page()

    # -------------------------
    # Update page indicator
    # -------------------------
    def update_page(self, *_):
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
            if isinstance(chunks, list):
                if chunks:
                    formatted = []
                    for c in chunks:
                        formatted.append(
                            f"[{c['file']}] (score: {c['score']:.4f})\n{c['content']}"
                        )
                    self.sources.setText("\n\n".join(formatted))
                else:
                    # empty list, just clear
                    self.sources.clear()
            else:
                # fallback to whatever was returned
                self.sources.setText(str(chunks))

        except Exception as e:
            self.chat.append(f"❌ Error: {e}")

        self.input.clear()
    def set_active_documents(self, paths):
        if isinstance(paths, str):
            self.active_documents = [paths]
        else:
            self.active_documents = paths
