from PySide6.QtWidgets import *
from PySide6.QtCore import *
from app import query_knowledge


class ComparePage(QWidget):
    def __init__(self):
        super().__init__()
        self.active_documents = []

        layout = QVBoxLayout(self)

        # Active docs label
        self.docs_label = QLabel("Comparing: None")
        self.docs_label.setStyleSheet("font-weight:bold;")
        layout.addWidget(self.docs_label)

        # Chat
        self.chat = QTextEdit()
        self.chat.setReadOnly(True)
        layout.addWidget(self.chat)

        # Input
        self.input = QLineEdit()
        self.input.setPlaceholderText("Ask a comparative question…")
        self.input.returnPressed.connect(self.ask)
        layout.addWidget(self.input)

    def set_active_documents(self, files):
        self.active_documents = files
        self.docs_label.setText("Comparing: " + ", ".join(files))
        self.chat.clear()

    def ask(self):
        q = self.input.text().strip()
        if not q:
            return

        self.chat.append(f"🧑 {q}")

        try:
            answer, chunks = query_knowledge(q, self.active_documents)

            self.chat.append(f"🤖 {answer}\n")

            if chunks:
                self.chat.append("\n📚 Retrieved Context:\n")

                from collections import defaultdict
                grouped = defaultdict(list)

                for c in chunks:
                    grouped[c["file"]].append(c)

                for file, items in grouped.items():
                    self.chat.append(f"\n🔹 {file}")
                    self.chat.append("-" * 40)

                for c in items:
                    self.chat.append(f"(score: {c['score']:.4f})")
                    self.chat.append(c["content"])
                    self.chat.append("")

        except Exception as e:
            self.chat.append(f"❌ Error: {e}")

        self.input.clear()
