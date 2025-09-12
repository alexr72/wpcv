import sys
import requests
import json
import os
import html
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QTextEdit, QPushButton, 
                             QVBoxLayout, QHBoxLayout, QWidget, QSplitter, QLabel, 
                             QFileDialog, QComboBox, QStatusBar, QMessageBox, QListWidget,
                             QTabWidget, QListWidgetItem, QCheckBox, QMenuBar, QMenu, QInputDialog)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QSyntaxHighlighter, QTextCharFormat, QColor, QTextDocument, QTextCursor, QClipboard
import markdown

# Try to import docx for Word document support
try:
    import docx
    HAVE_DOCX = True
except ImportError:
    HAVE_DOCX = False

class DeepSeekWorker(QThread):
    response_received = pyqtSignal(str, str)  # response, conversation_id
    error_occurred = pyqtSignal(str)
    
    def __init__(self, api_key, messages, model="deepseek-chat", conversation_id=None):
        super().__init__()
        self.api_key = api_key
        self.messages = messages
        self.model = model
        self.conversation_id = conversation_id
        self.url = "https://api.deepseek.com/v1/chat/completions"
        
    def run(self):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": self.messages,
            "temperature": 0.7,
            "max_tokens": 4000
        }
        
        # Retry logic (3 attempts)
        for attempt in range(3):
            try:
                response = requests.post(self.url, headers=headers, json=payload, timeout=60)
                if response.status_code == 200:
                    result = response.json()
                    self.response_received.emit(result['choices'][0]['message']['content'], self.conversation_id)
                    return
                else:
                    if attempt == 2:  # Last attempt
                        self.error_occurred.emit(f"API Error: {response.status_code} - {response.text}")
                    continue
                    
            except requests.exceptions.Timeout:
                if attempt == 2:  # Last attempt
                    self.error_occurred.emit("Request timed out after 3 attempts. Please check your internet connection.")
                continue
                
            except Exception as e:
                self.error_occurred.emit(f"Request failed: {str(e)}")
                return

class DocumentProcessor:
    """Class to handle various document formats including Word documents"""
    
    @staticmethod
    def extract_text_from_file(file_path):
        """Extract text from various document formats"""
        ext = os.path.splitext(file_path)[1].lower()
        
        try:
            if ext in ['.txt', '.md', '.py', '.js', '.php', '.html', '.css']:
                return DocumentProcessor._read_text_file(file_path)
            elif ext == '.docx' and HAVE_DOCX:
                return DocumentProcessor._read_docx(file_path)
            elif ext == '.docx' and not HAVE_DOCX:
                return "DOCX support requires: pip install python-docx"
            else:
                return f"Unsupported file format: {ext}"
                       
        except Exception as e:
            return f"Error reading file: {str(e)}"
    
    @staticmethod
    def _read_text_file(file_path):
        """Read plain text files"""
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    
    @staticmethod
    def _read_docx(file_path):
        """Read DOCX files"""
        doc = docx.Document(file_path)
        full_text = []
        for paragraph in doc.paragraphs:
            full_text.append(paragraph.text)
        return '\n'.join(full_text)

class LanguageHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None, language="python"):
        super().__init__(parent)
        self.language = language
        self.highlighting_rules = []
        self.setup_rules()
        
    def setup_rules(self):
        # Updated colors for dark mode
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor(100, 150, 100))
        
        string_format = QTextCharFormat()
        string_format.setForeground(QColor(200, 200, 100))
        
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor(86, 156, 214))
        keyword_format.setFontWeight(QFont.Weight.Bold)
        
        # Language-specific rules
        if self.language == "python":
            keywords = [
                "def", "class", "return", "if", "else", "elif", "for", "while", 
                "import", "from", "as", "try", "except", "finally", "with", "lambda",
                "and", "or", "not", "in", "is", "None", "True", "False"
            ]
            for word in keywords:
                pattern = r"\b" + word + r"\b"
                self.highlighting_rules.append((pattern, keyword_format))
            
            self.highlighting_rules.append((r"#.*", comment_format))
            self.highlighting_rules.append((r'""".*?"""', comment_format))
            self.highlighting_rules.append((r"'''.*?'''", comment_format))
            
        elif self.language == "javascript":
            keywords = [
                "function", "var", "let", "const", "if", "else", "for", "while", 
                "return", "class", "import", "export", "from", "try", "catch", 
                "finally", "this", "new", "typeof", "instanceof", "true", "false", "null"
            ]
            for word in keywords:
                pattern = r"\b" + word + r"\b"
                self.highlighting_rules.append((pattern, keyword_format))
            
            self.highlighting_rules.append((r"//.*", comment_format))
            self.highlighting_rules.append((r"/\*.*?\*/", comment_format))
            
        elif self.language == "php":
            keywords = [
                "<?php", "?>", "function", "class", "if", "else", "for", "while", 
                "return", "echo", "print", "foreach", "as", "try", "catch", 
                "finally", "public", "private", "protected", "static", "const"
            ]
            for word in keywords:
                pattern = r"\b" + word + r"\b"
                self.highlighting_rules.append((pattern, keyword_format))
            
            self.highlighting_rules.append((r"#.*", comment_format))
            self.highlighting_rules.append((r"//.*", comment_format))
            self.highlighting_rules.append((r"/\*.*?\*/", comment_format))
            
        elif self.language == "html":
            tag_format = QTextCharFormat()
            tag_format.setForeground(QColor(150, 100, 200))
            self.highlighting_rules.append((r"<\/?[^>]+>", tag_format))
            
            self.highlighting_rules.append((r"<!--.*?-->", comment_format))
            
            attr_format = QTextCharFormat()
            attr_format.setForeground(QColor(200, 150, 100))
            self.highlighting_rules.append((r'\b\w+(?=\=)', attr_format))
            
        elif self.language == "css":
            prop_format = QTextCharFormat()
            prop_format.setForeground(QColor(200, 100, 150))
            self.highlighting_rules.append((r"\b[\w-]+(?=:)", prop_format))
            
            value_format = QTextCharFormat()
            value_format.setForeground(QColor(100, 150, 200))
            self.highlighting_rules.append((r":\s*[^;]+", value_format))
            
            selector_format = QTextCharFormat()
            selector_format.setForeground(QColor(150, 200, 100))
            self.highlighting_rules.append((r"[^{]+(?=\{)", selector_format))
            
            self.highlighting_rules.append((r"/\*.*?\*/", comment_format))
        
        self.highlighting_rules.append((r'".*?"', string_format))
        self.highlighting_rules.append((r"'.*?'", string_format))  # Fixed the extra quote here
    
    def highlightBlock(self, text):
        for pattern, format in self.highlighting_rules:
            from PyQt6.QtCore import QRegularExpression
            expression = QRegularExpression(pattern)
            iterator = expression.globalMatch(text)
            while iterator.hasNext():
                match = iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), format)

class ResponseHighlighter(QSyntaxHighlighter):
    """Highlighter for the response area to make code blocks more visible"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlighting_rules = []
        self.setup_rules()
        
    def setup_rules(self):
        # Code block formatting
        code_block_format = QTextCharFormat()
        code_block_format.setBackground(QColor(30, 30, 30))
        code_block_format.setForeground(QColor(200, 200, 200))
        code_block_format.setFontFamily("Consolas")
        code_block_format.setFontFixedPitch(True)
        
        # Add rule for code blocks (between ```)
        self.highlighting_rules.append((r"```.*?```", code_block_format))
    
    def highlightBlock(self, text):
        for pattern, format in self.highlighting_rules:
            from PyQt6.QtCore import QRegularExpression
            expression = QRegularExpression(pattern, QRegularExpression.PatternOption.DotMatchesEverythingOption)
            iterator = expression.globalMatch(text)
            while iterator.hasNext():
                match = iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), format)

class DeepSeekAssistant(QMainWindow):
    def __init__(self):
        super().__init__()
        self.api_key = None
        self.current_file = None
        self.current_language = "python"
        self.conversation_history = []
        self.current_conversation_id = None
        self.conversation_context = {}  # Store conversation contexts
        
        # Replace single document with multi-document support
        self.loaded_documents = {}  # Key: filename, Value: document content
        self.current_project_context = ""  # Will hold a summary of the loaded project
        
        self.initUI()
        self.load_settings()
        self.apply_dark_mode_styles()
        
    def apply_dark_mode_styles(self):
        dark_stylesheet = """
        QMainWindow, QWidget { background-color: #2b2b2b; color: #ffffff; border: none; }
        QTextEdit, QPlainTextEdit { background-color: #1e1e1e; color: #d4d4d4; border: 1px solid #3c3c3c; border-radius: 4px; padding: 5px; font-family: Consolas, 'Courier New', monospace; }
        QTextEdit:focus, QPlainTextEdit:focus { border: 1px solid #0078d4; }
        QPushButton { background-color: #0e639c; color: #ffffff; border: none; border-radius: 4px; padding: 8px 16px; font-weight: bold; }
        QPushButton:hover { background-color: #1177bb; }
        QPushButton:pressed { background-color: #0c547d; }
        QPushButton:disabled { background-color: #424242; color: #888888; }
        QComboBox { background-color: #1e1e1e; color: #d4d4d4; border: 1px solid #3c3c3c; border-radius: 4px; padding: 5px; min-width: 100px; }
        QComboBox:focus { border: 1px solid #0078d4; }
        QComboBox QAbstractItemView { background-color: #1e1e1e; color: #d4d4d4; selection-background-color: #0e639c; selection-color: #ffffff; border: 1px solid #3c3c3c; }
        QListWidget { background-color: #1e1e1e; color: #d4d4d4; border: 1px solid #3c3c3c; border-radius: 4px; alternate-background-color: #252525; }
        QListWidget::item:selected { background-color: #0e639c; color: #ffffff; }
        QListWidget::item:hover { background-color: #2a2d2e; }
        QTabWidget::pane { border: 1px solid #3c3c3c; background-color: #2b2b2b; }
        QTabBar::tab { background-color: #2d2d2d; color: #cccccc; padding: 8px 16px; border-top-left-radius: 4px; border-top-right-radius: 4px; border: 1px solid #3c3c3c; margin-right: 2px; }
        QTabBar::tab:selected { background-color: #1e1e1e; color: #ffffff; border-bottom-color: #1e1e1e; }
        QTabBar::tab:hover:!selected { background-color: #383838; }
        QLabel { color: #cccccc; background-color: transparent; }
        QStatusBar { background-color: #252525; color: #cccccc; border-top: 1px solid #3c3c3c; }
        QMenuBar { background-color: #2b2b2b; color: #cccccc; border-bottom: 1px solid #3c3c3c; }
        QMenuBar::item:selected { background-color: #0e639c; color: #ffffff; }
        QMenu { background-color: #2b2b2b; color: #cccccc; border: 1px solid #3c3c3c; }
        QMenu::item:selected { background-color: #0e639c; color: #ffffff; }
        QSplitter::handle { background-color: #3c3c3c; }
        QSplitter::handle:hover { background-color: #0078d4; }
        QCheckBox { color: #cccccc; }
        QCheckBox::indicator { width: 15px; height: 15px; }
        QCheckBox::indicator:unchecked { background-color: #1e1e1e; border: 1px solid #3c3c3c; }
        QCheckBox::indicator:checked { background-color: #0e639c; border: 1px solid #0e639c; }
        """
        self.setStyleSheet(dark_stylesheet)
        
    def initUI(self):
        self.setWindowTitle("DeepSeek Document & Code Assistant")
        self.setGeometry(100, 100, 1400, 900)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        left_tabs = QTabWidget()
        
        # Document/Code editor tab
        editor_tab = QWidget()
        editor_layout = QVBoxLayout(editor_tab)
        
        editor_toolbar = QHBoxLayout()
        self.open_btn = QPushButton("Upload Document")
        self.open_btn.clicked.connect(self.load_document)
        self.save_btn = QPushButton("Save File")
        self.save_btn.clicked.connect(self.save_file)
        
        self.language_select = QComboBox()
        self.language_select.addItems(["text", "python", "javascript", "php", "html", "css", "markdown"])
        self.language_select.currentTextChanged.connect(self.change_language)
        
        editor_toolbar.addWidget(self.open_btn)
        editor_toolbar.addWidget(self.save_btn)
        editor_toolbar.addWidget(QLabel("Language:"))
        editor_toolbar.addWidget(self.language_select)
        editor_toolbar.addStretch()
        
        editor_layout.addLayout(editor_toolbar)
        
        # Add document list widget
        docs_label = QLabel("Loaded Documents:")
        editor_layout.addWidget(docs_label)
        
        self.docsListWidget = QListWidget()
        self.docsListWidget.itemClicked.connect(self.show_selected_document)
        editor_layout.addWidget(self.docsListWidget)
        
        # Add document management buttons
        doc_buttons_layout = QHBoxLayout()
        self.clear_docs_btn = QPushButton("Clear All")
        self.clear_docs_btn.clicked.connect(self.clear_documents)
        self.remove_doc_btn = QPushButton("Remove Selected")
        self.remove_doc_btn.clicked.connect(self.remove_selected_document)
        
        doc_buttons_layout.addWidget(self.remove_doc_btn)
        doc_buttons_layout.addWidget(self.clear_docs_btn)
        editor_layout.addLayout(doc_buttons_layout)
        
        self.editor = QTextEdit()
        self.editor.setFont(QFont("Consolas", 10))
        self.editor.textChanged.connect(self.update_highlighter)
        editor_layout.addWidget(self.editor)
        
        left_tabs.addTab(editor_tab, "Document Editor")
        
        # Project context tab
        context_tab = QWidget()
        context_layout = QVBoxLayout(context_tab)
        
        context_label = QLabel("Project Context (Summarize your project here):")
        context_layout.addWidget(context_label)
        
        self.project_context_edit = QTextEdit()
        self.project_context_edit.setPlaceholderText("Describe your project, goals, and any important context here...")
        context_layout.addWidget(self.project_context_edit)
        
        update_context_btn = QPushButton("Update Project Context")
        update_context_btn.clicked.connect(self.update_project_context)
        context_layout.addWidget(update_context_btn)
        
        left_tabs.addTab(context_tab, "Project Context")
        
        left_layout.addWidget(left_tabs)
        
        # Right panel
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # API key input
        api_layout = QHBoxLayout()
        api_layout.addWidget(QLabel("API Key:"))
        self.api_key_input = QTextEdit()
        self.api_key_input.setMaximumHeight(30)
        self.api_key_input.setPlaceholderText("Enter your DeepSeek API key here")
        api_layout.addWidget(self.api_key_input)
        
        self.save_key_btn = QPushButton("Save Key")
        self.save_key_btn.clicked.connect(self.save_api_key)
        api_layout.addWidget(self.save_key_btn)
        
        right_layout.addLayout(api_layout)
        
        # Model selection
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("Model:"))
        self.model_select = QComboBox()
        self.model_select.addItems(["deepseek-chat", "deepseek-coder"])
        model_layout.addWidget(self.model_select)
        
        self.conversation_select = QComboBox()
        self.conversation_select.addItem("New Conversation")
        self.conversation_select.currentTextChanged.connect(self.switch_conversation)
        model_layout.addWidget(QLabel("Conversation:"))
        model_layout.addWidget(self.conversation_select)
        
        self.delete_conversation_btn = QPushButton("Delete Conversation")
        self.delete_conversation_btn.clicked.connect(self.delete_conversation)
        model_layout.addWidget(self.delete_conversation_btn)
        
        right_layout.addLayout(model_layout)
        
        # Prompt input
        prompt_layout = QVBoxLayout()
        prompt_layout.addWidget(QLabel("Your Prompt:"))
        
        self.prompt_input = QTextEdit()
        self.prompt_input.setMaximumHeight(100)
        self.prompt_input.setPlaceholderText("Enter your prompt here...")
        prompt_layout.addWidget(self.prompt_input)
        
        prompt_buttons_layout = QHBoxLayout()
        
        self.include_context_check = QCheckBox("Include Project Context")
        self.include_context_check.setChecked(True)
        prompt_buttons_layout.addWidget(self.include_context_check)
        
        self.include_document_check = QCheckBox("Include Selected Document")
        self.include_document_check.setChecked(True)
        prompt_buttons_layout.addWidget(self.include_document_check)
        
        prompt_buttons_layout.addStretch()
        
        self.send_btn = QPushButton("Send to DeepSeek")
        self.send_btn.clicked.connect(self.send_to_deepseek)
        prompt_buttons_layout.addWidget(self.send_btn)
        
        prompt_layout.addLayout(prompt_buttons_layout)
        right_layout.addLayout(prompt_layout)
        
        # Response area
        response_layout = QVBoxLayout()
        response_layout.addWidget(QLabel("DeepSeek Response:"))
        
        self.response_output = QTextEdit()
        self.response_output.setReadOnly(True)
        self.response_output.setFont(QFont("Consolas", 10))
        response_layout.addWidget(self.response_output)
        
        # Add response highlighter
        self.response_highlighter = ResponseHighlighter(self.response_output.document())
        
        response_buttons_layout = QHBoxLayout()
        
        self.copy_btn = QPushButton("Copy Response")
        self.copy_btn.clicked.connect(self.copy_response)
        response_buttons_layout.addWidget(self.copy_btn)
        
        self.clear_response_btn = QPushButton("Clear Response")
        self.clear_response_btn.clicked.connect(self.clear_response)
        response_buttons_layout.addWidget(self.clear_response_btn)
        
        response_buttons_layout.addStretch()
        
        response_layout.addLayout(response_buttons_layout)
        right_layout.addLayout(response_layout)
        
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([500, 900])
        
        main_layout.addWidget(splitter)
        
        # Add status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
        # Initialize highlighter
        self.highlighter = LanguageHighlighter(self.editor.document(), self.current_language)
        
        # Create menu bar
        self.create_menu_bar()
        
    def create_menu_bar(self):
        menu_bar = QMenuBar(self)
        self.setMenuBar(menu_bar)
        
        # File menu
        file_menu = menu_bar.addMenu("File")
        
        new_action = file_menu.addAction("New Conversation")
        new_action.triggered.connect(self.new_conversation)
        
        save_action = file_menu.addAction("Save Conversation")
        save_action.triggered.connect(self.save_conversation)
        
        load_action = file_menu.addAction("Load Conversation")
        load_action.triggered.connect(self.load_conversation)
        
        file_menu.addSeparator()
        
        exit_action = file_menu.addAction("Exit")
        exit_action.triggered.connect(self.close)
        
        # Edit menu
        edit_menu = menu_bar.addMenu("Edit")
        
        clear_action = edit_menu.addAction("Clear All")
        clear_action.triggered.connect(self.clear_all)
        
        # Settings menu
        settings_menu = menu_bar.addMenu("Settings")
        
        token_action = settings_menu.addAction("Set Token Limit")
        token_action.triggered.connect(self.set_token_limit)
        
    def set_token_limit(self):
        current_limit = self.settings.get("max_tokens", 4000)
        new_limit, ok = QInputDialog.getInt(
            self, "Set Token Limit", 
            "Maximum tokens per response (lower values prevent truncation):", 
            current_limit, 100, 8000, 100
        )
        
        if ok:
            self.settings["max_tokens"] = new_limit
            self.save_settings()
            self.status_bar.showMessage(f"Token limit set to {new_limit}")
    
    def save_api_key(self):
        self.api_key = self.api_key_input.toPlainText().strip()
        if self.api_key:
            self.settings["api_key"] = self.api_key
            self.save_settings()
            self.status_bar.showMessage("API key saved")
        else:
            self.status_bar.showMessage("Please enter a valid API key")
    
    def load_settings(self):
        self.settings = {}
        try:
            if os.path.exists("deepseek_settings.json"):
                with open("deepseek_settings.json", "r") as f:
                    self.settings = json.load(f)
            
            if "api_key" in self.settings:
                self.api_key = self.settings["api_key"]
                self.api_key_input.setPlainText(self.api_key)
                
            if "max_tokens" not in self.settings:
                self.settings["max_tokens"] = 4000  # Default token limit
                
        except Exception as e:
            self.status_bar.showMessage(f"Error loading settings: {str(e)}")
    
    def save_settings(self):
        try:
            with open("deepseek_settings.json", "w") as f:
                json.dump(self.settings, f)
        except Exception as e:
            self.status_bar.showMessage(f"Error saving settings: {str(e)}")
    
    def load_document(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Document", "", 
            "All Supported Files (*.txt *.py *.js *.php *.html *.css *.md *.docx);;Text Files (*.txt);;Python Files (*.py);;JavaScript Files (*.js);;PHP Files (*.php);;HTML Files (*.html);;CSS Files (*.css);;Markdown Files (*.md);;Word Documents (*.docx)"
        )
        
        if file_path:
            content = DocumentProcessor.extract_text_from_file(file_path)
            filename = os.path.basename(file_path)
            
            # Store the document content
            self.loaded_documents[filename] = content
            
            # Add to list widget
            item = QListWidgetItem(filename)
            self.docsListWidget.addItem(item)
            
            # If it's the first document, show it
            if len(self.loaded_documents) == 1:
                self.show_document_content(filename)
            
            self.status_bar.showMessage(f"Loaded: {filename}")
    
    def show_selected_document(self, item):
        filename = item.text()
        self.show_document_content(filename)
    
    def show_document_content(self, filename):
        if filename in self.loaded_documents:
            content = self.loaded_documents[filename]
            self.editor.setPlainText(content)
            
            # Try to detect language based on file extension
            ext = os.path.splitext(filename)[1].lower()
            if ext == ".py":
                self.language_select.setCurrentText("python")
            elif ext in [".js", ".jsx"]:
                self.language_select.setCurrentText("javascript")
            elif ext == ".php":
                self.language_select.setCurrentText("php")
            elif ext in [".html", ".htm"]:
                self.language_select.setCurrentText("html")
            elif ext == ".css":
                self.language_select.setCurrentText("css")
            elif ext == ".md":
                self.language_select.setCurrentText("markdown")
            else:
                self.language_select.setCurrentText("text")
    
    def remove_selected_document(self):
        current_item = self.docsListWidget.currentItem()
        if current_item:
            filename = current_item.text()
            if filename in self.loaded_documents:
                del self.loaded_documents[filename]
                self.docsListWidget.takeItem(self.docsListWidget.row(current_item))
                self.status_bar.showMessage(f"Removed: {filename}")
                
                # If we removed the currently displayed document, clear the editor
                if self.editor.toPlainText() == self.loaded_documents.get(filename, ""):
                    self.editor.clear()
    
    def clear_documents(self):
        self.loaded_documents.clear()
        self.docsListWidget.clear()
        self.editor.clear()
        self.status_bar.showMessage("Cleared all documents")
    
    def update_project_context(self):
        self.current_project_context = self.project_context_edit.toPlainText()
        self.status_bar.showMessage("Project context updated")
    
    def change_language(self, language):
        self.current_language = language
        self.highlighter = LanguageHighlighter(self.editor.document(), language)
        self.status_bar.showMessage(f"Language changed to {language}")
    
    def update_highlighter(self):
        # Recreate highlighter when document changes
        self.highlighter = LanguageHighlighter(self.editor.document(), self.current_language)
    
    def save_file(self):
        if not self.editor.toPlainText().strip():
            self.status_bar.showMessage("No content to save")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save File", "", 
            "Text Files (*.txt);;Python Files (*.py);;JavaScript Files (*.js);;PHP Files (*.php);;HTML Files (*.html);;CSS Files (*.css);;Markdown Files (*.md)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.editor.toPlainText())
                self.status_bar.showMessage(f"File saved: {file_path}")
            except Exception as e:
                self.status_bar.showMessage(f"Error saving file: {str(e)}")
    
    def switch_conversation(self, conversation_name):
        if conversation_name == "New Conversation":
            self.new_conversation()
        elif conversation_name in self.conversation_context:
            self.current_conversation_id = conversation_name
            # Update the response area with the conversation history
            self.display_conversation_history()
            self.status_bar.showMessage(f"Switched to conversation: {conversation_name}")
    
    def delete_conversation(self):
        current_conversation = self.conversation_select.currentText()
        if current_conversation != "New Conversation":
            if current_conversation in self.conversation_context:
                del self.conversation_context[current_conversation]
            
            index = self.conversation_select.findText(current_conversation)
            if index >= 0:
                self.conversation_select.removeItem(index)
            
            # Switch to a new conversation
            self.new_conversation()
            self.status_bar.showMessage(f"Deleted conversation: {current_conversation}")
    
    def new_conversation(self):
        # Generate a unique conversation ID
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_conversation_id = f"Conversation_{timestamp}"
        
        # Initialize empty history for this conversation
        self.conversation_context[self.current_conversation_id] = []
        
        # Add to dropdown
        self.conversation_select.addItem(self.current_conversation_id)
        self.conversation_select.setCurrentText(self.current_conversation_id)
        
        # Clear response area
        self.response_output.clear()
        
        self.status_bar.showMessage(f"Started new conversation: {self.current_conversation_id}")
    
    def display_conversation_history(self):
        if self.current_conversation_id in self.conversation_context:
            history = self.conversation_context[self.current_conversation_id]
            formatted_history = ""
            
            for message in history:
                role = message.get("role", "")
                content = message.get("content", "")
                
                if role == "user":
                    formatted_history += f"<b>You:</b><br/>{html.escape(content)}<br/><br/>"
                elif role == "assistant":
                    formatted_history += f"<b>Assistant:</b><br/>{self.format_response(content)}<br/><br/>"
            
            self.response_output.setHtml(formatted_history)
    
    def format_response(self, text):
        # Convert markdown to HTML
        html_text = markdown.markdown(text)
        
        # Additional formatting for code blocks
        html_text = html_text.replace("<code>", '<code style="background-color: #2d2d2d; padding: 5px; border-radius: 3px; display: block; overflow-x: auto;">')
        
        return html_text
    
    def copy_response(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.response_output.toPlainText())
        self.status_bar.showMessage("Response copied to clipboard")
    
    def clear_response(self):
        self.response_output.clear()
        self.status_bar.showMessage("Response cleared")
    
    def clear_all(self):
        self.editor.clear()
        self.prompt_input.clear()
        self.response_output.clear()
        self.status_bar.showMessage("All content cleared")
    
    def save_conversation(self):
        if not self.current_conversation_id or self.current_conversation_id not in self.conversation_context:
            self.status_bar.showMessage("No conversation to save")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Conversation", f"{self.current_conversation_id}.json", 
            "JSON Files (*.json)"
        )
        
        if file_path:
            try:
                conversation_data = {
                    "id": self.current_conversation_id,
                    "history": self.conversation_context[self.current_conversation_id],
                    "timestamp": datetime.now().isoformat()
                }
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(conversation_data, f, indent=2)
                    
                self.status_bar.showMessage(f"Conversation saved: {file_path}")
            except Exception as e:
                self.status_bar.showMessage(f"Error saving conversation: {str(e)}")
    
    def load_conversation(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Load Conversation", "", 
            "JSON Files (*.json)"
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    conversation_data = json.load(f)
                
                conversation_id = conversation_data.get("id", f"Loaded_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
                history = conversation_data.get("history", [])
                
                # Add to conversation context
                self.conversation_context[conversation_id] = history
                
                # Add to dropdown
                self.conversation_select.addItem(conversation_id)
                self.conversation_select.setCurrentText(conversation_id)
                
                # Display the history
                self.current_conversation_id = conversation_id
                self.display_conversation_history()
                
                self.status_bar.showMessage(f"Loaded conversation: {conversation_id}")
            except Exception as e:
                self.status_bar.showMessage(f"Error loading conversation: {str(e)}")
    
    def send_to_deepseek(self):
        if not self.api_key:
            self.status_bar.showMessage("Please enter and save your API key first")
            return
            
        prompt = self.prompt_input.toPlainText().strip()
        if not prompt:
            self.status_bar.showMessage("Please enter a prompt")
            return
        
        # Create a new conversation if none exists
        if not self.current_conversation_id:
            self.new_conversation()
        
        # Build the message with context
        full_prompt = self.build_prompt_with_context(prompt)
        
        # Add user message to conversation history
        user_message = {"role": "user", "content": full_prompt}
        self.conversation_context[self.current_conversation_id].append(user_message)
        
        # Display user message in response area
        self.display_conversation_history()
        
        # Clear the prompt input
        self.prompt_input.clear()
        
        # Disable send button while processing
        self.send_btn.setEnabled(False)
        self.status_bar.showMessage("Sending to DeepSeek...")
        
        # Start the worker thread
        self.worker = DeepSeekWorker(
            self.api_key, 
            self.conversation_context[self.current_conversation_id],
            self.model_select.currentText(),
            self.current_conversation_id
        )
        self.worker.response_received.connect(self.handle_response)
        self.worker.error_occurred.connect(self.handle_error)
        self.worker.start()
    
    def build_prompt_with_context(self, prompt):
        """Build a comprehensive prompt with project context and document content"""
        full_prompt = prompt
        
        # Add project context if enabled
        if self.include_context_check.isChecked() and self.current_project_context:
            full_prompt = f"Project Context: {self.current_project_context}\n\nUser Question: {full_prompt}"
        
        # Add document content if enabled and available
        current_doc_content = self.editor.toPlainText().strip()
        if self.include_document_check.isChecked() and current_doc_content:
            # Get the current document name
            current_items = self.docsListWidget.selectedItems()
            doc_name = current_items[0].text() if current_items else "current document"
            
            full_prompt = f"Document Content ({doc_name}):\n```{current_doc_content}```\n\nUser Question: {full_prompt}"
        
        return full_prompt
    
    def handle_response(self, response, conversation_id):
        # Only process if it's for the current conversation
        if conversation_id == self.current_conversation_id:
            # Add assistant response to conversation history
            assistant_message = {"role": "assistant", "content": response}
            self.conversation_context[conversation_id].append(assistant_message)
            
            # Display the updated conversation
            self.display_conversation_history()
            
            # Scroll to bottom
            self.response_output.moveCursor(QTextCursor.MoveOperation.End)
            
            # Check if we're approaching token limits and trim if necessary
            self.manage_conversation_tokens()
            
            self.status_bar.showMessage("Response received")
        
        # Re-enable send button
        self.send_btn.setEnabled(True)
    
    def handle_error(self, error_message):
        self.status_bar.showMessage(f"Error: {error_message}")
        self.response_output.append(f"<b>Error:</b><br/>{html.escape(error_message)}<br/><br/>")
        
        # Re-enable send button
        self.send_btn.setEnabled(True)
    
    def manage_conversation_tokens(self):
        """Manage conversation tokens to prevent exceeding limits"""
        if self.current_conversation_id not in self.conversation_context:
            return
            
        history = self.conversation_context[self.current_conversation_id]
        max_tokens = self.settings.get("max_tokens", 4000)
        
        # Simple token estimation (approx 4 chars per token)
        total_chars = sum(len(msg.get("content", "")) for msg in history)
        estimated_tokens = total_chars / 4
        
        # If we're approaching the limit, remove older messages
        if estimated_tokens > max_tokens * 0.8:  # Start trimming at 80% of limit
            # Keep system message if exists and remove oldest user/assistant pairs
            if len(history) > 2:
                # Remove the second message (first user message after system if exists)
                # or the first message if no system message
                if history[0].get("role") == "system":
                    # Keep system message and remove oldest user/assistant pair
                    if len(history) > 3:
                        del history[1:3]  # Remove user and assistant messages
                    else:
                        # If only system + one pair, remove just the user message
                        if len(history) > 1:
                            del history[1]
                else:
                    # No system message, remove the first user/assistant pair
                    if len(history) >= 2:
                        del history[0:2]
                    else:
                        del history[0]
                
                self.status_bar.showMessage("Trimmed conversation history to stay within token limits")

def main():
    app = QApplication(sys.argv)
    window = DeepSeekAssistant()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()