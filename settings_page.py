from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QComboBox, QPushButton, QHBoxLayout

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
        self.has_changes = False
        self.original_lang = "(None)"
        self.original_model = ""

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20,20,20,20)
        
        # ----------------------
        # LANGUAGE SELECTOR
        # ----------------------
        layout.addWidget(QLabel("Force response language:"))
        self.lang_combo = QComboBox()
        self.lang_combo.addItem("(None)")
        self.lang_combo.addItems(LANGUAGES)
        layout.addWidget(self.lang_combo)
        
        # ----------------------
        # MODEL SELECTOR
        # ----------------------
        layout.addSpacing(20)
        layout.addWidget(QLabel("LLM Model (Ollama): "))
        self.model_combo = QComboBox()
        layout.addWidget(self.model_combo)

        layout.addStretch()
        
        # ----------------------
        # ACTION BUTTONS
        # ----------------------
        self.actions_widget = QWidget()
        actions_layout = QHBoxLayout(self.actions_widget)
        actions_layout.setContentsMargins(0,0,0,0)
        actions_layout.addStretch()
        
        self.cancel_button = QPushButton("Cancel")
        self.accept_button = QPushButton("Accept")
        
        actions_layout.addWidget(self.cancel_button)
        actions_layout.addWidget(self.accept_button)
        
        layout.addWidget(self.actions_widget)

        # Load initial state and connect signals
        self.load_and_set_initial_state()

        self.lang_combo.currentTextChanged.connect(self.check_for_changes)
        self.model_combo.currentTextChanged.connect(self.check_for_changes)
        
        self.accept_button.clicked.connect(self.apply_changes)
        self.cancel_button.clicked.connect(self.discard_changes)

        self.actions_widget.hide()

    def load_and_set_initial_state(self):
        self.lang_combo.blockSignals(True)
        self.model_combo.blockSignals(True)

        from app import get_installed_models, CURRENT_MODEL, CURRENT_LANGUAGE
        models = get_installed_models()
        if not models:
            models = ["No models found"]
        
        self.model_combo.clear()
        self.model_combo.addItems(models)
        
        self.original_model = CURRENT_MODEL if CURRENT_MODEL in models else models[0]
        self.model_combo.setCurrentText(self.original_model)

        self.original_lang = CURRENT_LANGUAGE if CURRENT_LANGUAGE else "(None)"
        self.lang_combo.setCurrentText(self.original_lang)

        self.lang_combo.blockSignals(False)
        self.model_combo.blockSignals(False)

        self.has_changes = False
        self.actions_widget.hide()

    def check_for_changes(self):
        lang_changed = self.lang_combo.currentText() != self.original_lang
        model_changed = self.model_combo.currentText() != self.original_model
        
        self.has_changes = lang_changed or model_changed
        self.actions_widget.setVisible(self.has_changes)

    def has_unsaved_changes(self):
        return self.has_changes

    # -------------------------------
    def apply_changes(self):
        from app import set_language, set_model
        
        new_lang = self.lang_combo.currentText()
        set_language(None if new_lang == "(None)" else new_lang)
        
        new_model = self.model_combo.currentText()
        set_model(new_model)
        
        self.load_and_set_initial_state()

    def discard_changes(self):
        self.load_and_set_initial_state()