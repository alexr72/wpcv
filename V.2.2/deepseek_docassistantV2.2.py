import sys
import requests
import json
import os
import html
import re
import tiktoken
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QTextEdit, QPushButton, 
                             QVBoxLayout, QHBoxLayout, QWidget, QSplitter, QLabel, 
                             QFileDialog, QComboBox, QStatusBar, QMessageBox, QListWidget,
                             QTabWidget, QListWidgetItem, QCheckBox, QMenuBar, QMenu,
                             QTreeWidget, QTreeWidgetItem, QHeaderView, QInputDialog)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QSyntaxHighlighter, QTextCharFormat, QColor, QTextDocument, QTextCursor, QClipboard
import markdown

class DeepSeekWorker(QThread):
    response_received = pyqtSignal(str, str)
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
        
        for attempt in range(3):
            try:
                response = requests.post(self.url, headers=headers, json=payload, timeout=60)
                if response.status_code == 200:
                    result = response.json()
                    self.response_received.emit(result['choices'][0]['message']['content'], self.conversation_id)
                    return
                else:
                    if attempt == 2:
                        self.error_occurred.emit(f"API Error: {response.status_code} - {response.text}")
                    continue
                    
            except requests.exceptions.Timeout:
                if attempt == 2:
                    self.error_occurred.emit("Request timed out after 3 attempts.")
                continue
                
            except Exception as e:
                self.error_occurred.emit(f"Request failed: {str(e)}")
                return

class WordPressHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlighting_rules = []
        self.setup_rules()
        
    def setup_rules(self):
        # PHP syntax highlighting
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor(100, 150, 100))
        
        string_format = QTextCharFormat()
        string_format.setForeground(QColor(200, 200, 100))
        
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor(86, 156, 214))
        keyword_format.setFontWeight(QFont.Weight.Bold)
        
        function_format = QTextCharFormat()
        function_format.setForeground(QColor(220, 220, 170))
        
        # WordPress-specific keywords
        wp_keywords = [
            "wp_enqueue_script", "wp_enqueue_style", "add_action", "add_filter",
            "get_template_part", "the_content", "the_title", "have_posts",
            "the_post", "WP_Query", "WP_Error", "register_post_type",
            "register_taxonomy", "is_admin", "is_user_logged_in", "wp_die",
            "apply_filters", "do_action", "get_option", "update_option",
            "get_post_meta", "update_post_meta", "get_the_ID", "get_permalink"
        ]
        
        for word in wp_keywords:
            pattern = r"\b" + word + r"\b"
            self.highlighting_rules.append((pattern, keyword_format))
            
        self.highlighting_rules.append((r"//.*", comment_format))
        self.highlighting_rules.append((r"/\*.*?\*/", comment_format))
        self.highlighting_rules.append((r'".*?"', string_format))
        self.highlighting_rules.append((r"'.*?'", string_format))
        self.highlighting_rules.append((r"\bfunction\b", keyword_format))
        self.highlighting_rules.append((r"\bclass\b", keyword_format))
    
    def highlightBlock(self, text):
        for pattern, format in self.highlighting_rules:
            from PyQt6.QtCore import QRegularExpression
            expression = QRegularExpression(pattern)
            iterator = expression.globalMatch(text)
            while iterator.hasNext():
                match = iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), format)

class WordPressAssistant(QMainWindow):
    def __init__(self):
        super().__init__()
        self.api_key = None
        self.conversation_history = []
        self.current_conversation_id = None
        self.conversation_context = {}
        self.loaded_documents = {}
        self.project_structure = {}
        self.current_project_path = None
        self.token_limit = 8000
        self.current_tokens = 0
        self.encoder = tiktoken.get_encoding("cl100k_base")
        
        self.initUI()
        self.load_settings()
        self.apply_wp_styles()
        
    def apply_wp_styles(self):
        wp_stylesheet = """
        QMainWindow, QWidget { background-color: #23282d; color: #f1f1f1; }
        QTextEdit, QPlainTextEdit { background-color: #32373c; color: #f1f1f1; border: 1px solid #0073aa; border-radius: 3px; padding: 5px; font-family: Consolas, monospace; }
        QPushButton { background-color: #0073aa; color: #ffffff; border: none; border-radius: 3px; padding: 8px 16px; }
        QPushButton:hover { background-color: #00a0d2; }
        QPushButton:pressed { background-color: #005a87; }
        QComboBox { background-color: #32373c; color: #f1f1f1; border: 1px solid #0073aa; border-radius: 3px; padding: 5px; }
        QListWidget { background-color: #32373c; color: #f1f1f1; border: 1px solid #0073aa; border-radius: 3px; }
        QTabWidget::pane { border: 1px solid #0073aa; background-color: #23282d; }
        QTabBar::tab { background-color: #32373c; color: #f1f1f1; padding: 8px 16px; border: 1px solid #0073aa; }
        QTabBar::tab:selected { background-color: #0073aa; color: #ffffff; }
        QLabel { color: #f1f1f1; }
        QStatusBar { background-color: #32373c; color: #f1f1f1; }
        QMenuBar { background-color: #23282d; color: #f1f1f1; }
        QMenu { background-color: #32373c; color: #f1f1f1; border: 1px solid #0073aa; }
        QCheckBox { color: #f1f1f1; }
        QTreeWidget { background-color: #32373c; color: #f1f1f1; border: 1px solid #0073aa; border-radius: 3px; }
        """
        self.setStyleSheet(wp_stylesheet)
        
    def initUI(self):
        self.setWindowTitle("WordPress & Vue Development Assistant")
        self.setGeometry(100, 100, 1400, 900)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel - Project structure and file management
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # Project structure tree
        left_layout.addWidget(QLabel("Project Structure:"))
        self.project_tree = QTreeWidget()
        self.project_tree.setHeaderLabel("Files")
        self.project_tree.itemClicked.connect(self.on_tree_item_clicked)
        left_layout.addWidget(self.project_tree)
        
        # Project buttons
        project_buttons = QHBoxLayout()
        self.load_project_btn = QPushButton("Load WordPress Project")
        self.load_project_btn.clicked.connect(self.load_wordpress_project)
        self.scan_project_btn = QPushButton("Scan Project")
        self.scan_project_btn.clicked.connect(self.scan_project_structure)
        
        project_buttons.addWidget(self.load_project_btn)
        project_buttons.addWidget(self.scan_project_btn)
        left_layout.addLayout(project_buttons)
        
        # Conversation history
        history_tab = QTabWidget()
        
        # Chat history tab
        chat_history_widget = QWidget()
        chat_history_layout = QVBoxLayout(chat_history_widget)
        
        chat_history_layout.addWidget(QLabel("Conversation History:"))
        self.conversation_list = QListWidget()
        self.conversation_list.itemClicked.connect(self.show_conversation_item)
        chat_history_layout.addWidget(self.conversation_list)
        
        history_buttons = QHBoxLayout()
        self.clear_history_btn = QPushButton("Clear History")
        self.clear_history_btn.clicked.connect(self.clear_conversation_history)
        self.new_chat_btn = QPushButton("New Chat")
        self.new_chat_btn.clicked.connect(self.start_new_conversation)
        
        history_buttons.addWidget(self.new_chat_btn)
        history_buttons.addWidget(self.clear_history_btn)
        chat_history_layout.addLayout(history_buttons)
        
        history_tab.addTab(chat_history_widget, "Chat History")
        
        # Document tab
        document_widget = QWidget()
        document_layout = QVBoxLayout(document_widget)
        
        document_layout.addWidget(QLabel("Loaded Files:"))
        self.docsListWidget = QListWidget()
        document_layout.addWidget(self.docsListWidget)
        
        doc_buttons = QHBoxLayout()
        self.load_doc_btn = QPushButton("Load File")
        self.load_doc_btn.clicked.connect(self.load_document)
        self.clear_docs_btn = QPushButton("Clear Files")
        self.clear_docs_btn.clicked.connect(self.clear_documents)
        
        doc_buttons.addWidget(self.load_doc_btn)
        doc_buttons.addWidget(self.clear_docs_btn)
        document_layout.addLayout(doc_buttons)
        
        history_tab.addTab(document_widget, "Documents")
        
        left_layout.addWidget(history_tab)
        
        # Document content
        left_layout.addWidget(QLabel("File Content:"))
        self.code_editor = QTextEdit()
        self.code_editor.setFont(QFont("Consolas", 11))
        self.highlighter = WordPressHighlighter(self.code_editor.document())
        left_layout.addWidget(self.code_editor)
        
        # Right panel - Assistant
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # WordPress-specific prompts
        wp_prompts = QHBoxLayout()
        self.wp_security_btn = QPushButton("Security Check")
        self.wp_security_btn.clicked.connect(self.wp_security_check)
        self.wp_performance_btn = QPushButton("Performance")
        self.wp_performance_btn.clicked.connect(self.wp_performance_tips)
        self.wp_debug_btn = QPushButton("Debug Help")
        self.wp_debug_btn.clicked.connect(self.wp_debug_help)
        
        wp_prompts.addWidget(self.wp_security_btn)
        wp_prompts.addWidget(self.wp_performance_btn)
        wp_prompts.addWidget(self.wp_debug_btn)
        right_layout.addLayout(wp_prompts)
        
        # Vue.js and advanced prompts
        advanced_prompts = QHBoxLayout()
        self.wp_plugin_btn = QPushButton("Create Plugin")
        self.wp_plugin_btn.clicked.connect(self.create_wp_plugin)
        self.wp_theme_btn = QPushButton("Create Theme")
        self.wp_theme_btn.clicked.connect(self.create_wp_theme)
        self.vue_btn = QPushButton("Vue Integration")
        self.vue_btn.clicked.connect(self.vue_integration)
        self.rest_api_btn = QPushButton("REST API")
        self.rest_api_btn.clicked.connect(self.wp_rest_api)
        
        advanced_prompts.addWidget(self.wp_plugin_btn)
        advanced_prompts.addWidget(self.wp_theme_btn)
        advanced_prompts.addWidget(self.vue_btn)
        advanced_prompts.addWidget(self.rest_api_btn)
        right_layout.addLayout(advanced_prompts)
        
        # Token management
        token_layout = QHBoxLayout()
        self.token_label = QLabel("Tokens: 0/8000")
        self.context_checkbox = QCheckBox("Maintain Context")
        self.context_checkbox.setChecked(True)
        
        token_layout.addWidget(self.token_label)
        token_layout.addStretch()
        token_layout.addWidget(self.context_checkbox)
        right_layout.addLayout(token_layout)
        
        # Prompt input
        right_layout.addWidget(QLabel("Ask about WordPress:"))
        self.prompt_input = QTextEdit()
        self.prompt_input.setMaximumHeight(100)
        self.prompt_input.setPlaceholderText("Ask WordPress development questions...")
        right_layout.addWidget(self.prompt_input)
        
        # Assistant controls
        controls_layout = QHBoxLayout()
        self.ask_btn = QPushButton("Ask Assistant")
        self.ask_btn.clicked.connect(self.ask_assistant)
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.clicked.connect(self.clear_chat)
        
        controls_layout.addWidget(self.ask_btn)
        controls_layout.addWidget(self.clear_btn)
        controls_layout.addStretch()
        right_layout.addLayout(controls_layout)
        
        # Response area with action buttons
        response_header = QHBoxLayout()
        response_header.addWidget(QLabel("Assistant Response:"))
        
        self.copy_btn = QPushButton("Copy Code")
        self.copy_btn.clicked.connect(self.copy_response_code)
        self.download_btn = QPushButton("Download Code")
        self.download_btn.clicked.connect(self.download_response_code)
        
        response_header.addStretch()
        response_header.addWidget(self.copy_btn)
        response_header.addWidget(self.download_btn)
        right_layout.addLayout(response_header)
        
        self.response_area = QTextEdit()
        self.response_area.setReadOnly(True)
        right_layout.addWidget(self.response_area)
        
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([500, 900])
        
        main_layout.addWidget(splitter)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready for WordPress development")
        
        # Menu
        menubar = self.menuBar()
        settings_menu = menubar.addMenu("Settings")
        api_action = settings_menu.addAction("Set API Key")
        api_action.triggered.connect(self.set_api_key)
        
        # Start new conversation
        self.start_new_conversation()
        
    def load_wordpress_project(self):
        """Load an entire WordPress project folder"""
        folder_path = QFileDialog.getExistingDirectory(
            self, 
            "Select WordPress Project Folder",
            "",
            QFileDialog.Option.ShowDirsOnly
        )
        
        if not folder_path:
            return
            
        self.current_project_path = folder_path
        self.status_bar.showMessage(f"Loaded project: {os.path.basename(folder_path)}")
        
        # Scan the project structure
        self.scan_project_structure()
        
    def scan_project_structure(self):
        """Scan and display the WordPress project structure"""
        if not self.current_project_path:
            QMessageBox.warning(self, "No Project", "Please load a WordPress project first.")
            return
            
        self.project_tree.clear()
        self.project_structure = {}
        
        # Common WordPress directories to highlight
        wp_directories = {
            'wp-admin': 'WordPress Admin',
            'wp-includes': 'WordPress Includes',
            'wp-content/themes': 'Themes',
            'wp-content/plugins': 'Plugins',
            'wp-content/uploads': 'Uploads',
            'wp-content/mu-plugins': 'Must-Use Plugins'
        }
        
        # Create root item
        root_item = QTreeWidgetItem(self.project_tree, [os.path.basename(self.current_project_path)])
        root_item.setData(0, Qt.ItemDataRole.UserRole, self.current_project_path)
        
        # Recursively add files and directories
        self.add_files_to_tree(root_item, self.current_project_path, wp_directories)
        
        # Expand the root item
        self.project_tree.expandItem(root_item)
        
    def add_files_to_tree(self, parent_item, path, wp_directories):
        """Recursively add files to the tree widget"""
        try:
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                relative_path = os.path.relpath(item_path, self.current_project_path)
                
                # Create tree item
                if os.path.isdir(item_path):
                    # Check if this is a special WordPress directory
                    display_name = wp_directories.get(relative_path, item)
                    
                    child_item = QTreeWidgetItem(parent_item, [display_name])
                    child_item.setData(0, Qt.ItemDataRole.UserRole, item_path)
                    
                    # Add icon or special formatting for WordPress directories
                    if relative_path in wp_directories:
                        child_item.setForeground(0, QColor(0, 150, 200))
                    
                    # Recursively add children
                    self.add_files_to_tree(child_item, item_path, wp_directories)
                else:
                    # Only add supported file types
                    if item.lower().endswith(('.php', '.js', '.css', '.html', '.txt', '.md', '.json', '.xml')):
                        child_item = QTreeWidgetItem(parent_item, [item])
                        child_item.setData(0, Qt.ItemDataRole.UserRole, item_path)
                        
                        # Color code by file type
                        if item.endswith('.php'):
                            child_item.setForeground(0, QColor(100, 150, 250))
                        elif item.endswith(('.js', '.ts')):
                            child_item.setForeground(0, QColor(240, 220, 100))
                        elif item.endswith('.css'):
                            child_item.setForeground(0, QColor(150, 100, 250))
        except PermissionError:
            self.status_bar.showMessage(f"Permission denied: {path}")
        except Exception as e:
            self.status_bar.showMessage(f"Error scanning: {str(e)}")
            
    def on_tree_item_clicked(self, item, column):
        """Handle clicks on tree items"""
        file_path = item.data(0, Qt.ItemDataRole.UserRole)
        
        if os.path.isfile(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                self.code_editor.setPlainText(content)
                
                # Set appropriate highlighter based on file extension
                ext = os.path.splitext(file_path)[1].lower()
                if ext == '.php':
                    self.highlighter = WordPressHighlighter(self.code_editor.document())
                else:
                    # You could add other highlighters here
                    self.highlighter = None
                    
                # Update status
                self.status_bar.showMessage(f"Loaded: {os.path.basename(file_path)}")
                
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not read file: {str(e)}")
                
    def wp_rest_api(self):
        """REST API specific prompt"""
        self.prompt_input.setPlainText("""
        Help with WordPress REST API:
        1. Creating custom endpoints
        2. Authentication methods
        3. Schema definition
        4. Permission callbacks
        5. Best practices for REST API in WordPress
        """)
        
    def build_project_context_prompt(self):
        """Build a context prompt based on the loaded WordPress project"""
        if not self.current_project_path:
            return ""
            
        prompt_lines = []
        prompt_lines.append("## WordPress Project Context\n")
        prompt_lines.append(f"Project: {os.path.basename(self.current_project_path)}")
        prompt_lines.append("")
        
        # Add information about the project structure
        prompt_lines.append("### Project Structure:")
        
        # Count files by type
        php_files = []
        js_files = []
        css_files = []
        
        for root, dirs, files in os.walk(self.current_project_path):
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, self.current_project_path)
                
                if file.endswith('.php'):
                    php_files.append(rel_path)
                elif file.endswith(('.js', '.ts')):
                    js_files.append(rel_path)
                elif file.endswith('.css'):
                    css_files.append(rel_path)
        
        prompt_lines.append(f"- PHP Files: {len(php_files)}")
        prompt_lines.append(f"- JavaScript Files: {len(js_files)}")
        prompt_lines.append(f"- CSS Files: {len(css_files)}")
        prompt_lines.append("")
        
        # Check if it's a standard WordPress installation
        wp_core_files = ['wp-admin', 'wp-includes', 'wp-content']
        has_wp_core = all(os.path.exists(os.path.join(self.current_project_path, f)) for f in wp_core_files)
        
        if has_wp_core:
            prompt_lines.append("This appears to be a standard WordPress installation.")
            
            # Check for themes
            themes_path = os.path.join(self.current_project_path, 'wp-content', 'themes')
            if os.path.exists(themes_path):
                themes = [d for d in os.listdir(themes_path) 
                         if os.path.isdir(os.path.join(themes_path, d)) and not d.startswith('.')]
                prompt_lines.append(f"Themes: {', '.join(themes) if themes else 'None found'}")
            
            # Check for plugins
            plugins_path = os.path.join(self.current_project_path, 'wp-content', 'plugins')
            if os.path.exists(plugins_path):
                plugins = [d for d in os.listdir(plugins_path) 
                          if os.path.isdir(os.path.join(plugins_path, d)) and not d.startswith('.')]
                prompt_lines.append(f"Plugins: {', '.join(plugins) if plugins else 'None found'}")
        
        prompt_lines.append("")
        prompt_lines.append("Please use this project context when answering questions.")
        
        return "\n".join(prompt_lines)
        
    def estimate_tokens(self, text):
        """More accurate token estimation using tiktoken"""
        if not text:
            return 0
        return len(self.encoder.encode(text))
        
    def update_token_count(self):
        self.token_label.setText(f"Tokens: {self.current_tokens}/{self.token_limit}")
        
        # Change color if approaching limit
        if self.current_tokens > self.token_limit * 0.8:
            self.token_label.setStyleSheet("color: #ff6b6b;")
        else:
            self.token_label.setStyleSheet("color: #f1f1f1;")
            
    def manage_token_usage(self, prompt_content, system_messages=[]):
        # Calculate tokens for all components
        prompt_tokens = self.estimate_tokens(prompt_content)
        system_tokens = sum(self.estimate_tokens(msg.get("content", "")) for msg in system_messages)

        total_new_tokens = prompt_tokens + system_tokens

        # Estimate response tokens (conservative estimate)
        estimated_response_tokens = 1000  # Average response size

        total_estimated_tokens = total_new_tokens + estimated_response_tokens

        # If adding new content would exceed limit, remove oldest messages from context
        while (self.current_tokens + total_estimated_tokens > self.token_limit and
               self.conversation_context.get(self.current_conversation_id, [])):

            # Remove the oldest message pair (user + assistant)
            if len(self.conversation_context[self.current_conversation_id]) >= 2:
                # Remove user message
                if self.conversation_context[self.current_conversation_id]:
                    removed = self.conversation_context[self.current_conversation_id].pop(0)
                    self.current_tokens -= self.estimate_tokens(removed.get("content", ""))

                # Remove assistant message
                if self.conversation_context[self.current_conversation_id]:
                    removed = self.conversation_context[self.current_conversation_id].pop(0)
                    self.current_tokens -= self.estimate_tokens(removed.get("content", ""))

        self.update_token_count()
        return prompt_tokens
        
    def create_wp_plugin(self):
        self.prompt_input.setPlainText("""
        Create a WordPress plugin with the following structure:
        1. Main plugin file with header comments
        2. Activation/deactivation hooks
        3. Example shortcode implementation
        4. Admin settings page
        5. Proper enqueueing of scripts and styles
        """)
        
    def create_wp_theme(self):
        self.prompt_input.setPlainText("""
        Create a WordPress theme with the following structure:
        1. style.css with theme header
        2. index.php, header.php, footer.php, sidebar.php
        3. functions.php with theme setup
        4. Template hierarchy implementation
        5. Responsive design considerations
        """)
        
    def vue_integration(self):
        self.prompt_input.setPlainText("""
        How to integrate Vue.js with WordPress:
        1. Enqueuing Vue.js in WordPress
        2. Creating Vue components for WordPress
        3. Communicating with WordPress REST API
        4. Best practices for Vue-WordPress integration
        5. Handling authentication and nonces
        """)
        
    def wp_security_check(self):
        self.prompt_input.setPlainText("""
        Provide WordPress security best practices for:
        1. Data validation and sanitization
        2. Nonce implementation
        3. User capability checks
        4. SQL injection prevention
        5. XSS prevention techniques
        """)
        
    def wp_performance_tips(self):
        self.prompt_input.setPlainText("""
        Provide WordPress performance optimization tips:
        1. Database query optimization
        2. Object caching implementation
        3. Asset optimization (CSS/JS)
        4. Transients usage
        5. AJAX optimization techniques
        """)
        
    def wp_debug_help(self):
        self.prompt_input.setPlainText("""
        Help debug common WordPress issues:
        1. White screen of death
        2. Plugin conflicts
        3. Database connection errors
        4. Memory limit exhaustion
        5. REST API authentication issues
        """)
        
    def load_document(self):
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "Open WordPress Files", "", 
            "WordPress Files (*.php *.js *.css *.html *.txt *.md);;All Files (*)"
        )
        
        if not file_paths:
            return
            
        for file_path in file_paths:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                filename = os.path.basename(file_path)
                self.loaded_documents[filename] = content
                
                # Add to list widget
                self.docsListWidget.addItem(filename)
                self.status_bar.showMessage(f"Loaded: {filename}")
                
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not load {file_path}: {str(e)}")
                
    def clear_documents(self):
        self.loaded_documents.clear()
        self.docsListWidget.clear()
        self.code_editor.clear()
        self.status_bar.showMessage("Documents cleared")
        
    def start_new_conversation(self):
        self.current_conversation_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.conversation_context[self.current_conversation_id] = []
        self.current_tokens = 0
        self.update_token_count()
        self.response_area.clear()
        self.prompt_input.clear()
        self.status_bar.showMessage("New conversation started")
        
    def show_conversation_item(self, item):
        # Find the conversation by timestamp in the item text
        timestamp_str = item.text().split(']')[0][1:]
        try:
            timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M")
            for conv in self.conversation_history:
                if datetime.fromtimestamp(conv["timestamp"]).strftime("%Y-%m-%d %H:%M") == timestamp_str:
                    # Display the conversation
                    html_content = f"""
                    <div style="background-color: #32373c; color: #f1f1f1; padding: 12px; border-radius: 5px; margin-bottom: 10px;">
                        <strong>You ({timestamp_str}):</strong><br>
                        {html.escape(conv['prompt']).replace('\n', '<br>')}
                    </div>
                    <div style="background-color: #2c3338; color: #f1f1f1; padding: 12px; border-radius: 5px;">
                        <strong>Assistant:</strong><br>
                        {markdown.markdown(conv['response'])}
                    </div>
                    """
                    self.response_area.setHtml(html_content)
                    break
        except ValueError:
            self.status_bar.showMessage("Could not parse conversation timestamp")
            
    def clear_conversation_history(self):
        reply = QMessageBox.question(self, "Clear History", 
                                    "Are you sure you want to clear all conversation history?",
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.conversation_history = []
            self.conversation_context = {}
            self.conversation_list.clear()
            self.start_new_conversation()
            self.status_bar.showMessage("Conversation history cleared")
            
    def copy_response_code(self):
        # Extract just the code blocks from the response for clean copying
        text = self.response_area.toPlainText()
        code_blocks = re.findall(r'```(?:\w+)?\s*(.*?)```', text, re.DOTALL)
        
        clipboard = QApplication.clipboard()
        if code_blocks:
            clipboard.setText("\n\n".join(code_blocks))
            self.status_bar.showMessage("Code blocks copied to clipboard!")
        else:
            clipboard.setText(text)
            self.status_bar.showMessage("Response copied to clipboard!")
            
    def download_response_code(self):
        # Extract code blocks or use full response
        text = self.response_area.toPlainText()
        code_blocks = re.findall(r'```(?:\w+)?\s*(.*?)```', text, re.DOTALL)
        
        content = "\n\n".join(code_blocks) if code_blocks else text
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Code", "", 
            "PHP Files (*.php);;JavaScript Files (*.js);;CSS Files (*.css);;All Files (*)"
        )
        
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                self.status_bar.showMessage(f"Code saved to {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not save file: {str(e)}")
                
    def ask_assistant(self):
        if not self.api_key:
            QMessageBox.warning(self, "API Key Required", "Please set your DeepSeek API key first.")
            return
        
        prompt = self.prompt_input.toPlainText().strip()
        if not prompt:
            QMessageBox.warning(self, "Empty Prompt", "Please enter a question.")
            return
        
        # Prepare system messages first
        system_messages = []
        
        # Add WordPress context
        wp_context = """
        You are a WordPress development expert. Focus on providing:
        - WordPress best practices
        - Secure code examples
        - Performance optimization tips
        - Vue.js integration advice where relevant
        - Modern development techniques (REST API, Blocks, etc.)
        """
        system_messages.append({"role": "system", "content": wp_context})
        
        # Add project context if available
        project_context = self.build_project_context_prompt()
        if project_context:
            system_messages.append({"role": "system", "content": project_context})

        # Manage token usage with all components
        prompt_tokens = self.manage_token_usage(prompt, system_messages)
        self.current_tokens += prompt_tokens

        # Add debug output:
        print(f"Available conversations: {list(self.conversation_context.keys())}")
        print(f"Looking for: {self.current_conversation_id}")

        self.status_bar.showMessage("Processing your question...")
        self.ask_btn.setEnabled(False)

        # Prepare messages for the API
        messages = []
        messages.extend(system_messages)
        
        # Add conversation history if context is enabled
        if self.context_checkbox.isChecked():
            context_key = self.current_conversation_id
            if context_key in self.conversation_context:
                context_messages = self.conversation_context[context_key]
                print(f"Adding {len(context_messages)} context messages to conversation {context_key}")
                messages.extend(context_messages)
            else:
                print(f"No context found for {context_key}")
        
        # Add current prompt
        messages.append({"role": "user", "content": prompt})
        
        # DEBUG: Print the messages being sent
        print("Sending messages to API:")
        for i, msg in enumerate(messages):
            print(f"{i}: {msg['role']} - {msg['content'][:100]}...")
        
        self.worker = DeepSeekWorker(self.api_key, messages, "deepseek-coder", self.current_conversation_id)
        self.worker.response_received.connect(self.handle_response)
        self.worker.error_occurred.connect(self.handle_error)
        self.worker.start()
        
    def handle_response(self, response, conversation_id):
        self.ask_btn.setEnabled(True)
        self.status_bar.showMessage("Response received")
        
        print(f"Storing response in conversation: {conversation_id}")
        print(f"Current context before adding: {len(self.conversation_context.get(conversation_id, []))} messages")

        # Update conversation context
        if conversation_id in self.conversation_context:
            prompt = self.prompt_input.toPlainText()

            # Add the user message and assistant response
            self.conversation_context[conversation_id].append({"role": "user", "content": prompt})
            self.conversation_context[conversation_id].append({"role": "assistant", "content": response})
            
            # Update token count with response only (prompt was already counted)
            response_tokens = self.estimate_tokens(response)
            self.current_tokens += response_tokens
            self.update_token_count()

        print(f"Context after adding: {len(self.conversation_context.get(conversation_id, []))} messages")

        # Convert markdown to HTML with WordPress styling
        html_response = markdown.markdown(response)
        
        formatted_html = f"""
        <div style="background-color: #2c3338; color: #f1f1f1; padding: 15px; border-radius: 5px; border: 1px solid #0073aa;">
            {html_response}
        </div>
        """
        self.response_area.setHtml(formatted_html)
        
        # Save to conversation history
        self.conversation_history.append({
            "timestamp": datetime.now().timestamp(),
            "conversation_id": conversation_id,
            "prompt": self.prompt_input.toPlainText(),
            "response": response
        })
        
        # Update conversation list
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        self.conversation_list.addItem(f"[{timestamp}] {self.prompt_input.toPlainText()[:30]}...")
        
        # Clear the prompt input
        self.prompt_input.clear()
        
    def handle_error(self, error_msg):
        self.ask_btn.setEnabled(True)
        self.status_bar.showMessage("Error occurred")
        self.response_area.setPlainText(f"Error: {error_msg}")
        
    def clear_chat(self):
        self.response_area.clear()
        self.prompt_input.clear()
        
    def set_api_key(self):
        key, ok = QInputDialog.getText(self, "API Key", "Enter your DeepSeek API Key:")
        if ok and key:
            self.api_key = key
            self.save_settings()
            self.status_bar.showMessage("API key set successfully")
            
    def load_settings(self):
        try:
            if os.path.exists("wp_assistant_settings.json"):
                with open("wp_assistant_settings.json", "r") as f:
                    settings = json.load(f)
                    self.api_key = settings.get("api_key")
                    self.conversation_history = settings.get("conversation_history", [])
                    self.conversation_context = settings.get("conversation_context", {})
                    
                    # Update conversation list
                    for conv in self.conversation_history:
                        timestamp = datetime.fromtimestamp(conv["timestamp"]).strftime("%Y-%m-%d %H:%M")
                        self.conversation_list.addItem(f"[{timestamp}] {conv['prompt'][:30]}...")
        except:
            self.api_key = None
            self.conversation_history = []
            self.conversation_context = {}
            
    def save_settings(self):
        try:
            with open("wp_assistant_settings.json", "w") as f:
                json.dump({
                    "api_key": self.api_key,
                    "conversation_history": self.conversation_history,
                    "conversation_context": self.conversation_context
                }, f)
        except Exception as e:
            print(f"Error saving settings: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WordPressAssistant()
    window.show()
    sys.exit(app.exec())
