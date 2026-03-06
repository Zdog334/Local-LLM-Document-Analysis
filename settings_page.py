from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QComboBox

# a small list of languages, expand as needed
LANGUAGES = [
    "English",
    "Español",
    "Français",
    "Deutsch",
    "中文",
    "日本語",
]


class SettingsPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20,20,20,20)

        layout.addWidget(QLabel("Force response language:"))
        self.lang_combo = QComboBox()
        self.lang_combo.addItem("(None)")
        self.lang_combo.addItems(LANGUAGES)
        layout.addWidget(self.lang_combo)
        layout.addStretch()

        # sync with global state
        from app import CURRENT_LANGUAGE
        if CURRENT_LANGUAGE in LANGUAGES:
            index = LANGUAGES.index(CURRENT_LANGUAGE) + 1
            self.lang_combo.setCurrentIndex(index)
        else:
            self.lang_combo.setCurrentIndex(0)

        self.lang_combo.currentTextChanged.connect(self.language_changed)

    def language_changed(self, text):
        from app import set_language
        if text == "(None)":
            set_language(None)
        else:
            set_language(text)
