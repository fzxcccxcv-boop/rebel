# REBEL HOSTING BOT - (OWNER PANEL, BACKUP SYSTEM, TIER CAPS, AST CUSTOMIZER, AUTO-RESTART & 🖥️ SMALL TERMINAL)

import telebot
import subprocess
import os
import zipfile
import tempfile
import shutil
from telebot import types
import time
from datetime import datetime, timedelta
import psutil
import sqlite3
import json
import logging
import signal
import threading
import re
import sys
import atexit
import requests
import hashlib
import mimetypes
import struct
import uuid
import ast

# --- Flask Keep Alive ---
from flask import Flask
from threading import Thread

app = Flask(__name__)

@app.route('/')
def home():
    return "bot is running...."

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    for _ in range(10):
        try:
            # use_reloader=False is required for background threads on Windows
            app.run(host='0.0.0.0', port=port, use_reloader=False)
            break
        except OSError as e:
            # 98: Linux, 48: macOS, 10048: Windows WSAEADDRINUSE
            if "Address already in use" in str(e) or (hasattr(e, 'errno') and e.errno in (98, 48, 10048)):
                print(f"Port {port} is in use, trying port {port + 1}...")
                port += 1
            else:
                print(f"Flask keep-alive error: {e}")
                break
        except Exception as e:
            print(f"Unexpected Flask error: {e}")
            break

def keep_alive():
    t = Thread(target=run_flask, daemon=True)
    t.start()
    print("Flask Keep-Alive server started.")
# --- End Flask Keep Alive ---

# --- Configuration ---
TOKEN = '8964561893:AAEdqAJuJ2kxrfuwLeXrpbtKa3psxaJnt3o'
OWNER_ID = 8976761358
ADMIN_ID = 7499791505
YOUR_USERNAME = '@Kengofaws'
UPDATE_CHANNEL = '@cudaipurog'

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_BOTS_DIR = os.path.join(BASE_DIR, 'upload_bots')
IROTECH_DIR = os.path.join(BASE_DIR, 'inf')
DATABASE_PATH = os.path.join(IROTECH_DIR, 'bot_data.db')

FREE_USER_LIMIT = 5
SUBSCRIBED_USER_LIMIT = 19
ADMIN_LIMIT = 49
OWNER_LIMIT = float('inf')

# --- Security, Per-Tier Resource Caps & Container Settings ---
DEFAULT_AST_BLOCKED_MODULES = {
    'pty', 'ctypes', 'winreg', 'mmap', 'fcntl', 'resource', 'grp', 'pwd', 'spwd'
}
DANGEROUS_PY_IMPORTS = set(DEFAULT_AST_BLOCKED_MODULES)

TIER_RESOURCE_LIMITS = {
    'free': {'ram_mb': 256, 'cpu_pct': 60.0},
    'premium': {'ram_mb': 512, 'cpu_pct': 85.0},
    'admin': {'ram_mb': 1024, 'cpu_pct': 95.0}
}

CPU_OVERLOAD_STRIKES_LIMIT = 4              # Consecutive high-CPU checks before termination
MAX_AUTO_RESTART_CRASHES = 5                # Max consecutive auto-restarts before disabling
MAX_ZIP_EXTRACTED_SIZE = 100 * 1024 * 1024  # 100 MB Zip-Bomb cap
DOCKER_BIN = shutil.which('docker') or shutil.which('docker.exe')
USE_DOCKER_SANDBOX = False                  # Can be toggled live from Owner Panel

os.makedirs(UPLOAD_BOTS_DIR, exist_ok=True)
os.makedirs(IROTECH_DIR, exist_ok=True)

bot = telebot.TeleBot(TOKEN)

# --- Module Aliases Dictionary (Defined Early) ---
TELEGRAM_MODULES = {
    'telebot': 'pyTelegramBotAPI', 'telegram': 'python-telegram-bot', 'python_telegram_bot': 'python-telegram-bot',
    'aiogram': 'aiogram', 'pyrogram': 'pyrogram', 'telethon': 'telethon', 'telethon.sync': 'telethon',
    'from telethon.sync import telegramclient': 'telethon', 'telepot': 'telepot', 'pytg': 'pytg',
    'tgcrypto': 'tgcrypto', 'bs4': 'beautifulsoup4', 'requests': 'requests', 'pillow': 'Pillow',
    'cv2': 'opencv-python', 'yaml': 'PyYAML', 'dotenv': 'python-dotenv', 'dateutil': 'python-dateutil',
    'pandas': 'pandas', 'numpy': 'numpy', 'flask': 'Flask', 'django': 'Django', 'sqlalchemy': 'SQLAlchemy',
    'psutil': 'psutil'
}

# --- Data structures ---
bot_scripts = {}
user_subscriptions = {}
user_files = {}
active_users = set()
admin_ids = {ADMIN_ID, OWNER_ID}
banned_users = set()
authenticated_users = set()
username_to_id = {}
bot_locked = False
pending_approvals = {}
script_security_reports = {}
auto_restart_scripts = set()     # Stores script_keys ("{user_id}_{file_name}") with Auto-Restart ON
crash_restart_counts = {}        # Tracks crash counts per script_key
terminal_sessions = {}           # [TERMINAL] user_id -> True when terminal session is active

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Node and NPM executable resolution for Windows
NODE_BIN = shutil.which('node') or shutil.which('node.exe') or 'node'
NPM_BIN = shutil.which('npm') or shutil.which('npm.cmd') or ('npm.cmd' if os.name == 'nt' else 'npm')

# --- Command Button Layouts ---
COMMAND_BUTTONS_LAYOUT_USER_SPEC = [          # [TERMINAL] added
    ["📢 Updates Channel"],
    ["📤 Upload File", "📂 Check Files"],
    ["🖥️ Terminal"],
    ["⚡ Bot Speed", "📊 Statistics"],
    ["📤 Send Command", "📞 Contact Owner"]
]
ADMIN_COMMAND_BUTTONS_LAYOUT_USER_SPEC = [    # [TERMINAL] added
    ["📢 Updates Channel"],
    ["📤 Upload File", "📂 Check Files"],
    ["🖥️ Terminal"],
    ["⚡ Bot Speed", "📊 Statistics"],
    ["💳 Subscriptions", "📢 Broadcast"],
    ["🔒 Lock Bot", "🟢 Running All Code"],
    ["📤 Send Command", "👑 Admin Panel"],
    ["👑 Owner Panel", "📞 Contact Owner"]
]

# --- Colorful Inline Button Helper (Telegram Bot API 9.4+ / 2026 Support) ---
def colorful_btn(text, callback_data=None, url=None, style=None):
    """
    Creates an InlineKeyboardButton and attaches the Telegram Bot API `style`
    property ('primary' = Blue, 'success' = Green, 'danger' = Red) for colorful buttons.
    """
    btn = types.InlineKeyboardButton(text, callback_data=callback_data, url=url)
    if style:
        btn.style = style
    return btn

_orig_btn_to_dict = types.InlineKeyboardButton.to_dict
def _patched_btn_to_dict(self):
    data = _orig_btn_to_dict(self)
    if getattr(self, 'style', None):
        data['style'] = self.style
    return data
types.InlineKeyboardButton.to_dict = _patched_btn_to_dict

# --- AST Static Security Scanner & Zip-Slip Protection ---
HIGH_RISK_PY_CALLS = {
    'eval', 'exec', 'compile', '__import__'
}
SENSITIVE_PATTERNS = [
    r'bot_data\.db',
    r'upload_bots',
    r'8964561893:',  # Protecting host bot token
    r'rm\s+-rf\s+/',
    r'format\s+[a-zA-Z]:',
    r'del\s+/[fFsS]',
    r'nc\s+-e',
    r'/dev/tcp/'
]

class PythonASTSecurityVisitor(ast.NodeVisitor):
    def __init__(self):
        self.issues = []
        self.critical = False

    def visit_Import(self, node):
        for alias in node.names:
            root_mod = alias.name.split('.')[0].strip()
            if root_mod in DANGEROUS_PY_IMPORTS:
                self.issues.append(f"🚨 Blocked import: `{alias.name}` (Line {node.lineno})")
                self.critical = True
            elif root_mod in ('subprocess', 'shutil'):
                self.issues.append(f"ℹ️ System module imported: `{alias.name}` (Line {node.lineno})")
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module:
            root_mod = node.module.split('.')[0].strip()
            if root_mod in DANGEROUS_PY_IMPORTS:
                self.issues.append(f"🚨 Blocked import from: `{node.module}` (Line {node.lineno})")
                self.critical = True
            elif root_mod in ('subprocess', 'shutil'):
                self.issues.append(f"ℹ️ System module imported: `{node.module}` (Line {node.lineno})")
        self.generic_visit(node)

    def visit_Call(self, node):
        func_name = ""
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                func_name = f"{node.func.value.id}.{node.func.attr}"
            else:
                func_name = node.func.attr

        if func_name in HIGH_RISK_PY_CALLS:
            self.issues.append(f"⚠️ Dynamic code execution `{func_name}()` (Line {node.lineno})")
        elif func_name in ('os.system', 'os.popen', 'subprocess.Popen', 'subprocess.run', 'subprocess.call'):
            self.issues.append(f"⚠️ Shell/Subprocess execution `{func_name}()` (Line {node.lineno})")
        elif func_name in ('shutil.rmtree', 'os.remove', 'os.unlink'):
            for arg in node.args:
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    if '..' in arg.value or arg.value.startswith(('/', '\\', 'C:', 'c:')):
                        self.issues.append(f"🚨 CRITICAL: Path traversal deletion `{func_name}('{arg.value}')` (Line {node.lineno})")
                        self.critical = True
        self.generic_visit(node)

def scan_script_security(file_path, file_type='py'):
    """
    Runs AST static security analysis on Python scripts and pattern scanning on JS/Py files.
    Returns (is_safe_for_user, risk_level, issues_list)
    """
    issues = []
    critical = False
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        for pattern in SENSITIVE_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                issues.append(f"🚨 CRITICAL: Matched blocked security pattern `{pattern}`")
                critical = True

        if file_type == 'py':
            try:
                tree = ast.parse(content, filename=os.path.basename(file_path))
                visitor = PythonASTSecurityVisitor()
                visitor.visit(tree)
                issues.extend(visitor.issues)
                if visitor.critical:
                    critical = True
            except SyntaxError as se:
                issues.append(f"⚠️ Python Syntax Error at line {se.lineno}: {se.msg}")
        elif file_type == 'js':
            js_checks = [
                (r'child_process', "⚠️ Uses Node `child_process` module"),
                (r'\beval\s*\(', "⚠️ Uses dynamic `eval()`"),
                (r'fs\.(rmSync|rmdirSync|unlinkSync)\s*\(\s*[\'"`]\.\.', "🚨 CRITICAL: Parent directory deletion attempt")
            ]
            for pat, msg in js_checks:
                if re.search(pat, content):
                    issues.append(msg)
                    if "CRITICAL" in msg:
                        critical = True

    except Exception as e:
        issues.append(f"⚠️ Could not complete scan: {e}")

    if critical:
        risk_level = "🔴 CRITICAL RISK"
    elif issues:
        risk_level = "🟡 MODERATE WARNING"
    else:
        risk_level = "🟢 CLEAN (PASSED)"

    return (not critical), risk_level, issues[:8]

def safe_extract_zip(zip_path, extract_to):
    """
    Safely extracts a ZIP archive preventing Zip-Slip path traversal and Zip-Bomb attacks.
    """
    total_uncompressed = 0
    abs_extract_to = os.path.abspath(extract_to)

    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        for member in zip_ref.infolist():
            total_uncompressed += member.file_size
            if total_uncompressed > MAX_ZIP_EXTRACTED_SIZE:
                raise ValueError(f"Archive exceeds maximum uncompressed limit ({MAX_ZIP_EXTRACTED_SIZE // (1024*1024)} MB).")

            member_path = os.path.abspath(os.path.join(abs_extract_to, member.filename))
            if not member_path.startswith(abs_extract_to + os.sep) and member_path != abs_extract_to:
                raise ValueError(f"Zip-Slip path traversal blocked: {member.filename}")

        zip_ref.extractall(abs_extract_to)

# --- Windows Safe File Helpers ---
def safe_remove(path, retries=5, delay=0.5):
    if not os.path.exists(path):
        return
    for _ in range(retries):
        try:
            os.remove(path)
            return
        except PermissionError:
            time.sleep(delay)
        except Exception:
            break
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception as e:
        logger.warning(f"Could not remove file {path}: {e}")

def safe_rmtree(path, retries=5, delay=0.5):
    if not os.path.exists(path):
        return
    for _ in range(retries):
        try:
            shutil.rmtree(path)
            return
        except PermissionError:
            time.sleep(delay)
        except Exception:
            break
    try:
        if os.path.exists(path):
            shutil.rmtree(path, ignore_errors=True)
    except Exception as e:
        logger.warning(f"Could not remove folder {path}: {e}")

# --- Database Setup ---
DB_LOCK = threading.Lock()

def init_db():
    logger.info(f"Initializing database at: {DATABASE_PATH}")
    with DB_LOCK:
        try:
            conn = sqlite3.connect(DATABASE_PATH, timeout=30, check_same_thread=False)
            c = conn.cursor()
            c.execute('''CREATE TABLE IF NOT EXISTS subscriptions (user_id INTEGER PRIMARY KEY, expiry TEXT)''')
            c.execute('''CREATE TABLE IF NOT EXISTS user_files (user_id INTEGER, file_name TEXT, file_type TEXT, PRIMARY KEY (user_id, file_name))''')
            c.execute('''CREATE TABLE IF NOT EXISTS active_users (user_id INTEGER PRIMARY KEY)''')
            c.execute('''CREATE TABLE IF NOT EXISTS admins (user_id INTEGER PRIMARY KEY)''')
            c.execute('''CREATE TABLE IF NOT EXISTS banned_users (user_id INTEGER PRIMARY KEY)''')
            c.execute('''CREATE TABLE IF NOT EXISTS user_usernames (username TEXT PRIMARY KEY, user_id INTEGER)''')
            c.execute('''CREATE TABLE IF NOT EXISTS auth_users (user_id INTEGER PRIMARY KEY)''')
            c.execute('''CREATE TABLE IF NOT EXISTS ast_blocked_modules (module_name TEXT PRIMARY KEY)''')
            c.execute('''CREATE TABLE IF NOT EXISTS tier_limits (tier TEXT PRIMARY KEY, ram_mb INTEGER, cpu_pct REAL)''')
            c.execute('''CREATE TABLE IF NOT EXISTS auto_restart_prefs (user_id INTEGER, file_name TEXT, enabled INTEGER, PRIMARY KEY (user_id, file_name))''')

            c.execute('INSERT OR IGNORE INTO admins (user_id) VALUES (?)', (OWNER_ID,))
            if ADMIN_ID != OWNER_ID:
                c.execute('INSERT OR IGNORE INTO admins (user_id) VALUES (?)', (ADMIN_ID,))

            c.execute('SELECT COUNT(*) FROM ast_blocked_modules')
            if c.fetchone()[0] == 0:
                for mod in DEFAULT_AST_BLOCKED_MODULES:
                    c.execute('INSERT OR IGNORE INTO ast_blocked_modules (module_name) VALUES (?)', (mod,))

            for tier_name, limits in TIER_RESOURCE_LIMITS.items():
                c.execute('INSERT OR IGNORE INTO tier_limits (tier, ram_mb, cpu_pct) VALUES (?, ?, ?)',
                          (tier_name, limits['ram_mb'], limits['cpu_pct']))

            conn.commit()
            conn.close()
            logger.info("Database initialized successfully.")
        except Exception as e:
            logger.error(f"❌ Database initialization error: {e}", exc_info=True)

def load_data():
    logger.info("Loading data from database...")
    with DB_LOCK:
        try:
            conn = sqlite3.connect(DATABASE_PATH, timeout=30, check_same_thread=False)
            c = conn.cursor()

            c.execute('SELECT user_id, expiry FROM subscriptions')
            for user_id, expiry in c.fetchall():
                try:
                    user_subscriptions[user_id] = {'expiry': datetime.fromisoformat(expiry)}
                except ValueError:
                    pass

            c.execute('SELECT user_id, file_name, file_type FROM user_files')
            for user_id, file_name, file_type in c.fetchall():
                if user_id not in user_files:
                    user_files[user_id] = []
                user_files[user_id].append((file_name, file_type))

            c.execute('SELECT user_id FROM active_users')
            active_users.update(user_id for (user_id,) in c.fetchall())

            c.execute('SELECT user_id FROM admins')
            admin_ids.update(user_id for (user_id,) in c.fetchall())

            c.execute('SELECT user_id FROM banned_users')
            banned_users.update(user_id for (user_id,) in c.fetchall())

            c.execute('SELECT username, user_id FROM user_usernames')
            for uname, uid in c.fetchall():
                username_to_id[uname.lower()] = uid

            c.execute('SELECT user_id FROM auth_users')
            authenticated_users.update(user_id for (user_id,) in c.fetchall())

            c.execute('SELECT module_name FROM ast_blocked_modules')
            db_mods = {row[0] for row in c.fetchall()}
            if db_mods:
                DANGEROUS_PY_IMPORTS.clear()
                DANGEROUS_PY_IMPORTS.update(db_mods)

            c.execute('SELECT tier, ram_mb, cpu_pct FROM tier_limits')
            for tier_name, ram_mb, cpu_pct in c.fetchall():
                TIER_RESOURCE_LIMITS[tier_name] = {'ram_mb': int(ram_mb), 'cpu_pct': float(cpu_pct)}

            c.execute('SELECT user_id, file_name, enabled FROM auto_restart_prefs')
            for uid, fname, enabled in c.fetchall():
                if enabled:
                    auto_restart_scripts.add(f"{uid}_{fname}")

            conn.close()
            logger.info(f"Data loaded: {len(active_users)} users, {len(DANGEROUS_PY_IMPORTS)} blocked AST modules, {len(auto_restart_scripts)} auto-restart scripts.")
        except Exception as e:
            logger.error(f"❌ Error loading data: {e}", exc_info=True)

init_db()
load_data()

# --- Tier Resource Limit & DB Persistence Helpers ---
def get_user_resource_limits(user_id):
    """Returns (ram_mb, cpu_pct, tier_label) based on the user's tier."""
    if user_id == OWNER_ID:
        return float('inf'), 100.0, "👑 Owner (Unlimited)"
    if user_id in admin_ids:
        cfg = TIER_RESOURCE_LIMITS.get('admin', {'ram_mb': 1024, 'cpu_pct': 95.0})
        return cfg['ram_mb'], cfg['cpu_pct'], "🛡️ Admin"
    if user_id in user_subscriptions and user_subscriptions[user_id].get('expiry', datetime.min) > datetime.now():
        cfg = TIER_RESOURCE_LIMITS.get('premium', {'ram_mb': 512, 'cpu_pct': 85.0})
        return cfg['ram_mb'], cfg['cpu_pct'], "⭐ Premium"
    cfg = TIER_RESOURCE_LIMITS.get('free', {'ram_mb': 256, 'cpu_pct': 60.0})
    return cfg['ram_mb'], cfg['cpu_pct'], "🆓 Free"

def update_tier_limit_db(tier, ram_mb, cpu_pct):
    TIER_RESOURCE_LIMITS[tier] = {'ram_mb': int(ram_mb), 'cpu_pct': float(cpu_pct)}
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, timeout=30, check_same_thread=False)
        c = conn.cursor()
        try:
            c.execute('INSERT OR REPLACE INTO tier_limits (tier, ram_mb, cpu_pct) VALUES (?, ?, ?)', (tier, int(ram_mb), float(cpu_pct)))
            conn.commit()
        except Exception: pass
        finally: conn.close()

def add_ast_module_db(mod_name):
    mod_name = mod_name.strip().lower()
    if not mod_name: return
    DANGEROUS_PY_IMPORTS.add(mod_name)
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, timeout=30, check_same_thread=False)
        c = conn.cursor()
        try:
            c.execute('INSERT OR IGNORE INTO ast_blocked_modules (module_name) VALUES (?)', (mod_name,))
            conn.commit()
        except Exception: pass
        finally: conn.close()

def remove_ast_module_db(mod_name):
    mod_name = mod_name.strip().lower()
    DANGEROUS_PY_IMPORTS.discard(mod_name)
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, timeout=30, check_same_thread=False)
        c = conn.cursor()
        try:
            c.execute('DELETE FROM ast_blocked_modules WHERE module_name = ?', (mod_name,))
            conn.commit()
        except Exception: pass
        finally: conn.close()

def reset_ast_modules_db():
    DANGEROUS_PY_IMPORTS.clear()
    DANGEROUS_PY_IMPORTS.update(DEFAULT_AST_BLOCKED_MODULES)
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, timeout=30, check_same_thread=False)
        c = conn.cursor()
        try:
            c.execute('DELETE FROM ast_blocked_modules')
            for mod in DEFAULT_AST_BLOCKED_MODULES:
                c.execute('INSERT OR IGNORE INTO ast_blocked_modules (module_name) VALUES (?)', (mod,))
            conn.commit()
        except Exception: pass
        finally: conn.close()

def set_auto_restart_db(user_id, file_name, enabled):
    script_key = f"{user_id}_{file_name}"
    if enabled:
        auto_restart_scripts.add(script_key)
        crash_restart_counts[script_key] = 0
    else:
        auto_restart_scripts.discard(script_key)
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, timeout=30, check_same_thread=False)
        c = conn.cursor()
        try:
            c.execute('INSERT OR REPLACE INTO auto_restart_prefs (user_id, file_name, enabled) VALUES (?, ?, ?)',
                      (user_id, file_name, 1 if enabled else 0))
            conn.commit()
        except Exception: pass
        finally: conn.close()

# --- Owner Full Backup System (Database + All User Files) ---
SKIP_BACKUP_DIRS = {'node_modules', '__pycache__', '.git', 'venv', '.venv', 'env'}

def build_backup_zip(zip_filepath, skip_logs=False):
    """
    Packages a safe SQLite snapshot of bot_data.db and all user scripts/files into zip_filepath.
    Returns (user_folders_count, files_archived_count).
    """
    temp_db_copy = zip_filepath + "_temp.db"
    files_archived = 0
    user_folders = set()

    try:
        # 1. Perform safe online SQLite backup
        if os.path.exists(DATABASE_PATH):
            with DB_LOCK:
                src_conn = sqlite3.connect(DATABASE_PATH, timeout=30, check_same_thread=False)
                dst_conn = sqlite3.connect(temp_db_copy)
                try:
                    src_conn.backup(dst_conn)
                finally:
                    dst_conn.close()
                    src_conn.close()

        # 2. Write database & user files into the ZIP archive
        with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zf:
            if os.path.exists(temp_db_copy):
                zf.write(temp_db_copy, arcname=os.path.join('inf', 'bot_data.db'))
                files_archived += 1

            if os.path.exists(UPLOAD_BOTS_DIR):
                for root, dirs, files in os.walk(UPLOAD_BOTS_DIR):
                    dirs[:] = [d for d in dirs if d not in SKIP_BACKUP_DIRS]
                    for file in files:
                        if skip_logs and file.endswith('.log'):
                            continue
                        full_path = os.path.join(root, file)
                        rel_path = os.path.relpath(full_path, BASE_DIR)
                        parts = rel_path.split(os.sep)
                        if len(parts) >= 2 and parts[0] == 'upload_bots':
                            user_folders.add(parts[1])
                        try:
                            zf.write(full_path, arcname=rel_path)
                            files_archived += 1
                        except Exception as e:
                            logger.warning(f"Could not archive {full_path}: {e}")
    finally:
        safe_remove(temp_db_copy)

    return len(user_folders), files_archived

def execute_owner_backup(chat_id):
    """Runs in a background thread to build and send the full backup ZIP to the Owner."""
    temp_dir = None
    try:
        status_msg = bot.send_message(chat_id, "⏳ *Creating full backup of SQLite Database & all User Files...*", parse_mode='Markdown')
        temp_dir = tempfile.mkdtemp(prefix="rebel_backup_")
        timestamp_str = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        zip_filename = f"rebel_backup_{timestamp_str}.zip"
        zip_filepath = os.path.join(temp_dir, zip_filename)

        user_folders_count, files_count = build_backup_zip(zip_filepath, skip_logs=False)
        zip_size_mb = os.path.getsize(zip_filepath) / (1024 * 1024)
        note_str = "Included (Full DB + Scripts + Logs)"

        # Fallback if log files push the archive over Telegram's 50 MB Bot API limit
        if zip_size_mb > 49.0:
            safe_remove(zip_filepath)
            user_folders_count, files_count = build_backup_zip(zip_filepath, skip_logs=True)
            zip_size_mb = os.path.getsize(zip_filepath) / (1024 * 1024)
            note_str = "DB + Scripts only (.log files skipped to stay under 50MB limit)"

        caption = (
            f"💾 *Full System Backup Completed!*\n\n"
            f"📅 *Timestamp:* `{timestamp_str}`\n"
            f"🗄️ *Database:* `inf/bot_data.db` (`{len(active_users)}` users)\n"
            f"📁 *User Folders:* `{user_folders_count}`\n"
            f"📄 *Total Files Archived:* `{files_count}`\n"
            f"📦 *Archive Size:* `{zip_size_mb:.2f} MB`\n"
            f"ℹ️ *Contents:* {note_str}"
        )

        with open(zip_filepath, 'rb') as f:
            bot.send_document(chat_id, f, caption=caption, parse_mode='Markdown')

        if status_msg:
            try:
                bot.delete_message(chat_id, status_msg.message_id)
            except Exception:
                pass
    except Exception as e:
        logger.error(f"Backup error: {e}", exc_info=True)
        try:
            bot.send_message(chat_id, f"❌ *Backup Failed:* `{str(e)}`", parse_mode='Markdown')
        except Exception:
            pass
    finally:
        if temp_dir and os.path.exists(temp_dir):
            safe_rmtree(temp_dir)

# --- Helper Functions ---
def safe_reply(message_obj, text, **kwargs):
    try:
        if len(text) > 4000:
            text = text[:3900] + "\n... (Message truncated)"
        chat_id = getattr(getattr(message_obj, 'chat', None), 'id', None)
        msg_id = getattr(message_obj, 'message_id', None)

        if msg_id and chat_id:
            return bot.reply_to(message_obj, text, **kwargs)
        elif chat_id:
            return bot.send_message(chat_id, text, **kwargs)
    except Exception as e:
        logger.warning(f"Could not send notification: {e}")
        return None

class PseudoMessage:
    def __init__(self, from_user, chat_id=None):
        self.chat = type('Chat', (), {'id': chat_id if chat_id is not None else from_user.id})()
        self.from_user = from_user
        self.message_id = None

def check_joined(user_id, chat_id, is_callback=False, call_id=None):
    if user_id in banned_users:
        msg = "❌ You have been banned from using this bot by the Owner."
        if is_callback and call_id:
            try: bot.answer_callback_query(call_id, msg, show_alert=True)
            except Exception: pass
        else:
            try: bot.send_message(chat_id, msg)
            except Exception: pass
        return False

    if user_id in admin_ids or user_id == OWNER_ID:
        return True
    try:
        member = bot.get_chat_member(UPDATE_CHANNEL, user_id)
        if member.status in ['member', 'administrator', 'creator']:
            return True
    except Exception:
        pass

    markup = types.InlineKeyboardMarkup()
    channel_url = f"https://t.me/{UPDATE_CHANNEL.replace('@', '')}"
    markup.add(colorful_btn('📢 Join Channel', url=channel_url, style='primary'))
    markup.add(colorful_btn('🔄 Verify Membership', callback_data='verify_join', style='success'))

    if is_callback and call_id:
        try: bot.answer_callback_query(call_id, "⚠️ You must join our updates channel first!", show_alert=True)
        except Exception: pass

    try: bot.send_message(chat_id, f"❌ *Access Denied!*\n\nYou must be a member of our updates channel ({UPDATE_CHANNEL}) to use this bot.\n\nJoin the channel and click *Verify Membership*.", reply_markup=markup, parse_mode='Markdown')
    except Exception: pass
    return False

def get_user_folder(user_id):
    user_folder = os.path.join(UPLOAD_BOTS_DIR, str(user_id))
    os.makedirs(user_folder, exist_ok=True)
    return user_folder

def get_user_file_limit(user_id):
    if user_id == OWNER_ID: return OWNER_LIMIT
    if user_id in admin_ids: return ADMIN_LIMIT
    if user_id in user_subscriptions and user_subscriptions[user_id]['expiry'] > datetime.now(): return SUBSCRIBED_USER_LIMIT
    return FREE_USER_LIMIT

def get_user_file_count(user_id):
    return len(user_files.get(user_id, []))

def is_bot_running(script_owner_id, file_name):
    script_key = f"{script_owner_id}_{file_name}"
    script_info = bot_scripts.get(script_key)
    if not script_info:
        return False

    process = script_info.get('process')
    if not process:
        return False

    if process.poll() is not None:
        return False

    try:
        proc = psutil.Process(process.pid)
        is_running = proc.is_running() and (not hasattr(psutil, 'STATUS_ZOMBIE') or proc.status() != psutil.STATUS_ZOMBIE)
        return is_running
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return False
    except Exception:
        return False

def kill_process_tree(process_info):
    pid = None
    script_key = process_info.get('script_key', 'N/A')

    container_name = process_info.get('container_name')
    if container_name and DOCKER_BIN:
        try:
            subprocess.run([DOCKER_BIN, 'rm', '-f', container_name], capture_output=True, timeout=10, check=False)
        except Exception:
            pass

    try:
        process = process_info.get('process')
        if process and hasattr(process, 'pid'):
            pid = process.pid
            if pid:
                try:
                    parent = psutil.Process(pid)
                    children = parent.children(recursive=True)
                    for child in children:
                        try: child.kill()
                        except (psutil.NoSuchProcess, psutil.AccessDenied): pass
                    try: parent.kill()
                    except (psutil.NoSuchProcess, psutil.AccessDenied): pass
                except (psutil.NoSuchProcess, psutil.AccessDenied): pass
                except Exception as e:
                    logger.warning(f"psutil termination warning for PID {pid}: {e}")

                if os.name == 'nt':
                    try:
                        subprocess.run(['taskkill', '/F', '/T', '/PID', str(pid)], capture_output=True, check=False)
                    except Exception: pass

        if 'log_file' in process_info and hasattr(process_info['log_file'], 'close'):
            try:
                if not process_info['log_file'].closed:
                    process_info['log_file'].close()
            except Exception: pass
    except Exception as e:
        logger.error(f"❌ Unexpected error killing process tree for PID {pid or 'N/A'} ({script_key}): {e}")

# --- Process Resource Caps Watchdog & Auto-Restart Engine ---
def get_process_tree_stats(pid):
    """Returns total (memory_mb, cpu_percent, thread_count) for a process and all its children."""
    try:
        parent = psutil.Process(pid)
        procs = [parent] + parent.children(recursive=True)
        total_mem = 0
        total_cpu = 0.0
        total_threads = 0
        for p in procs:
            try:
                total_mem += p.memory_info().rss
                total_cpu += p.cpu_percent(interval=0.05)
                total_threads += p.num_threads()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return round(total_mem / (1024 * 1024), 2), round(total_cpu, 1), total_threads
    except Exception:
        return 0.0, 0.0, 0

def resource_watchdog_loop():
    """
    Background daemon that:
    1. Monitors crashed scripts and triggers Auto-Restart if enabled.
    2. Enforces per-tier RAM and CPU caps on all running scripts.
    """
    while True:
        try:
            for script_key, script_info in list(bot_scripts.items()):
                process = script_info.get('process')
                owner_id = script_info.get('script_owner_id')
                file_name = script_info.get('file_name')
                user_folder = script_info.get('user_folder')
                file_type = script_info.get('type', 'py')
                chat_id = script_info.get('chat_id', owner_id)

                if not process or process.poll() is not None:
                    if 'log_file' in script_info and hasattr(script_info['log_file'], 'close'):
                        try:
                            if not script_info['log_file'].closed:
                                script_info['log_file'].close()
                        except Exception: pass

                    manual_stop = script_info.get('manual_stop', False)
                    killed_by_watchdog = script_info.get('killed_by_watchdog', False)
                    bot_scripts.pop(script_key, None)

                    if script_key in auto_restart_scripts and not manual_stop and not killed_by_watchdog:
                        crashes = crash_restart_counts.get(script_key, 0) + 1
                        crash_restart_counts[script_key] = crashes
                        script_path = os.path.join(user_folder, file_name)

                        if crashes <= MAX_AUTO_RESTART_CRASHES and os.path.exists(script_path):
                            logger.info(f"🔁 Auto-restarting crashed script {script_key} (Attempt {crashes}/{MAX_AUTO_RESTART_CRASHES})")
                            try:
                                bot.send_message(
                                    chat_id,
                                    f"🔁 *Auto-Restart Triggered!*\nScript `{file_name}` exited unexpectedly. Restarting (`{crashes}/{MAX_AUTO_RESTART_CRASHES}`)...",
                                    parse_mode='Markdown'
                                )
                            except Exception: pass
                            dummy_user = type('User', (), {'id': owner_id, 'first_name': 'AutoRestart', 'username': None})()
                            dummy_msg = PseudoMessage(dummy_user, chat_id)
                            if file_type == 'py':
                                threading.Thread(target=run_script, args=(script_path, owner_id, user_folder, file_name, dummy_msg), daemon=True).start()
                            elif file_type == 'js':
                                threading.Thread(target=run_js_script, args=(script_path, owner_id, user_folder, file_name, dummy_msg), daemon=True).start()
                        elif crashes > MAX_AUTO_RESTART_CRASHES:
                            set_auto_restart_db(owner_id, file_name, False)
                            try:
                                bot.send_message(
                                    chat_id,
                                    f"⚠️ *Auto-Restart Disabled for `{file_name}`*\nScript crashed {MAX_AUTO_RESTART_CRASHES} times consecutively. Check logs before restarting.",
                                    parse_mode='Markdown'
                                )
                            except Exception: pass
                    continue

                if (datetime.now() - script_info.get('start_time', datetime.now())).total_seconds() > 180:
                    crash_restart_counts[script_key] = 0

                if owner_id == OWNER_ID:
                    continue

                max_ram_mb, max_cpu_pct, tier_label = get_user_resource_limits(owner_id)
                mem_mb, cpu_pct, _ = get_process_tree_stats(process.pid)
                script_info['peak_mem_mb'] = max(script_info.get('peak_mem_mb', 0.0), mem_mb)

                if mem_mb > max_ram_mb:
                    script_info['killed_by_watchdog'] = True
                    kill_process_tree(script_info)
                    bot_scripts.pop(script_key, None)
                    logger.warning(f"🚨 Watchdog killed {script_key}: Memory exceeded ({mem_mb} MB > {max_ram_mb} MB)")
                    try:
                        bot.send_message(
                            chat_id,
                            f"🚨 *Tier RAM Limit Exceeded!*\n\nScript `{file_name}` was terminated because it used `{mem_mb} MB` RAM (Your {tier_label} Limit: `{max_ram_mb} MB`).",
                            parse_mode='Markdown'
                        )
                    except Exception: pass
                    continue

                if cpu_pct > max_cpu_pct:
                    strikes = script_info.get('cpu_strikes', 0) + 1
                    script_info['cpu_strikes'] = strikes
                    if strikes >= CPU_OVERLOAD_STRIKES_LIMIT:
                        script_info['killed_by_watchdog'] = True
                        kill_process_tree(script_info)
                        bot_scripts.pop(script_key, None)
                        logger.warning(f"🚨 Watchdog killed {script_key}: Sustained CPU overload ({cpu_pct}%)")
                        try:
                            bot.send_message(
                                chat_id,
                                f"🚨 *Tier CPU Limit Exceeded!*\n\nScript `{file_name}` was terminated due to sustained high CPU usage (`{cpu_pct}%`, Your {tier_label} Limit: `{max_cpu_pct}%`).",
                                parse_mode='Markdown'
                            )
                        except Exception: pass
                else:
                    script_info['cpu_strikes'] = 0
        except Exception as e:
            logger.debug(f"Watchdog loop warning: {e}")
        time.sleep(5)

def request_run_script(file_type, file_path, script_owner_id, user_folder, file_name, message, requesting_user_id=None):
    if requesting_user_id is None:
        if hasattr(message, 'from_user') and message.from_user:
            requesting_user_id = message.from_user.id
        elif hasattr(message, 'chat') and message.chat:
            requesting_user_id = message.chat.id
        else:
            requesting_user_id = script_owner_id

    is_safe, risk_level, issues = scan_script_security(file_path, file_type)
    script_key = f"{script_owner_id}_{file_name}"
    script_security_reports[script_key] = (risk_level, issues)

    if not is_safe and requesting_user_id not in admin_ids and script_owner_id not in admin_ids:
        issues_text = "\n".join(f"• {i}" for i in issues)
        safe_reply(
            message,
            f"🚨 *AST Security Scanner Blocked Execution!*\n\nFile: `{file_name}`\nStatus: {risk_level}\n\n*Detected Issues:*\n{issues_text}",
            parse_mode='Markdown'
        )
        try:
            bot.send_message(
                OWNER_ID,
                f"🚨 *Security Alert (Blocked Upload)*\n👤 User: `{script_owner_id}`\n📄 File: `{file_name}`\n{risk_level}\n\n{issues_text}",
                parse_mode='Markdown'
            )
        except Exception:
            pass
        return

    if requesting_user_id in admin_ids or script_owner_id in admin_ids:
        if file_type == 'py': threading.Thread(target=run_script, args=(file_path, script_owner_id, user_folder, file_name, message), daemon=True).start()
        elif file_type == 'js': threading.Thread(target=run_js_script, args=(file_path, script_owner_id, user_folder, file_name, message), daemon=True).start()
        return

    approval_id = str(uuid.uuid4())[:8]
    pending_approvals[approval_id] = {
        'file_type': file_type, 'file_path': file_path, 'script_owner_id': script_owner_id,
        'user_folder': user_folder, 'file_name': file_name, 'message': message
    }

    markup = types.InlineKeyboardMarkup()
    markup.add(
        colorful_btn("✅ Approve", callback_data=f"approve_{approval_id}", style='success'),
        colorful_btn("❌ Reject", callback_data=f"reject_{approval_id}", style='danger')
    )

    scan_summary = f"\n🛡️ *AST Scan:* {risk_level}"
    if issues:
        scan_summary += "\n" + "\n".join(f"  - {i}" for i in issues[:4])

    try:
        bot.send_message(OWNER_ID, f"⚠️ *Run Request*\n\n👤 User ID: `{script_owner_id}`\n📄 File: `{file_name}`{scan_summary}\n\nDo you approve execution?", reply_markup=markup, parse_mode='Markdown')
        safe_reply(message, f"⏳ Request sent to Owner for approval to run `{file_name}` (🛡️ Scan: {risk_level}). Please wait...", parse_mode='Markdown')
    except Exception:
        safe_reply(message, "❌ Failed to request approval from Owner.")

# --- Automatic Package Installation & Script Running ---
def run_pip_command(command_list):
    result = subprocess.run(command_list, capture_output=True, text=True, check=False, encoding='utf-8', errors='ignore')
    if result.returncode != 0 and 'externally-managed-environment' in (result.stderr or ''):
        logger.info("PEP 668 restricted environment detected. Retrying with --break-system-packages.")
        if '--break-system-packages' not in command_list:
            command_list.append('--break-system-packages')
        result = subprocess.run(command_list, capture_output=True, text=True, check=False, encoding='utf-8', errors='ignore')
    return result

def attempt_install_pip(module_name, message):
    package_name = TELEGRAM_MODULES.get(module_name.lower(), module_name)
    if package_name is None: return False
    try:
        safe_reply(message, f"🐍 Module `{module_name}` missing. Installing `{package_name}`...", parse_mode='Markdown')

        if module_name.lower() == 'telegram':
            run_pip_command([sys.executable, '-m', 'pip', 'uninstall', '-y', 'telegram'])
            command = [sys.executable, '-m', 'pip', 'install', '--force-reinstall', package_name]
        else:
            command = [sys.executable, '-m', 'pip', 'install', package_name]

        logger.info(f"Running install: {' '.join(command)}")
        result = run_pip_command(command)

        if result.returncode == 0:
            safe_reply(message, f"✅ Package `{package_name}` (for `{module_name}`) installed.", parse_mode='Markdown')
            return True
        else:
            error_msg = f"❌ Failed to install `{package_name}` for `{module_name}`.\nLog:\n```\n{result.stderr or result.stdout}\n```"
            safe_reply(message, error_msg, parse_mode='Markdown')
            return False
    except Exception as e:
        safe_reply(message, f"❌ Error installing `{package_name}`: {str(e)}")
        return False

def attempt_install_npm(module_name, user_folder, message):
    try:
        safe_reply(message, f"🟠 Node package `{module_name}` not found. Installing locally...", parse_mode='Markdown')
        command = [NPM_BIN, 'install', module_name]
        use_shell = (os.name == 'nt')
        result = subprocess.run(command, capture_output=True, text=True, check=False, cwd=user_folder, shell=use_shell, encoding='utf-8', errors='ignore')
        if result.returncode == 0:
            safe_reply(message, f"✅ Node package `{module_name}` installed locally.", parse_mode='Markdown')
            return True
        else:
            error_msg = f"❌ Failed to install Node package `{module_name}`.\nLog:\n```\n{result.stderr or result.stdout}\n```"
            safe_reply(message, error_msg, parse_mode='Markdown')
            return False
    except FileNotFoundError:
         safe_reply(message, "❌ Error: 'npm' not found. Ensure Node.js/npm are installed and in PATH.")
         return False
    except Exception as e:
        safe_reply(message, f"❌ Error installing Node package `{module_name}`: {str(e)}")
        return False

def apply_os_resource_limits(pid):
    """Applies lower CPU priority to child processes so user scripts cannot freeze the host."""
    try:
        p = psutil.Process(pid)
        if os.name == 'nt':
            p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
        else:
            p.nice(10)
    except Exception:
        pass

def run_script(script_path, script_owner_id, user_folder, file_name, message_obj_for_reply, attempt=1, attempted_modules=None):
    if attempted_modules is None: attempted_modules = set()
    max_attempts = 15
    if attempt > max_attempts:
        safe_reply(message_obj_for_reply, f"❌ Failed to run '{file_name}' after {max_attempts} auto-install attempts. Check script logs.")
        return

    script_key = f"{script_owner_id}_{file_name}"
    try:
        if not os.path.exists(script_path):
             safe_reply(message_obj_for_reply, f"❌ Error: Script '{file_name}' not found at '{script_path}'!")
             if script_owner_id in user_files:
                 user_files[script_owner_id] = [f for f in user_files.get(script_owner_id, []) if f[0] != file_name]
             remove_user_file_db(script_owner_id, file_name)
             return

        log_file_path = os.path.join(user_folder, f"{os.path.splitext(file_name)[0]}.log")
        try:
            log_file = open(log_file_path, 'a+b')
        except Exception as e:
            safe_reply(message_obj_for_reply, f"❌ Failed to open log file '{log_file_path}': {e}")
            return

        startupinfo = None
        creationflags = 0
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            creationflags = subprocess.CREATE_NEW_PROCESS_GROUP

        max_ram_mb, max_cpu_pct, _ = get_user_resource_limits(script_owner_id)
        docker_ram = 2048 if max_ram_mb == float('inf') else int(max_ram_mb)
        docker_cpus = round(max_cpu_pct / 100.0, 2)

        container_name = None
        if USE_DOCKER_SANDBOX and DOCKER_BIN:
            container_name = f"sidhost_py_{script_owner_id}_{uuid.uuid4().hex[:6]}"
            cmd = [
                DOCKER_BIN, 'run', '--rm', '-i',
                '--name', container_name,
                f'--memory={docker_ram}m',
                f'--cpus={docker_cpus}',
                '-v', f"{os.path.abspath(user_folder)}:/app",
                '-w', '/app',
                'python:3.11-slim',
                'python', file_name
            ]
        else:
            cmd = [sys.executable, script_path]

        process = subprocess.Popen(
            cmd,
            cwd=user_folder,
            stdout=log_file,
            stderr=log_file,
            stdin=subprocess.PIPE,
            startupinfo=startupinfo,
            creationflags=creationflags,
            text=True,
            encoding='utf-8',
            errors='ignore'
        )
        apply_os_resource_limits(process.pid)

        time.sleep(1.8)
        exit_code = process.poll()

        if exit_code is not None:
            try: log_file.flush()
            except Exception: pass

            stderr_content = ""
            if os.path.exists(log_file_path):
                try:
                    with open(log_file_path, 'rb') as lf:
                        lf.seek(max(0, os.path.getsize(log_file_path) - 3000))
                        stderr_content = lf.read().decode('utf-8', errors='ignore')
                except Exception: pass

            match_py = re.search(r"(?:ModuleNotFoundError|ImportError): No module named '(.+?)'", stderr_content)
            if not match_py:
                match_py = re.search(r"ImportError: cannot import name '.*?' from '([^']+)'", stderr_content)

            if match_py:
                module_name = match_py.group(1).strip().strip("'\"")
                if module_name in attempted_modules:
                    safe_reply(message_obj_for_reply, f"❌ **Install Loop Prevented!** Package `{module_name}` collision or script error.", parse_mode='Markdown')
                    return
                attempted_modules.add(module_name)

                if attempt_install_pip(module_name, message_obj_for_reply):
                    safe_reply(message_obj_for_reply, f"🔄 Retrying '{file_name}'...")
                    time.sleep(1)
                    threading.Thread(target=run_script, args=(script_path, script_owner_id, user_folder, file_name, message_obj_for_reply, attempt + 1, attempted_modules), daemon=True).start()
                    return
                else:
                    safe_reply(message_obj_for_reply, f"❌ Install failed. Cannot run '{file_name}'.")
                    return
            else:
                err_summary = stderr_content[-500:] if stderr_content else "No error log available."
                safe_reply(message_obj_for_reply, f"❌ Script '{file_name}' stopped immediately (Exit code {exit_code}):\n```\n{err_summary}\n```", parse_mode='Markdown')
                return

        bot_scripts[script_key] = {
            'process': process, 'log_file': log_file, 'file_name': file_name,
            'chat_id': getattr(getattr(message_obj_for_reply, 'chat', None), 'id', script_owner_id),
            'script_owner_id': script_owner_id, 'start_time': datetime.now(),
            'user_folder': user_folder, 'type': 'py', 'script_key': script_key,
            'container_name': container_name, 'cpu_strikes': 0, 'peak_mem_mb': 0.0,
            'manual_stop': False, 'killed_by_watchdog': False
        }
        mode_str = "🐳 Docker Sandbox" if container_name else "⚡ Local Subprocess"
        ar_str = "🔁 Auto-Restart: ON" if script_key in auto_restart_scripts else "🔁 Auto-Restart: OFF"
        logger.info(f"Started Python process {process.pid} for {script_key} ({mode_str})")
        safe_reply(message_obj_for_reply, f"✅ Python script '{file_name}' started! (PID: {process.pid} | {mode_str} | {ar_str})")
    except Exception as e:
        safe_reply(message_obj_for_reply, f"❌ Unexpected error running Python script '{file_name}': {str(e)}")
        if script_key in bot_scripts:
            kill_process_tree(bot_scripts[script_key])
            bot_scripts.pop(script_key, None)

def run_js_script(script_path, script_owner_id, user_folder, file_name, message_obj_for_reply, attempt=1, attempted_modules=None):
    if attempted_modules is None: attempted_modules = set()
    max_attempts = 15
    if attempt > max_attempts:
        safe_reply(message_obj_for_reply, f"❌ Failed to run '{file_name}' after {max_attempts} auto-install attempts. Check script logs.")
        return

    script_key = f"{script_owner_id}_{file_name}"
    try:
        if not os.path.exists(script_path):
             safe_reply(message_obj_for_reply, f"❌ Error: Script '{file_name}' not found at '{script_path}'!")
             if script_owner_id in user_files:
                 user_files[script_owner_id] = [f for f in user_files.get(script_owner_id, []) if f[0] != file_name]
             remove_user_file_db(script_owner_id, file_name)
             return

        log_file_path = os.path.join(user_folder, f"{os.path.splitext(file_name)[0]}.log")
        try:
            log_file = open(log_file_path, 'a+b')
        except Exception as e:
            safe_reply(message_obj_for_reply, f"❌ Failed to open log file '{log_file_path}': {e}")
            return

        startupinfo = None
        creationflags = 0
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            creationflags = subprocess.CREATE_NEW_PROCESS_GROUP

        max_ram_mb, max_cpu_pct, _ = get_user_resource_limits(script_owner_id)
        docker_ram = 2048 if max_ram_mb == float('inf') else int(max_ram_mb)
        docker_cpus = round(max_cpu_pct / 100.0, 2)

        container_name = None
        if USE_DOCKER_SANDBOX and DOCKER_BIN:
            container_name = f"sidhost_js_{script_owner_id}_{uuid.uuid4().hex[:6]}"
            cmd = [
                DOCKER_BIN, 'run', '--rm', '-i',
                '--name', container_name,
                f'--memory={docker_ram}m',
                f'--cpus={docker_cpus}',
                '-v', f"{os.path.abspath(user_folder)}:/app",
                '-w', '/app',
                'node:20-alpine',
                'node', file_name
            ]
        else:
            cmd = [NODE_BIN, script_path]

        process = subprocess.Popen(
            cmd,
            cwd=user_folder,
            stdout=log_file,
            stderr=log_file,
            stdin=subprocess.PIPE,
            startupinfo=startupinfo,
            creationflags=creationflags,
            text=True,
            encoding='utf-8',
            errors='ignore'
        )
        apply_os_resource_limits(process.pid)

        time.sleep(1.8)
        exit_code = process.poll()

        if exit_code is not None:
            try: log_file.flush()
            except Exception: pass

            stderr_content = ""
            if os.path.exists(log_file_path):
                try:
                    with open(log_file_path, 'rb') as lf:
                        lf.seek(max(0, os.path.getsize(log_file_path) - 3000))
                        stderr_content = lf.read().decode('utf-8', errors='ignore')
                except Exception: pass

            match_js = re.search(r"Cannot find module '(.+?)'", stderr_content)
            if match_js:
                module_name = match_js.group(1).strip().strip("'\"")
                if not module_name.startswith('.') and not module_name.startswith('/'):
                    if module_name in attempted_modules:
                        safe_reply(message_obj_for_reply, f"❌ **Install Loop Prevented!** Package `{module_name}` collision detected.", parse_mode='Markdown')
                        return
                    attempted_modules.add(module_name)
                    if attempt_install_npm(module_name, user_folder, message_obj_for_reply):
                        safe_reply(message_obj_for_reply, f"🔄 NPM Install successful. Retrying '{file_name}'...")
                        time.sleep(1)
                        threading.Thread(target=run_js_script, args=(script_path, script_owner_id, user_folder, file_name, message_obj_for_reply, attempt + 1, attempted_modules), daemon=True).start()
                        return
                    else:
                        safe_reply(message_obj_for_reply, f"❌ NPM Install failed. Cannot run '{file_name}'.")
                        return

            err_summary = stderr_content[-500:] if stderr_content else "No error log available."
            safe_reply(message_obj_for_reply, f"❌ JS script '{file_name}' stopped (Exit code {exit_code}):\n```\n{err_summary}\n```", parse_mode='Markdown')
            return

        bot_scripts[script_key] = {
            'process': process, 'log_file': log_file, 'file_name': file_name,
            'chat_id': getattr(getattr(message_obj_for_reply, 'chat', None), 'id', script_owner_id),
            'script_owner_id': script_owner_id, 'start_time': datetime.now(),
            'user_folder': user_folder, 'type': 'js', 'script_key': script_key,
            'container_name': container_name, 'cpu_strikes': 0, 'peak_mem_mb': 0.0,
            'manual_stop': False, 'killed_by_watchdog': False
        }
        mode_str = "🐳 Docker Sandbox" if container_name else "⚡ Local Subprocess"
        ar_str = "🔁 Auto-Restart: ON" if script_key in auto_restart_scripts else "🔁 Auto-Restart: OFF"
        logger.info(f"Started JS process {process.pid} for {script_key} ({mode_str})")
        safe_reply(message_obj_for_reply, f"✅ JS script '{file_name}' started! (PID: {process.pid} | {mode_str} | {ar_str})")
    except Exception as e:
        safe_reply(message_obj_for_reply, f"❌ Unexpected error running JS script '{file_name}': {str(e)}")
        if script_key in bot_scripts:
            kill_process_tree(bot_scripts[script_key])
            bot_scripts.pop(script_key, None)

# --- Database Operations ---
def save_user_file(user_id, file_name, file_type='py'):
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, timeout=30, check_same_thread=False)
        c = conn.cursor()
        try:
            c.execute('INSERT OR REPLACE INTO user_files (user_id, file_name, file_type) VALUES (?, ?, ?)', (user_id, file_name, file_type))
            conn.commit()
            if user_id not in user_files: user_files[user_id] = []
            user_files[user_id] = [(fn, ft) for fn, ft in user_files[user_id] if fn != file_name]
            user_files[user_id].append((file_name, file_type))
        except Exception: pass
        finally: conn.close()

def remove_user_file_db(user_id, file_name):
    auto_restart_scripts.discard(f"{user_id}_{file_name}")
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, timeout=30, check_same_thread=False)
        c = conn.cursor()
        try:
            c.execute('DELETE FROM user_files WHERE user_id = ? AND file_name = ?', (user_id, file_name))
            c.execute('DELETE FROM auto_restart_prefs WHERE user_id = ? AND file_name = ?', (user_id, file_name))
            conn.commit()
            if user_id in user_files:
                user_files[user_id] = [f for f in user_files[user_id] if f[0] != file_name]
                if not user_files[user_id]: del user_files[user_id]
        except Exception: pass
        finally: conn.close()

def add_active_user(user_id):
    active_users.add(user_id)
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, timeout=30, check_same_thread=False)
        c = conn.cursor()
        try:
            c.execute('INSERT OR IGNORE INTO active_users (user_id) VALUES (?)', (user_id,))
            conn.commit()
        except Exception: pass
        finally: conn.close()

def update_username(user_id, username):
    if username:
        uname_lower = username.lower()
        username_to_id[uname_lower] = user_id
        with DB_LOCK:
            conn = sqlite3.connect(DATABASE_PATH, timeout=30, check_same_thread=False)
            c = conn.cursor()
            try:
                c.execute('INSERT OR REPLACE INTO user_usernames (username, user_id) VALUES (?, ?)', (uname_lower, user_id))
                conn.commit()
            except Exception: pass
            finally: conn.close()

def ban_user_db(user_id):
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, timeout=30, check_same_thread=False)
        c = conn.cursor()
        try:
            c.execute('INSERT OR IGNORE INTO banned_users (user_id) VALUES (?)', (user_id,))
            conn.commit()
            banned_users.add(user_id)
        except Exception: pass
        finally: conn.close()

def unban_user_db(user_id):
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, timeout=30, check_same_thread=False)
        c = conn.cursor()
        try:
            c.execute('DELETE FROM banned_users WHERE user_id = ?', (user_id,))
            conn.commit()
            banned_users.discard(user_id)
        except Exception: pass
        finally: conn.close()

def save_subscription(user_id, expiry):
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, timeout=30, check_same_thread=False)
        c = conn.cursor()
        try:
            c.execute('INSERT OR REPLACE INTO subscriptions (user_id, expiry) VALUES (?, ?)', (user_id, expiry.isoformat()))
            conn.commit()
            user_subscriptions[user_id] = {'expiry': expiry}
        except Exception: pass
        finally: conn.close()

def remove_subscription_db(user_id):
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, timeout=30, check_same_thread=False)
        c = conn.cursor()
        try:
            c.execute('DELETE FROM subscriptions WHERE user_id = ?', (user_id,))
            conn.commit()
            user_subscriptions.pop(user_id, None)
        except Exception: pass
        finally: conn.close()

def add_admin_db(admin_id):
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, timeout=30, check_same_thread=False)
        c = conn.cursor()
        try:
            c.execute('INSERT OR IGNORE INTO admins (user_id) VALUES (?)', (admin_id,))
            conn.commit()
            admin_ids.add(admin_id)
        except Exception: pass
        finally: conn.close()

def remove_admin_db(admin_id):
    if admin_id == OWNER_ID: return False
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, timeout=30, check_same_thread=False)
        c = conn.cursor()
        removed = False
        try:
            c.execute('SELECT 1 FROM admins WHERE user_id = ?', (admin_id,))
            if c.fetchone():
                c.execute('DELETE FROM admins WHERE user_id = ?', (admin_id,))
                conn.commit()
                removed = c.rowcount > 0
                if removed: admin_ids.discard(admin_id)
            else: admin_ids.discard(admin_id)
            return removed
        except Exception: return False
        finally: conn.close()

# --- Menu Creation (Colorful Inline Buttons + Dedicated Owner Panel) ---
def create_main_menu_inline(user_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    buttons = [
        colorful_btn('📢 Updates Channel', url=f'https://t.me/{UPDATE_CHANNEL.replace("@", "")}', style='primary'),
        colorful_btn('📤 Upload File', callback_data='upload', style='success'),
        colorful_btn('📂 Check Files', callback_data='check_files', style='primary'),
        colorful_btn('⚡ Bot Speed', callback_data='speed', style='primary'),
        colorful_btn('📤 Send Command', callback_data='send_command', style='primary'),
        colorful_btn('📞 Contact Owner', url=f'https://t.me/{YOUR_USERNAME.replace("@", "")}', style='success')
    ]

    # [TERMINAL] Add the terminal button in both branches
    term_btn = colorful_btn('🖥️ Terminal', callback_data='term_open', style='success')

    if user_id in admin_ids:
        admin_buttons = [
            colorful_btn('💳 Subscriptions', callback_data='subscription', style='primary'),
            colorful_btn('📊 Statistics', callback_data='stats', style='primary'),
            colorful_btn('🔒 Lock Bot' if not bot_locked else '🔓 Unlock Bot', callback_data='lock_bot' if not bot_locked else 'unlock_bot', style='danger' if not bot_locked else 'success'),
            colorful_btn('📢 Broadcast', callback_data='broadcast', style='primary'),
            colorful_btn('🛡️ Admin Panel', callback_data='admin_panel', style='primary'),
            colorful_btn('🟢 Run All User Scripts', callback_data='run_all_scripts', style='success')
        ]
        markup.add(buttons[0])
        markup.add(buttons[1], buttons[2])
        markup.add(term_btn)                                    # [TERMINAL]
        markup.add(buttons[3], admin_buttons[0])
        markup.add(admin_buttons[1], admin_buttons[3])
        markup.add(admin_buttons[2], admin_buttons[5])
        markup.add(buttons[4])
        if user_id == OWNER_ID:
            markup.row(
                admin_buttons[4],
                colorful_btn('👑 Owner Panel', callback_data='owner_panel', style='danger')
            )
        else:
            markup.add(admin_buttons[4])
        markup.add(buttons[5])
    else:
        markup.add(buttons[0])
        markup.add(buttons[1], buttons[2])
        markup.add(term_btn)                                    # [TERMINAL]
        markup.add(buttons[3])
        markup.add(buttons[4])
        markup.add(colorful_btn('📊 Statistics', callback_data='stats', style='primary'))
        markup.add(buttons[5])
    return markup

def create_reply_keyboard_main_menu(user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    layout_to_use = ADMIN_COMMAND_BUTTONS_LAYOUT_USER_SPEC if user_id in admin_ids else COMMAND_BUTTONS_LAYOUT_USER_SPEC
    for row_buttons_text in layout_to_use:
        markup.add(*[types.KeyboardButton(text) for text in row_buttons_text])
    return markup

def create_control_buttons(script_owner_id, file_name, is_running=True):
    markup = types.InlineKeyboardMarkup(row_width=2)
    script_key = f"{script_owner_id}_{file_name}"
    ar_on = script_key in auto_restart_scripts
    ar_label = f"🔁 Auto-Restart: {'ON 🟢' if ar_on else 'OFF 🔴'}"
    ar_style = 'success' if ar_on else 'primary'

    if is_running:
        markup.row(
            colorful_btn("🔴 Stop", callback_data=f'stop_{script_owner_id}_{file_name}', style='danger'),
            colorful_btn("🔄 Restart", callback_data=f'restart_{script_owner_id}_{file_name}', style='primary')
        )
        markup.row(
            colorful_btn("📊 Resource Stats", callback_data=f'stats_proc_{script_owner_id}_{file_name}', style='success'),
            colorful_btn("📜 Logs", callback_data=f'logs_{script_owner_id}_{file_name}', style='primary')
        )
        markup.row(
            colorful_btn(ar_label, callback_data=f'autorestart_{script_owner_id}_{file_name}', style=ar_style),
            colorful_btn("🛡️ AST Scan", callback_data=f'scan_{script_owner_id}_{file_name}', style='primary')
        )
        markup.row(
            colorful_btn("🗑️ Delete", callback_data=f'delete_{script_owner_id}_{file_name}', style='danger')
        )
    else:
        markup.row(
            colorful_btn("🟢 Start", callback_data=f'start_{script_owner_id}_{file_name}', style='success'),
            colorful_btn("🗑️ Delete", callback_data=f'delete_{script_owner_id}_{file_name}', style='danger')
        )
        markup.row(
            colorful_btn(ar_label, callback_data=f'autorestart_{script_owner_id}_{file_name}', style=ar_style),
            colorful_btn("🛡️ AST Scan", callback_data=f'scan_{script_owner_id}_{file_name}', style='primary')
        )
        markup.row(
            colorful_btn("📜 View Logs", callback_data=f'logs_{script_owner_id}_{file_name}', style='primary')
        )
    markup.add(colorful_btn("🔙 Back to Files", callback_data='check_files', style='primary'))
    return markup

def create_admin_panel(user_id=None):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.row(
        colorful_btn('➕ Add Admin', callback_data='add_admin', style='success'),
        colorful_btn('➖ Remove Admin', callback_data='remove_admin', style='danger')
    )
    markup.row(
        colorful_btn('🚫 Ban User', callback_data='ban_user', style='danger'),
        colorful_btn('✅ Unban User', callback_data='unban_user', style='success')
    )
    markup.row(
        colorful_btn('📋 List Admins', callback_data='list_admins', style='primary'),
        colorful_btn('🗂️ Manage All Files', callback_data='manage_all_files', style='primary')
    )
    markup.row(
        colorful_btn('👥 Users List', callback_data='users_list', style='primary'),
        colorful_btn('👑 Owner Panel', callback_data='owner_panel', style='danger')
    )
    markup.row(
        colorful_btn('🔙 Back to Main', callback_data='back_to_main', style='primary')
    )
    return markup

def create_owner_panel():
    """Dedicated Owner Panel exclusively for OWNER_ID (Now with Backup DB & Files)."""
    markup = types.InlineKeyboardMarkup(row_width=2)
    docker_label = f"🐳 Docker Sandbox: {'ON' if USE_DOCKER_SANDBOX else 'OFF'}"
    markup.row(
        colorful_btn('🛡️ AST Blocked Modules', callback_data='owner_ast_menu', style='primary'),
        colorful_btn('📊 Tier RAM/CPU Caps', callback_data='owner_tier_menu', style='success')
    )
    markup.row(
        colorful_btn('💾 Backup DB & All Files (.zip)', callback_data='owner_backup_all', style='success')
    )
    markup.row(
        colorful_btn(docker_label, callback_data='toggle_docker', style='success' if USE_DOCKER_SANDBOX else 'primary'),
        colorful_btn('🔁 Enable Auto-Restart All', callback_data='owner_autorestart_all', style='success')
    )
    markup.row(
        colorful_btn('🛑 Kill All Running Bots', callback_data='owner_kill_all', style='danger'),
        colorful_btn('♻️ Factory Reset', callback_data='factory_reset', style='danger')
    )
    markup.row(
        colorful_btn('🛡️ Admin Panel', callback_data='admin_panel', style='primary'),
        colorful_btn('🔙 Back to Main', callback_data='back_to_main', style='primary')
    )
    return markup

def create_ast_customizer_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.row(
        colorful_btn('➕ Block Module', callback_data='ast_add_mod', style='danger'),
        colorful_btn('➖ Unblock Module', callback_data='ast_remove_mod', style='success')
    )
    markup.row(
        colorful_btn('🔄 Reset Defaults', callback_data='ast_reset_mods', style='primary'),
        colorful_btn('🔙 Back to Owner Panel', callback_data='owner_panel', style='primary')
    )
    return markup

def create_tier_limits_menu():
    markup = types.InlineKeyboardMarkup(row_width=1)
    f_cfg = TIER_RESOURCE_LIMITS['free']
    p_cfg = TIER_RESOURCE_LIMITS['premium']
    a_cfg = TIER_RESOURCE_LIMITS['admin']
    markup.add(
        colorful_btn(f"🆓 Edit Free Tier ({f_cfg['ram_mb']}MB | {f_cfg['cpu_pct']}% CPU)", callback_data='edit_tier_free', style='primary'),
        colorful_btn(f"⭐ Edit Premium Tier ({p_cfg['ram_mb']}MB | {p_cfg['cpu_pct']}% CPU)", callback_data='edit_tier_premium', style='success'),
        colorful_btn(f"🛡️ Edit Admin Tier ({a_cfg['ram_mb']}MB | {a_cfg['cpu_pct']}% CPU)", callback_data='edit_tier_admin', style='danger'),
        colorful_btn("🔙 Back to Owner Panel", callback_data='owner_panel', style='primary')
    )
    return markup

def create_subscription_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.row(
        colorful_btn('➕ Add Subscription', callback_data='add_subscription', style='success'),
        colorful_btn('➖ Remove Subscription', callback_data='remove_subscription', style='danger')
    )
    markup.row(colorful_btn('🔍 Check Subscription', callback_data='check_subscription', style='primary'))
    markup.row(colorful_btn('🔙 Back to Main', callback_data='back_to_main', style='primary'))
    return markup

def create_send_command_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.row(
        colorful_btn('📝 Send to Process', callback_data='send_to_process', style='success'),
        colorful_btn('🔍 View All Logs', callback_data='view_all_logs', style='primary')
    )
    markup.row(colorful_btn('🔙 Back to Main', callback_data='back_to_main', style='primary'))
    return markup

# --- File Handling ---
def handle_zip_file(downloaded_file_content, file_name_zip, message):
    user_id = message.from_user.id
    user_folder = get_user_folder(user_id)
    temp_dir = None

    try:
        temp_dir = tempfile.mkdtemp(prefix=f"user_{user_id}_zip_")
        zip_path = os.path.join(temp_dir, file_name_zip)
        with open(zip_path, 'wb') as new_file:
            new_file.write(downloaded_file_content)

        safe_extract_zip(zip_path, temp_dir)

        target_dir = temp_dir
        root_files = os.listdir(target_dir)

        if not any(f.endswith(('.py', '.js')) for f in root_files):
            for root, dirs, files in os.walk(temp_dir):
                dirs[:] = [d for d in dirs if not d.startswith('.') and not d.startswith('__')]
                if any(f.endswith(('.py', '.js')) for f in files):
                    target_dir = root
                    break

        if target_dir != temp_dir:
            for item in os.listdir(target_dir):
                s = os.path.join(target_dir, item)
                d = os.path.join(temp_dir, item)
                if os.path.exists(d):
                    if os.path.isdir(d): safe_rmtree(d)
                    else: safe_remove(d)
                shutil.move(s, d)
            extracted_items = os.listdir(temp_dir)
        else:
            extracted_items = root_files

        py_files = [f for f in extracted_items if f.endswith('.py')]
        js_files = [f for f in extracted_items if f.endswith('.js')]
        req_file = 'requirements.txt' if 'requirements.txt' in extracted_items else None
        pkg_json = 'package.json' if 'package.json' in extracted_items else None

        if req_file:
            req_path = os.path.join(temp_dir, req_file)
            safe_reply(message, f"🔄 Installing Python deps from `{req_file}`...")
            try:
                result = run_pip_command([sys.executable, '-m', 'pip', 'install', '-r', req_path])
                if result.returncode == 0:
                    safe_reply(message, f"✅ Python deps from `{req_file}` installed.")
                else:
                    error_msg = f"❌ Failed to install Python deps from `{req_file}`.\nLog:\n```\n{result.stderr or result.stdout}\n```"
                    safe_reply(message, error_msg, parse_mode='Markdown')
                    return
            except Exception as e:
                 safe_reply(message, f"❌ Unexpected error installing Python deps: {e}")
                 return

        if pkg_json:
            safe_reply(message, f"🔄 Installing Node deps from `{pkg_json}`...")
            try:
                use_shell = (os.name == 'nt')
                command = [NPM_BIN, 'install']
                result = subprocess.run(command, capture_output=True, text=True, check=True, cwd=temp_dir, shell=use_shell, encoding='utf-8', errors='ignore')
                safe_reply(message, f"✅ Node deps from `{pkg_json}` installed.")
            except FileNotFoundError:
                safe_reply(message, "❌ 'npm' not found. Cannot install Node deps."); return
            except subprocess.CalledProcessError as e:
                log_content = getattr(e, 'stderr', None) or getattr(e, 'stdout', None) or "No log output available."
                error_msg = f"❌ Failed to install Node deps from `{pkg_json}`.\nLog:\n```\n{log_content}\n```"
                safe_reply(message, error_msg, parse_mode='Markdown'); return
            except Exception as e:
                 safe_reply(message, f"❌ Unexpected error installing Node deps: {e}")
                 return

        main_script_name = None; file_type = None
        preferred_py = ['main.py', 'bot.py', 'app.py']; preferred_js = ['index.js', 'main.js', 'bot.js', 'app.js']
        for p in preferred_py:
            if p in py_files: main_script_name = p; file_type = 'py'; break
        if not main_script_name:
             for p in preferred_js:
                 if p in js_files: main_script_name = p; file_type = 'js'; break
        if not main_script_name:
            if py_files: main_script_name = py_files[0]; file_type = 'py'
            elif js_files: main_script_name = js_files[0]; file_type = 'js'
        if not main_script_name:
            safe_reply(message, "❌ No `.py` or `.js` script found in archive!"); return

        for item_name in os.listdir(temp_dir):
            if item_name == file_name_zip: continue
            src_path = os.path.join(temp_dir, item_name)
            dest_path = os.path.join(user_folder, item_name)
            if os.path.isdir(dest_path): safe_rmtree(dest_path)
            elif os.path.exists(dest_path): safe_remove(dest_path)
            shutil.move(src_path, dest_path)

        save_user_file(user_id, main_script_name, file_type)
        safe_reply(message, f"✅ Files extracted safely. Running AST scan & requesting approval for `{main_script_name}`...", parse_mode='Markdown')

        main_script_path = os.path.join(user_folder, main_script_name)
        request_run_script(file_type, main_script_path, user_id, user_folder, main_script_name, message)
    except ValueError as ve:
        safe_reply(message, f"🚨 Security Error extracting ZIP: {ve}")
    except zipfile.BadZipFile as e:
        safe_reply(message, f"❌ Error: Invalid/corrupted ZIP. {e}")
    except Exception as e:
        safe_reply(message, f"❌ Error processing zip: {str(e)}")
    finally:
        if temp_dir and os.path.exists(temp_dir):
            safe_rmtree(temp_dir)

def handle_js_file(file_path, script_owner_id, user_folder, file_name, message):
    try:
        save_user_file(script_owner_id, file_name, 'js')
        request_run_script('js', file_path, script_owner_id, user_folder, file_name, message)
    except Exception as e: safe_reply(message, f"❌ Error processing JS file: {str(e)}")

def handle_py_file(file_path, script_owner_id, user_folder, file_name, message):
    try:
        save_user_file(script_owner_id, file_name, 'py')
        request_run_script('py', file_path, script_owner_id, user_folder, file_name, message)
    except Exception as e: safe_reply(message, f"❌ Error processing Python file: {str(e)}")

# --- Send Command and Enhanced Logs Functions ---
def _logic_send_command(message):
    user_id = message.from_user.id
    if bot_locked and user_id not in admin_ids:
        safe_reply(message, "⚠️ Bot locked by admin.")
        return
    safe_reply(message, "📤 Send Command Options:", reply_markup=create_send_command_menu())

def send_to_process_init(message, user_id=None):
    if user_id is None:
        user_id = message.from_user.id
    user_running_scripts = []
    for script_key, script_info in list(bot_scripts.items()):
        script_owner_id = script_info['script_owner_id']
        if (user_id == script_owner_id or user_id in admin_ids) and is_bot_running(script_owner_id, script_info['file_name']):
            user_running_scripts.append((script_key, script_info))

    if not user_running_scripts:
        safe_reply(message, "❌ No running scripts found.")
        return

    markup = types.InlineKeyboardMarkup(row_width=1)
    for script_key, script_info in user_running_scripts:
        btn_text = f"🟢 {script_info['file_name']} (User: {script_info['script_owner_id']})"
        markup.add(colorful_btn(btn_text, callback_data=f'sendcmd_select_{script_key}', style='success'))

    markup.add(colorful_btn("🔙 Back", callback_data='send_command', style='primary'))
    safe_reply(message, "📝 Select a running script to send command to:", reply_markup=markup)

def process_send_command(message, script_key):
    if not message.text:
        safe_reply(message, "❌ Please send a text command.")
        return
    if script_key not in bot_scripts:
        safe_reply(message, "❌ Script is no longer running.")
        return

    script_info = bot_scripts[script_key]
    command_text = message.text.strip()

    try:
        process = script_info['process']
        if process and process.poll() is None:
            process.stdin.write(command_text + '\n')
            process.stdin.flush()
            safe_reply(message, f"✅ Command sent to `{script_info['file_name']}`:\n`{command_text}`", parse_mode='Markdown')
            time.sleep(0.5)
            if process.poll() is not None:
                safe_reply(message, f"⚠️ Script `{script_info['file_name']}` stopped after receiving command.")
        else:
            safe_reply(message, f"❌ Script `{script_info['file_name']}` is not running.")
    except Exception as e:
        safe_reply(message, f"❌ Error sending command: {str(e)}")

def view_all_logs(message):
    user_id = message.from_user.id
    user_logs = []
    user_folder = get_user_folder(user_id)
    if os.path.exists(user_folder):
        for file in os.listdir(user_folder):
            if file.endswith('.log'):
                log_path = os.path.join(user_folder, file)
                file_size = os.path.getsize(log_path)
                user_logs.append((file, file_size, log_path))

    if not user_logs:
        safe_reply(message, "📜 No log files found.")
        return

    markup = types.InlineKeyboardMarkup(row_width=1)
    for log_file, size, log_path in sorted(user_logs):
        btn_text = f"📜 {log_file} ({size / 1024:.1f} KB)"
        markup.add(colorful_btn(btn_text, callback_data=f'viewlog_{user_id}_{log_file}', style='primary'))

    markup.add(colorful_btn("🔙 Back", callback_data='send_command', style='primary'))
    safe_reply(message, "📜 Available Log Files:", reply_markup=markup)

def send_log_file(message, log_path, log_filename):
    try:
        if not os.path.exists(log_path):
            safe_reply(message, "❌ Log file not found.")
            return
        file_size = os.path.getsize(log_path)
        if file_size == 0:
            safe_reply(message, f"📜 Log file `{log_filename}` is currently empty.", parse_mode='Markdown')
            return
        if file_size > 50 * 1024 * 1024:
            safe_reply(message, f"❌ Log file too large ({file_size/1024/1024:.1f} MB). Maximum 50MB.")
            return
        with open(log_path, 'rb') as log_file:
            bot.send_document(message.chat.id, log_file, caption=f"📜 {log_filename}")
    except Exception as e:
        safe_reply(message, f"❌ Error sending log file: {str(e)}")

# --- Logic Functions ---
def _logic_send_welcome(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    user_name = message.from_user.first_name
    user_username = message.from_user.username

    update_username(user_id, user_username)

    if bot_locked and user_id not in admin_ids:
        bot.send_message(chat_id, "⚠️ Bot locked by admin. Try later.")
        return

    user_bio = "Could not fetch bio"; photo_file_id = None
    try: user_bio = bot.get_chat(user_id).bio or "No bio"
    except Exception: pass
    try:
        user_profile_photos = bot.get_user_profile_photos(user_id, limit=1)
        if user_profile_photos.photos: photo_file_id = user_profile_photos.photos[0][-1].file_id
    except Exception: pass

    if user_id not in active_users:
        add_active_user(user_id)
        try:
            owner_notification = (f"🎉 New user!\n👤 Name: {user_name}\n✳️ User: @{user_username or 'N/A'}\n🆔 ID: `{user_id}`\n📝 Bio: {user_bio}")
            bot.send_message(OWNER_ID, owner_notification, parse_mode='Markdown')
            if photo_file_id: bot.send_photo(OWNER_ID, photo_file_id, caption=f"Pic of new user {user_id}")
        except Exception: pass

    file_limit = get_user_file_limit(user_id)
    current_files = get_user_file_count(user_id)
    limit_str = str(file_limit) if file_limit != float('inf') else "Unlimited"
    max_ram_mb, max_cpu_pct, _ = get_user_resource_limits(user_id)
    ram_str = "Unlimited" if max_ram_mb == float('inf') else f"{max_ram_mb} MB"

    expiry_info = ""
    if user_id == OWNER_ID: user_status = "👑 Owner"
    elif user_id in admin_ids: user_status = "🛡️ Admin"
    elif user_id in user_subscriptions:
        expiry_date = user_subscriptions[user_id].get('expiry')
        if expiry_date and expiry_date > datetime.now():
            user_status = "⭐ Premium"; days_left = (expiry_date - datetime.now()).days
            expiry_info = f"\n⏳ Subscription expires in: {days_left} days"
        else: user_status = "🆓 Free User (Expired Sub)"; remove_subscription_db(user_id)
    else: user_status = "🆓 Free User"

    welcome_msg_text = (f" 𝗪𝗘𝗟𝗖𝗢𝗠𝗘 𝗧𝗢 𝗥𝗘𝗕𝗘𝗟 𝗛𝗢𝗦𝗧𝗜𝗡𝗚 𝗕𝗢𝗧 🎀, {user_name}!\n\n🆔 Your User ID: `{user_id}`\n"
                        f"✳️ Username: `@{user_username or 'Not set'}`\n"
                        f"🔰 Your Status: {user_status}{expiry_info}\n"
                        f"📁 Files Uploaded: {current_files} / {limit_str}\n"
                        f"🧠 Tier Resource Cap: `{ram_str} RAM` | `{max_cpu_pct}% CPU`\n\n"
                        f"🤖 Host & run Python (`.py`) or JS (`.js`) scripts.\n"
                        f"   Upload single scripts or `.zip` archives.\n\n"
                        f"👇 Use buttons or type commands.")
    main_reply_markup = create_reply_keyboard_main_menu(user_id)
    try:
        if photo_file_id: bot.send_photo(chat_id, photo_file_id)
        bot.send_message(chat_id, welcome_msg_text, reply_markup=main_reply_markup, parse_mode='Markdown')
        bot.send_message(chat_id, "🎛️ *Quick Control Menu:*", reply_markup=create_main_menu_inline(user_id), parse_mode='Markdown')
    except Exception:
        try: bot.send_message(chat_id, welcome_msg_text, reply_markup=main_reply_markup, parse_mode='Markdown')
        except Exception: pass

def _logic_updates_channel(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(colorful_btn('📢 Updates Channel', url=f'https://t.me/{UPDATE_CHANNEL.replace("@", "")}', style='primary'))
    safe_reply(message, "Visit our Updates Channel:", reply_markup=markup)

def _logic_upload_file(message):
    user_id = message.from_user.id
    if bot_locked and user_id not in admin_ids:
        safe_reply(message, "⚠️ Bot locked by admin, cannot accept files.")
        return

    file_limit = get_user_file_limit(user_id)
    current_files = get_user_file_count(user_id)
    if current_files >= file_limit:
        limit_str = str(file_limit) if file_limit != float('inf') else "Unlimited"
        safe_reply(message, f"⚠️ File limit ({current_files}/{limit_str}) reached. Delete files first.")
        return
    safe_reply(message, "📤 Send your Python (`.py`), JS (`.js`), or ZIP (`.zip`) file.")

def _logic_check_files(message):
    user_id = message.from_user.id
    user_files_list = user_files.get(user_id, [])
    if not user_files_list:
        safe_reply(message, "📂 Your files:\n\n(No files uploaded yet)")
        return
    markup = types.InlineKeyboardMarkup(row_width=1)
    for file_name, file_type in sorted(user_files_list):
        is_running = is_bot_running(user_id, file_name)
        status_icon = "🟢 Running" if is_running else "🔴 Stopped"
        ar_icon = " 🔁" if f"{user_id}_{file_name}" in auto_restart_scripts else ""
        btn_style = 'success' if is_running else 'danger'
        btn_text = f"{file_name} ({file_type}) - {status_icon}{ar_icon}"
        markup.add(colorful_btn(btn_text, callback_data=f'file_{user_id}_{file_name}', style=btn_style))
    safe_reply(message, "📂 Your files:\nClick to manage.", reply_markup=markup, parse_mode='Markdown')

def _logic_bot_speed(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    start_time_ping = time.time()
    wait_msg = safe_reply(message, "🏃 Testing speed...")
    try:
        bot.send_chat_action(chat_id, 'typing')
        response_time = round((time.time() - start_time_ping) * 1000, 2)
        status = "🔓 Unlocked" if not bot_locked else "🔒 Locked"
        max_ram_mb, max_cpu_pct, user_level = get_user_resource_limits(user_id)
        ram_str = "Unlimited" if max_ram_mb == float('inf') else f"{max_ram_mb} MB"
        host_cpu = psutil.cpu_percent(interval=0.1)
        host_ram = psutil.virtual_memory().percent
        speed_msg = (f"⚡ Bot Speed & Status:\n\n⏱️ API Response Time: {response_time} ms\n"
                     f"🖥️ Host CPU: {host_cpu}% | RAM: {host_ram}%\n"
                     f"🚦 Bot Status: {status}\n"
                     f"👤 Your Tier: {user_level} ({ram_str} RAM / {max_cpu_pct}% CPU)")
        if wait_msg:
            bot.edit_message_text(speed_msg, chat_id, wait_msg.message_id)
        else:
            bot.send_message(chat_id, speed_msg)
    except Exception:
        if wait_msg:
            bot.edit_message_text("❌ Error during speed test.", chat_id, wait_msg.message_id)

def _logic_contact_owner(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(colorful_btn('📞 Contact Owner', url=f'https://t.me/{YOUR_USERNAME.replace("@", "")}', style='success'))
    safe_reply(message, "Click to contact Owner:", reply_markup=markup)

def _logic_subscriptions_panel(message):
    if message.from_user.id not in admin_ids:
        safe_reply(message, "⚠️ Admin permissions required.")
        return
    safe_reply(message, "💳 Subscription Management\nUse inline buttons from /start or admin command menu.", reply_markup=create_subscription_menu())

def _logic_statistics(message):
    user_id = message.from_user.id
    total_users = len(active_users)
    total_files_records = sum(len(files) for files in user_files.values())

    running_bots_count = 0
    user_running_bots = 0

    for script_key_iter, script_info_iter in list(bot_scripts.items()):
        try:
            s_owner_id = int(script_info_iter['script_owner_id'])
            if is_bot_running(s_owner_id, script_info_iter['file_name']):
                running_bots_count += 1
                if s_owner_id == user_id:
                    user_running_bots += 1
        except Exception:
            pass

    stats_msg_base = (f"📊 Bot Statistics:\n\n👥 Total Users: {total_users}\n📂 Total File Records: {total_files_records}\n🟢 Total Active Bots: {running_bots_count}\n🔁 Auto-Restart Active: {len(auto_restart_scripts)} scripts\n")
    if user_id in admin_ids:
        stats_msg_admin = (f"🔒 Bot Status: {'🔴 Locked' if bot_locked else '🟢 Unlocked'}\n🐳 Docker Sandbox: {'🟢 ON' if USE_DOCKER_SANDBOX else '🔴 OFF'}\n🤖 Your Running Bots: {user_running_bots}")
        stats_msg = stats_msg_base + stats_msg_admin
    else: stats_msg = stats_msg_base + f"🤖 Your Running Bots: {user_running_bots}"
    safe_reply(message, stats_msg)

def _logic_broadcast_init(message):
    if message.from_user.id not in admin_ids:
        safe_reply(message, "⚠️ Admin permissions required.")
        return
    msg = safe_reply(message, "📢 Send message to broadcast to all active users.\n/cancel to abort.")
    if msg:
        bot.register_next_step_handler(msg, process_broadcast_message)

def _logic_toggle_lock_bot(message):
    if message.from_user.id not in admin_ids:
        safe_reply(message, "⚠️ Admin permissions required.")
        return
    global bot_locked
    bot_locked = not bot_locked
    status = "locked" if bot_locked else "unlocked"
    safe_reply(message, f"🔒 Bot has been {status}.")

def _logic_admin_panel(message):
    if message.from_user.id not in admin_ids:
        safe_reply(message, "⚠️ Admin permissions required.")
        return
    safe_reply(message, "🛡️ Admin Panel\nManage admins, users, and files:", reply_markup=create_admin_panel(message.from_user.id))

def _logic_owner_panel(message):
    if message.from_user.id != OWNER_ID:
        safe_reply(message, "❌ Access Denied: Only the Bot Owner can open the Owner Panel.")
        return
    f_cfg = TIER_RESOURCE_LIMITS['free']
    p_cfg = TIER_RESOURCE_LIMITS['premium']
    a_cfg = TIER_RESOURCE_LIMITS['admin']
    panel_text = (
        f"👑 *Owner Control Panel*\n\n"
        f"🛡️ *AST Blocked Modules:* `{len(DANGEROUS_PY_IMPORTS)}` active\n"
        f"🆓 *Free Cap:* `{f_cfg['ram_mb']}MB` RAM | `{f_cfg['cpu_pct']}%` CPU\n"
        f"⭐ *Premium Cap:* `{p_cfg['ram_mb']}MB` RAM | `{p_cfg['cpu_pct']}%` CPU\n"
        f"🛡️ *Admin Cap:* `{a_cfg['ram_mb']}MB` RAM | `{a_cfg['cpu_pct']}%` CPU\n"
        f"🐳 *Docker Mode:* `{'ON' if USE_DOCKER_SANDBOX else 'OFF'}`"
    )
    safe_reply(message, panel_text, reply_markup=create_owner_panel(), parse_mode='Markdown')

def _logic_run_all_scripts(message_or_call):
    if isinstance(message_or_call, telebot.types.Message):
        admin_user_id = message_or_call.from_user.id
        reply_func = lambda text, **kwargs: safe_reply(message_or_call, text, **kwargs)
        admin_message_obj = message_or_call
    elif isinstance(message_or_call, telebot.types.CallbackQuery):
        admin_user_id = message_or_call.from_user.id
        admin_chat_id = message_or_call.message.chat.id
        bot.answer_callback_query(message_or_call.id)
        reply_func = lambda text, **kwargs: bot.send_message(admin_chat_id, text, **kwargs)
        admin_message_obj = PseudoMessage(message_or_call.from_user, admin_chat_id)
    else: return

    if admin_user_id not in admin_ids:
        reply_func("⚠️ Admin permissions required.")
        return

    reply_func("⏳ Starting execution requests for all saved scripts...")

    started_count = 0; attempted_users = 0; skipped_files = 0; error_files_details = []
    all_user_files_snapshot = dict(user_files)

    for target_user_id, files_for_user in all_user_files_snapshot.items():
        if not files_for_user: continue
        attempted_users += 1
        user_folder = get_user_folder(target_user_id)

        for file_name, file_type in files_for_user:
            if not is_bot_running(target_user_id, file_name):
                file_path = os.path.join(user_folder, file_name)
                if os.path.exists(file_path):
                    try:
                        request_run_script(file_type, file_path, target_user_id, user_folder, file_name, admin_message_obj, requesting_user_id=admin_user_id)
                        started_count += 1
                        time.sleep(0.5)
                    except Exception:
                        error_files_details.append(f"`{file_name}` (User {target_user_id}) - Start error")
                        skipped_files += 1
                else:
                    error_files_details.append(f"`{file_name}` (User {target_user_id}) - File not found")
                    skipped_files += 1

    summary_msg = (f"✅ All Scripts Processed:\n\n▶️ Started: {started_count} scripts.\n👥 Users: {attempted_users}.\n")
    if skipped_files > 0:
        summary_msg += f"⚠️ Skipped: {skipped_files}\n"
        if error_files_details: summary_msg += "Details:\n" + "\n".join([f"  - {err}" for err in error_files_details[:5]])
    reply_func(summary_msg, parse_mode='Markdown')

def process_broadcast_message(message):
    if message.text and message.text.lower() == '/cancel':
        safe_reply(message, "🛑 Broadcast cancelled.")
        return

    safe_reply(message, "⏳ Broadcasting message... Please wait.")
    success_count = 0
    fail_count = 0
    users_to_message = list(active_users)

    for user_id in users_to_message:
        if user_id == message.from_user.id: continue
        try:
            bot.copy_message(user_id, message.chat.id, message.message_id)
            success_count += 1
            time.sleep(0.04)
        except Exception: fail_count += 1

    safe_reply(message, f"📢 **Broadcast Complete!**\n\n✅ Sent: `{success_count}` users\n❌ Failed: `{fail_count}` users", parse_mode='Markdown')

# --- Password Authentication System ---
def is_authenticated(user_id):
    if user_id == OWNER_ID or user_id in admin_ids: return True
    return user_id in authenticated_users

def authenticate_user(user_id):
    authenticated_users.add(user_id)
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, timeout=30, check_same_thread=False)
        c = conn.cursor()
        try:
            c.execute('INSERT OR IGNORE INTO auth_users (user_id) VALUES (?)', (user_id,))
            conn.commit()
        except Exception: pass
        finally: conn.close()

@bot.message_handler(func=lambda m: not is_authenticated(m.from_user.id), content_types=['text', 'document', 'photo', 'video', 'audio', 'voice', 'sticker'])
def handle_unauthenticated(message):
    if message.content_type == 'text' and message.text.strip().lower() == "rebel baap":
        authenticate_user(message.from_user.id)
        bot.reply_to(message, "✅ **Password correct! Access granted.**", parse_mode="Markdown")
        if not check_joined(message.from_user.id, message.chat.id): return
        _logic_send_welcome(message)
    else:
        bot.reply_to(message, "🔒 **Bot is Password Protected**\n\nPlease enter the password to access:")

@bot.callback_query_handler(func=lambda call: not is_authenticated(call.from_user.id))
def auth_callback(call):
    bot.answer_callback_query(call.id, "🔒 Please enter the password in the chat to unlock the bot.", show_alert=True)
# --------------------------------------

# --- Command Handlers ---
@bot.message_handler(commands=['start', 'help'])
def command_send_welcome(message):
    if not check_joined(message.from_user.id, message.chat.id): return
    _logic_send_welcome(message)

@bot.message_handler(commands=['status'])
def command_show_status(message):
    if not check_joined(message.from_user.id, message.chat.id): return
    _logic_statistics(message)

@bot.message_handler(commands=['ownerpanel'])
def command_owner_panel(message):
    if not check_joined(message.from_user.id, message.chat.id): return
    _logic_owner_panel(message)

@bot.message_handler(commands=['backup'])
def command_owner_backup(message):
    if message.from_user.id != OWNER_ID:
        safe_reply(message, "❌ Access Denied: Only the Bot Owner can create system backups.")
        return
    threading.Thread(target=execute_owner_backup, args=(message.chat.id,), daemon=True).start()

@bot.message_handler(commands=['ban'])
def command_ban(message):
    if message.from_user.id not in admin_ids: return
    parts = message.text.split()
    if len(parts) < 2:
        safe_reply(message, "⚠️ Usage: /ban <user_id or @username>")
        return
    target = parts[1].replace('@', '').strip().lower()

    target_id = None
    if target.isdigit():
        target_id = int(target)
    elif target in username_to_id:
        target_id = username_to_id[target]

    if target_id:
        if target_id == OWNER_ID or target_id in admin_ids:
            safe_reply(message, "❌ Cannot ban an admin or owner.")
            return
        ban_user_db(target_id)
        safe_reply(message, f"✅ User `{target_id}` has been successfully banned.", parse_mode="Markdown")
    else:
        safe_reply(message, "❌ User not found in database. Try using their numerical User ID.")

@bot.message_handler(commands=['unban'])
def command_unban(message):
    if message.from_user.id not in admin_ids: return
    parts = message.text.split()
    if len(parts) < 2:
        safe_reply(message, "⚠️ Usage: /unban <user_id or @username>")
        return
    target = parts[1].replace('@', '').strip().lower()

    target_id = None
    if target.isdigit():
        target_id = int(target)
    elif target in username_to_id:
        target_id = username_to_id[target]

    if target_id:
        unban_user_db(target_id)
        safe_reply(message, f"✅ User `{target_id}` has been unbanned.", parse_mode="Markdown")
    else:
        safe_reply(message, "❌ User not found.")

BUTTON_TEXT_TO_LOGIC = {
    "📢 Updates Channel": _logic_updates_channel, "📤 Upload File": _logic_upload_file,
    "📂 Check Files": _logic_check_files, "⚡ Bot Speed": _logic_bot_speed,
    "📤 Send Command": _logic_send_command, "📞 Contact Owner": _logic_contact_owner,
    "📊 Statistics": _logic_statistics, "💳 Subscriptions": _logic_subscriptions_panel,
    "📢 Broadcast": _logic_broadcast_init, "🔒 Lock Bot": _logic_toggle_lock_bot,
    "🟢 Running All Code": _logic_run_all_scripts, "👑 Admin Panel": _logic_admin_panel,
    "👑 Owner Panel": _logic_owner_panel,
}

@bot.message_handler(func=lambda message: message.text in BUTTON_TEXT_TO_LOGIC)
def handle_button_text(message):
    if not check_joined(message.from_user.id, message.chat.id): return
    logic_func = BUTTON_TEXT_TO_LOGIC.get(message.text)
    if logic_func: logic_func(message)

@bot.message_handler(commands=['updateschannel'])
def command_updates_channel(message):
    if not check_joined(message.from_user.id, message.chat.id): return
    _logic_updates_channel(message)

@bot.message_handler(commands=['uploadfile'])
def command_upload_file(message):
    if not check_joined(message.from_user.id, message.chat.id): return
    _logic_upload_file(message)

@bot.message_handler(commands=['checkfiles'])
def command_check_files(message):
    if not check_joined(message.from_user.id, message.chat.id): return
    _logic_check_files(message)

@bot.message_handler(commands=['botspeed'])
def command_bot_speed(message):
    if not check_joined(message.from_user.id, message.chat.id): return
    _logic_bot_speed(message)

@bot.message_handler(commands=['sendcommand'])
def command_send_command(message):
    if not check_joined(message.from_user.id, message.chat.id): return
    _logic_send_command(message)

@bot.message_handler(commands=['contactowner'])
def command_contact_owner(message):
    if not check_joined(message.from_user.id, message.chat.id): return
    _logic_contact_owner(message)

@bot.message_handler(commands=['subscriptions'])
def command_subscriptions(message):
    if not check_joined(message.from_user.id, message.chat.id): return
    _logic_subscriptions_panel(message)

@bot.message_handler(commands=['statistics'])
def command_statistics(message):
    if not check_joined(message.from_user.id, message.chat.id): return
    _logic_statistics(message)

@bot.message_handler(commands=['broadcast'])
def command_broadcast(message):
    if not check_joined(message.from_user.id, message.chat.id): return
    _logic_broadcast_init(message)

@bot.message_handler(commands=['lockbot'])
def command_lock_bot(message):
    if not check_joined(message.from_user.id, message.chat.id): return
    _logic_toggle_lock_bot(message)

@bot.message_handler(commands=['adminpanel'])
def command_admin_panel(message):
    if not check_joined(message.from_user.id, message.chat.id): return
    _logic_admin_panel(message)

@bot.message_handler(commands=['runningallcode'])
def command_run_all_code(message):
    if not check_joined(message.from_user.id, message.chat.id): return
    _logic_run_all_scripts(message)

@bot.message_handler(commands=['ping'])
def ping(message):
    start_ping_time = time.time()
    msg = bot.reply_to(message, "Pong!")
    latency = round((time.time() - start_ping_time) * 1000, 2)
    bot.edit_message_text(f"Pong! Latency: {latency} ms", message.chat.id, msg.message_id)

@bot.message_handler(content_types=['document'])
def handle_file_upload_doc(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    if not check_joined(user_id, chat_id): return
    doc = message.document

    if bot_locked and user_id not in admin_ids:
        safe_reply(message, "⚠️ Bot locked, cannot accept files.")
        return

    file_limit = get_user_file_limit(user_id)
    current_files = get_user_file_count(user_id)
    if current_files >= file_limit:
        limit_str = str(file_limit) if file_limit != float('inf') else "Unlimited"
        safe_reply(message, f"⚠️ File limit ({current_files}/{limit_str}) reached. Delete files via /checkfiles.")
        return

    file_name = doc.file_name
    if not file_name:
        safe_reply(message, "⚠️ No file name. Ensure file has a name.")
        return
    if len(file_name) > 30:
        safe_reply(message, f"⚠️ The file name `{file_name}` is too long ({len(file_name)} characters).\n\nPlease rename it to be under 30 characters.", parse_mode='Markdown')
        return

    file_ext = os.path.splitext(file_name)[1].lower()
    if file_ext not in ['.py', '.js', '.zip']:
        safe_reply(message, "⚠️ Unsupported type! Only `.py`, `.js`, `.zip` allowed.")
        return
    max_file_size = 20 * 1024 * 1024
    if doc.file_size > max_file_size:
        safe_reply(message, f"⚠️ File too large (Max: {max_file_size // 1024 // 1024} MB).")
        return

    try:
        try:
            bot.forward_message(OWNER_ID, chat_id, message.message_id)
            bot.send_message(OWNER_ID, f"⬆️ File '{file_name}' from {message.from_user.first_name} (`{user_id}`)", parse_mode='Markdown')
        except Exception: pass

        download_wait_msg = safe_reply(message, f"⏳ Downloading `{file_name}`...")
        file_info_tg_doc = bot.get_file(doc.file_id)
        downloaded_file_content = bot.download_file(file_info_tg_doc.file_path)

        if download_wait_msg:
            bot.edit_message_text(f"✅ Downloaded `{file_name}`. Processing...", chat_id, download_wait_msg.message_id)
        user_folder = get_user_folder(user_id)

        if file_ext == '.zip':
            handle_zip_file(downloaded_file_content, file_name, message)
        else:
            file_path = os.path.join(user_folder, file_name)
            with open(file_path, 'wb') as f: f.write(downloaded_file_content)
            if file_ext == '.js': handle_js_file(file_path, user_id, user_folder, file_name, message)
            elif file_ext == '.py': handle_py_file(file_path, user_id, user_folder, file_name, message)
    except Exception as e:
         if "file is too big" in str(e).lower():
             safe_reply(message, f"❌ Telegram API Error: File too large to download (~20MB limit).")
         else:
             safe_reply(message, f"❌ Telegram API Error: {str(e)}. Try later.")

# --- Callback Query Handlers ---
@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    data = call.data

    if data == 'verify_join':
        if user_id in admin_ids or user_id == OWNER_ID:
            is_member = True
        else:
            try:
                member = bot.get_chat_member(UPDATE_CHANNEL, user_id)
                is_member = member.status in ['member', 'administrator', 'creator']
            except Exception: is_member = False

        if is_member:
            bot.answer_callback_query(call.id, "✅ Membership verified! Access Granted.", show_alert=False)
            try: bot.delete_message(chat_id, call.message.message_id)
            except Exception: pass
            _logic_send_welcome(PseudoMessage(call.from_user, chat_id))
        else:
            bot.answer_callback_query(call.id, f"❌ You still haven't joined {UPDATE_CHANNEL} yet!", show_alert=True)
        return

    if not check_joined(user_id, chat_id, is_callback=True, call_id=call.id): return
    if bot_locked and user_id not in admin_ids and data not in ['back_to_main', 'speed', 'stats']:
        bot.answer_callback_query(call.id, "⚠️ Bot locked by admin.", show_alert=True)
        return

    try:
        if data.startswith('approve_') or data.startswith('reject_'): handle_approval_action(call)
        elif data == 'upload': upload_callback(call)
        elif data == 'check_files': check_files_callback(call)
        elif data.startswith('file_'): file_control_callback(call)
        elif data.startswith('start_'): start_bot_callback(call)
        elif data.startswith('stop_'): stop_bot_callback(call)
        elif data.startswith('restart_'): restart_bot_callback(call)
        elif data.startswith('delete_'): delete_bot_callback(call)
        elif data.startswith('logs_'): logs_bot_callback(call)
        elif data.startswith('autorestart_'): toggle_autorestart_callback(call)
        elif data.startswith('stats_proc_'): stats_proc_callback(call)
        elif data.startswith('scan_'): scan_file_callback(call)
        elif data == 'speed': speed_callback(call)
        elif data == 'back_to_main': back_to_main_callback(call)
        elif data == 'send_command': send_command_callback(call)
        elif data == 'send_to_process': send_to_process_callback(call)
        elif data.startswith('sendcmd_select_'): sendcmd_select_callback(call)
        elif data == 'view_all_logs': view_all_logs_callback(call)
        elif data.startswith('viewlog_'): viewlog_callback(call)
        elif data == 'subscription': admin_required_callback(call, subscription_management_callback)
        elif data == 'stats': stats_callback(call)
        elif data == 'lock_bot': admin_required_callback(call, lock_bot_callback)
        elif data == 'unlock_bot': admin_required_callback(call, unlock_bot_callback)
        elif data == 'run_all_scripts': admin_required_callback(call, run_all_scripts_callback)
        elif data == 'broadcast': admin_required_callback(call, broadcast_callback)
        elif data == 'admin_panel': admin_required_callback(call, admin_panel_callback)
        elif data == 'owner_panel': owner_required_callback(call, owner_panel_callback)
        elif data == 'owner_backup_all': owner_required_callback(call, owner_backup_all_callback)
        elif data == 'owner_ast_menu': owner_required_callback(call, owner_ast_menu_callback)
        elif data == 'ast_add_mod': owner_required_callback(call, ast_add_mod_callback)
        elif data == 'ast_remove_mod': owner_required_callback(call, ast_remove_mod_callback)
        elif data == 'ast_reset_mods': owner_required_callback(call, ast_reset_mods_callback)
        elif data == 'owner_tier_menu': owner_required_callback(call, owner_tier_menu_callback)
        elif data.startswith('edit_tier_'): owner_required_callback(call, edit_tier_callback)
        elif data == 'owner_autorestart_all': owner_required_callback(call, owner_autorestart_all_callback)
        elif data == 'owner_kill_all': owner_required_callback(call, owner_kill_all_callback)
        elif data == 'toggle_docker': owner_required_callback(call, toggle_docker_callback)
        elif data == 'add_admin': admin_required_callback(call, add_admin_callback)
        elif data == 'remove_admin': admin_required_callback(call, remove_admin_callback)
        elif data == 'ban_user': admin_required_callback(call, ban_user_callback)
        elif data == 'unban_user': admin_required_callback(call, unban_user_callback)
        elif data == 'list_admins': admin_required_callback(call, list_admins_callback)
        elif data == 'add_subscription': admin_required_callback(call, add_subscription_callback)
        elif data == 'remove_subscription': admin_required_callback(call, remove_subscription_callback)
        elif data == 'check_subscription': admin_required_callback(call, check_subscription_callback)
        elif data == 'manage_all_files': admin_required_callback(call, manage_all_files_callback)
        elif data.startswith('admin_user_files_'): admin_required_callback(call, admin_user_files_callback)
        elif data == 'users_list': admin_required_callback(call, users_list_callback)
        elif data == 'factory_reset': owner_required_callback(call, factory_reset_callback)
        elif data == 'confirm_reset': owner_required_callback(call, confirm_reset_callback)
        # [TERMINAL] — terminal callbacks
        elif data == 'term_open':  term_open_callback(call)
        elif data == 'term_close': term_close_callback(call)
        elif data == 'term_help':  term_help_callback(call)
        elif data == 'term_ls':    term_ls_callback(call)
        else: bot.answer_callback_query(call.id, "Unknown action.")
    except Exception as e:
        logger.error(f"Error handling callback '{data}' for {user_id}: {e}", exc_info=True)

def admin_required_callback(call, func_to_run):
    if call.from_user.id not in admin_ids:
        bot.answer_callback_query(call.id, "⚠️ Admin permissions required.", show_alert=True)
        return
    func_to_run(call)

def owner_required_callback(call, func_to_run):
    if call.from_user.id != OWNER_ID:
        bot.answer_callback_query(call.id, "❌ Access Denied: Only the Bot Owner can use this feature.", show_alert=True)
        return
    func_to_run(call)

# --- Owner Panel Callbacks (Backup, AST Customizer, Tier Caps, Global Controls) ---
def owner_panel_callback(call):
    bot.answer_callback_query(call.id)
    f_cfg = TIER_RESOURCE_LIMITS['free']
    p_cfg = TIER_RESOURCE_LIMITS['premium']
    a_cfg = TIER_RESOURCE_LIMITS['admin']
    panel_text = (
        f"👑 *Owner Control Panel*\n\n"
        f"🛡️ *AST Blocked Modules:* `{len(DANGEROUS_PY_IMPORTS)}` active\n"
        f"🆓 *Free Cap:* `{f_cfg['ram_mb']}MB` RAM | `{f_cfg['cpu_pct']}%` CPU\n"
        f"⭐ *Premium Cap:* `{p_cfg['ram_mb']}MB` RAM | `{p_cfg['cpu_pct']}%` CPU\n"
        f"🛡️ *Admin Cap:* `{a_cfg['ram_mb']}MB` RAM | `{a_cfg['cpu_pct']}%` CPU\n"
        f"🐳 *Docker Mode:* `{'ON' if USE_DOCKER_SANDBOX else 'OFF'}`"
    )
    bot.edit_message_text(panel_text, call.message.chat.id, call.message.message_id, reply_markup=create_owner_panel(), parse_mode='Markdown')

def owner_backup_all_callback(call):
    bot.answer_callback_query(call.id, "💾 Starting full backup...")
    threading.Thread(target=execute_owner_backup, args=(call.message.chat.id,), daemon=True).start()

def owner_ast_menu_callback(call):
    bot.answer_callback_query(call.id)
    mods_formatted = ", ".join(f"`{m}`" for m in sorted(DANGEROUS_PY_IMPORTS)) if DANGEROUS_PY_IMPORTS else "*(None)*"
    text = (
        f"🛡️ *AST Blocked Modules Customizer*\n\n"
        f"Any non-admin Python script importing these modules is automatically blocked before execution:\n\n"
        f"{mods_formatted}"
    )
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=create_ast_customizer_menu(), parse_mode='Markdown')

def ast_add_mod_callback(call):
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id, "➕ Send the Python module name(s) to block in AST scanner (e.g., `socket` or `os subprocess`):", parse_mode='Markdown')
    bot.register_next_step_handler(msg, process_ast_add_mod)

def process_ast_add_mod(message):
    if not message.text: return
    mods = [m.strip().lower() for m in message.text.replace(',', ' ').split() if m.strip()]
    for m in mods:
        add_ast_module_db(m)
    safe_reply(message, f"✅ Added to AST blocked modules: {', '.join(f'`{m}`' for m in mods)}", parse_mode='Markdown')

def ast_remove_mod_callback(call):
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id, "➖ Send the Python module name(s) to unblock from AST scanner:", parse_mode='Markdown')
    bot.register_next_step_handler(msg, process_ast_remove_mod)

def process_ast_remove_mod(message):
    if not message.text: return
    mods = [m.strip().lower() for m in message.text.replace(',', ' ').split() if m.strip()]
    for m in mods:
        remove_ast_module_db(m)
    safe_reply(message, f"✅ Removed from AST blocked modules: {', '.join(f'`{m}`' for m in mods)}", parse_mode='Markdown')

def ast_reset_mods_callback(call):
    reset_ast_modules_db()
    bot.answer_callback_query(call.id, "🔄 Reset AST blocked modules to defaults!", show_alert=True)
    owner_ast_menu_callback(call)

def owner_tier_menu_callback(call):
    bot.answer_callback_query(call.id)
    text = (
        "📊 *Customize Per-Tier Resource Limits*\n\n"
        "Select a user tier below to customize its maximum RAM (MB) and CPU (%) caps enforced by the watchdog:"
    )
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=create_tier_limits_menu(), parse_mode='Markdown')

def edit_tier_callback(call):
    tier = call.data.replace('edit_tier_', '')
    bot.answer_callback_query(call.id)
    cur = TIER_RESOURCE_LIMITS.get(tier, {'ram_mb': 256, 'cpu_pct': 60.0})
    msg = bot.send_message(
        call.message.chat.id,
        f"⚙️ Editing *{tier.upper()}* Tier Limits\nCurrent: `{cur['ram_mb']} MB` RAM, `{cur['cpu_pct']}%` CPU\n\n"
        f"Send new `RAM_MB CPU_PERCENT` separated by space (e.g. `512 80`):",
        parse_mode='Markdown'
    )
    bot.register_next_step_handler(msg, lambda m: process_edit_tier_step(m, tier))

def process_edit_tier_step(message, tier):
    if not message.text: return
    try:
        parts = message.text.strip().split()
        if len(parts) != 2: raise ValueError
        ram_mb = int(parts[0])
        cpu_pct = float(parts[1])
        if ram_mb < 32 or cpu_pct <= 5: raise ValueError
        update_tier_limit_db(tier, ram_mb, cpu_pct)
        safe_reply(message, f"✅ Updated *{tier.upper()}* Tier Limits to `{ram_mb} MB` RAM and `{cpu_pct}%` CPU.", parse_mode='Markdown')
    except ValueError:
        safe_reply(message, "❌ Invalid format! Send `RAM_MB CPU_PERCENT` (e.g., `512 80`).", parse_mode='Markdown')

def owner_autorestart_all_callback(call):
    count = 0
    for uid, files in user_files.items():
        for fname, _ in files:
            set_auto_restart_db(uid, fname, True)
            count += 1
    bot.answer_callback_query(call.id, f"🔁 Enabled Auto-Restart for all {count} saved scripts!", show_alert=True)
    owner_panel_callback(call)

def owner_kill_all_callback(call):
    killed = 0
    for script_key, process_info in list(bot_scripts.items()):
        process_info['manual_stop'] = True
        kill_process_tree(process_info)
        bot_scripts.pop(script_key, None)
        killed += 1
    bot.answer_callback_query(call.id, f"🛑 Terminated {killed} running scripts.", show_alert=True)
    owner_panel_callback(call)

def toggle_docker_callback(call):
    global USE_DOCKER_SANDBOX
    if not DOCKER_BIN and not USE_DOCKER_SANDBOX:
        bot.answer_callback_query(call.id, "⚠️ Docker executable not found in PATH! Running in Local Subprocess mode.", show_alert=True)
        return
    USE_DOCKER_SANDBOX = not USE_DOCKER_SANDBOX
    state_str = "ENABLED 🐳" if USE_DOCKER_SANDBOX else "DISABLED ⚡"
    bot.answer_callback_query(call.id, f"Docker Sandbox Mode {state_str}", show_alert=True)
    owner_panel_callback(call)

def toggle_autorestart_callback(call):
    _, script_owner_id_str, file_name = call.data.split('_', 2)
    script_owner_id = int(script_owner_id_str)
    requesting_user_id = call.from_user.id

    if not (requesting_user_id == script_owner_id or requesting_user_id in admin_ids):
        bot.answer_callback_query(call.id, "⚠️ Permission denied.", show_alert=True)
        return

    script_key = f"{script_owner_id}_{file_name}"
    new_state = script_key not in auto_restart_scripts
    set_auto_restart_db(script_owner_id, file_name, new_state)
    bot.answer_callback_query(call.id, f"🔁 Auto-Restart {'ENABLED 🟢' if new_state else 'DISABLED 🔴'} for {file_name}")

    is_running = is_bot_running(script_owner_id, file_name)
    status_text = '🟢 Running' if is_running else '🔴 Stopped'
    user_files_list = user_files.get(script_owner_id, [])
    file_type = next((f[1] for f in user_files_list if f[0] == file_name), '?')
    bot.edit_message_text(
        f"⚙️ Controls for: `{file_name}` ({file_type}) of User `{script_owner_id}`\nStatus: {status_text}",
        call.message.chat.id, call.message.message_id,
        reply_markup=create_control_buttons(script_owner_id, file_name, is_running),
        parse_mode='Markdown'
    )
        bot.edit_message_text(
        f"⚙️ Controls for: `{file_name}` ({file_type}) of User `{script_owner_id}`\nStatus: {status_text}",
        call.message.chat.id, call.message.message_id,
        reply_markup=create_control_buttons(script_owner_id, file_name, is_running),
        parse_mode='Markdown'
    )

# --- Standard Callbacks ---
def handle_approval_action(call):
    action, approval_id = call.data.split('_', 1)
    if call.from_user.id != OWNER_ID:
        bot.answer_callback_query(call.id, "❌ Only the owner can approve/reject.", show_alert=True)
        return
    if approval_id not in pending_approvals:
        bot.answer_callback_query(call.id, "❌ Request expired or already processed.", show_alert=True)
        bot.edit_message_text(f"{call.message.text}\n\n*(Expired or already processed)*", call.message.chat.id, call.message.message_id)
        return
    req = pending_approvals.pop(approval_id)
    if action == 'approve':
        bot.answer_callback_query(call.id, "✅ Approved.")
        bot.edit_message_text(f"✅ Approved run for `{req['file_name']}` (User: `{req['script_owner_id']}`).", call.message.chat.id, call.message.message_id, parse_mode='Markdown')
        try: bot.send_message(req['message'].chat.id, f"✅ Owner approved the execution of `{req['file_name']}`. Starting now...", parse_mode='Markdown')
        except Exception: pass
        if req['file_type'] == 'py': threading.Thread(target=run_script, args=(req['file_path'], req['script_owner_id'], req['user_folder'], req['file_name'], req['message']), daemon=True).start()
        elif req['file_type'] == 'js': threading.Thread(target=run_js_script, args=(req['file_path'], req['script_owner_id'], req['user_folder'], req['file_name'], req['message']), daemon=True).start()
    elif action == 'reject':
        bot.answer_callback_query(call.id, "❌ Rejected.")
        bot.edit_message_text(f"❌ Rejected run for `{req['file_name']}` (User: `{req['script_owner_id']}`).", call.message.chat.id, call.message.message_id, parse_mode='Markdown')
        try: bot.send_message(req['message'].chat.id, f"❌ Owner *denied* the execution of `{req['file_name']}`.", parse_mode='Markdown')
        except Exception: pass

def broadcast_callback(call):
    bot.answer_callback_query(call.id)
    _logic_broadcast_init(PseudoMessage(call.from_user, call.message.chat.id))

def stats_proc_callback(call):
    _, _, script_owner_id_str, file_name = call.data.split('_', 3)
    script_owner_id = int(script_owner_id_str)
    script_key = f"{script_owner_id}_{file_name}"
    script_info = bot_scripts.get(script_key)
    if not script_info or not is_bot_running(script_owner_id, file_name):
        bot.answer_callback_query(call.id, "⚠️ Script is not currently running.", show_alert=True)
        return

    process = script_info['process']
    mem_mb, cpu_pct, threads = get_process_tree_stats(process.pid)
    peak_mem = max(script_info.get('peak_mem_mb', 0.0), mem_mb)
    max_ram_mb, max_cpu_pct, tier_label = get_user_resource_limits(script_owner_id)
    ram_cap_str = "Unlimited" if max_ram_mb == float('inf') else f"{max_ram_mb} MB"
    uptime = str(datetime.now() - script_info['start_time']).split('.')[0]
    mode = "🐳 Docker Container" if script_info.get('container_name') else "⚡ Local Subprocess"
    ar_status = "🟢 ON" if script_key in auto_restart_scripts else "🔴 OFF"

    bot.answer_callback_query(call.id)
    stats_text = (
        f"📊 *Live Process Resource Stats*\n\n"
        f"📄 *File:* `{file_name}`\n"
        f"👤 *Tier:* {tier_label}\n"
        f"🆔 *PID:* `{process.pid}`\n"
        f"⚙️ *Engine:* {mode}\n"
        f"🔁 *Auto-Restart:* {ar_status}\n"
        f"⏱️ *Uptime:* `{uptime}`\n"
        f"🧠 *RAM Usage:* `{mem_mb} MB` / `{ram_cap_str}` (Peak: `{peak_mem} MB`)\n"
        f"⚡ *CPU Usage:* `{cpu_pct}%` (Cap: `{max_cpu_pct}%`)\n"
        f"🧵 *Active Threads:* `{threads}`"
    )
    bot.send_message(call.message.chat.id, stats_text, parse_mode='Markdown')

def scan_file_callback(call):
    _, script_owner_id_str, file_name = call.data.split('_', 2)
    script_owner_id = int(script_owner_id_str)
    user_folder = get_user_folder(script_owner_id)
    file_path = os.path.join(user_folder, file_name)
    if not os.path.exists(file_path):
        bot.answer_callback_query(call.id, "❌ File not found on disk.", show_alert=True)
        return

    file_ext = os.path.splitext(file_name)[1].lower().replace('.', '')
    _, risk_level, issues = scan_script_security(file_path, file_ext)
    bot.answer_callback_query(call.id, f"Scan Result: {risk_level}")
    issues_str = "\n".join(f"• {i}" for i in issues) if issues else "• No suspicious AST nodes or blocked imports detected."
    report_msg = (
        f"🛡️ *AST Static Security Report*\n\n"
        f"📄 *File:* `{file_name}`\n"
        f"🚦 *Verdict:* {risk_level}\n\n"
        f"*Findings:*\n{issues_str}"
    )
    bot.send_message(call.message.chat.id, report_msg, parse_mode='Markdown')

def send_command_callback(call):
    bot.answer_callback_query(call.id)
    bot.edit_message_text("📤 Send Command Options:", call.message.chat.id, call.message.message_id, reply_markup=create_send_command_menu())

def send_to_process_callback(call):
    bot.answer_callback_query(call.id)
    send_to_process_init(call.message, call.from_user.id)

def sendcmd_select_callback(call):
    script_key = call.data.replace('sendcmd_select_', '')
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id, f"📝 Enter command to send to `{script_key}`:", parse_mode='Markdown')
    bot.register_next_step_handler(msg, lambda m: process_send_command(m, script_key))

def view_all_logs_callback(call):
    bot.answer_callback_query(call.id)
    view_all_logs(call.message)

def viewlog_callback(call):
    _, user_id_str, log_filename = call.data.split('_', 2)
    user_id = int(user_id_str)
    requesting_user_id = call.from_user.id
    if not (requesting_user_id == user_id or requesting_user_id in admin_ids):
        bot.answer_callback_query(call.id, "⚠️ You can only view your own logs.", show_alert=True)
        return
    user_folder = get_user_folder(user_id)
    log_path = os.path.join(user_folder, log_filename)
    if not os.path.exists(log_path):
        bot.answer_callback_query(call.id, "❌ Log file not found.", show_alert=True)
        return
    bot.answer_callback_query(call.id, "📜 Sending log file...")
    send_log_file(call.message, log_path, log_filename)

def upload_callback(call):
    user_id = call.from_user.id
    file_limit = get_user_file_limit(user_id)
    current_files = get_user_file_count(user_id)
    if current_files >= file_limit:
        bot.answer_callback_query(call.id, "⚠️ File limit reached.", show_alert=True)
        return
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, "📤 Send your Python (`.py`), JS (`.js`), or ZIP (`.zip`) file.")

def check_files_callback(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    user_files_list = user_files.get(user_id, [])
    if not user_files_list:
        bot.answer_callback_query(call.id, "⚠️ No files uploaded.", show_alert=True)
        markup = types.InlineKeyboardMarkup()
        markup.add(colorful_btn("🔙 Back to Main", callback_data='back_to_main', style='primary'))
        bot.edit_message_text("📂 Your files:\n\n(No files uploaded)", chat_id, call.message.message_id, reply_markup=markup)
        return
    bot.answer_callback_query(call.id)
    markup = types.InlineKeyboardMarkup(row_width=1)
    for file_name, file_type in sorted(user_files_list):
        is_running = is_bot_running(user_id, file_name)
        status_icon = "🟢 Running" if is_running else "🔴 Stopped"
        ar_icon = " 🔁" if f"{user_id}_{file_name}" in auto_restart_scripts else ""
        btn_style = 'success' if is_running else 'danger'
        btn_text = f"{file_name} ({file_type}) - {status_icon}{ar_icon}"
        markup.add(colorful_btn(btn_text, callback_data=f'file_{user_id}_{file_name}', style=btn_style))
    markup.add(colorful_btn("🔙 Back to Main", callback_data='back_to_main', style='primary'))
    bot.edit_message_text("📂 Your files:\nClick to manage.", chat_id, call.message.message_id, reply_markup=markup, parse_mode='Markdown')

def file_control_callback(call):
    _, script_owner_id_str, file_name = call.data.split('_', 2)
    script_owner_id = int(script_owner_id_str)
    requesting_user_id = call.from_user.id

    if not (requesting_user_id == script_owner_id or requesting_user_id in admin_ids):
        bot.answer_callback_query(call.id, "⚠️ You can only manage your own files.", show_alert=True)
        return

    user_files_list = user_files.get(script_owner_id, [])
    bot.answer_callback_query(call.id)
    is_running = is_bot_running(script_owner_id, file_name)
    status_text = '🟢 Running' if is_running else '🔴 Stopped'
    file_type = next((f[1] for f in user_files_list if f[0] == file_name), '?')
    bot.edit_message_text(f"⚙️ Controls for: `{file_name}` ({file_type}) of User `{script_owner_id}`\nStatus: {status_text}",
        call.message.chat.id, call.message.message_id, reply_markup=create_control_buttons(script_owner_id, file_name, is_running), parse_mode='Markdown')

def start_bot_callback(call):
    _, script_owner_id_str, file_name = call.data.split('_', 2)
    script_owner_id = int(script_owner_id_str)
    user_files_list = user_files.get(script_owner_id, [])
    file_info = next((f for f in user_files_list if f[0] == file_name), None)
    if not file_info:
        bot.answer_callback_query(call.id, "⚠️ File not found.", show_alert=True)
        return
    file_type = file_info[1]
    user_folder = get_user_folder(script_owner_id)
    file_path = os.path.join(user_folder, file_name)

    crash_restart_counts[f"{script_owner_id}_{file_name}"] = 0
    bot.answer_callback_query(call.id, "⏳ Starting script...")
    user_pseudo_msg = PseudoMessage(call.from_user, call.message.chat.id)
    request_run_script(file_type, file_path, script_owner_id, user_folder, file_name, user_pseudo_msg, requesting_user_id=call.from_user.id)
    time.sleep(1)

    is_now_running = is_bot_running(script_owner_id, file_name)
    status_text = '🟢 Running' if is_now_running else '⏳ Pending / 🔴 Stopped'
    bot.edit_message_text(f"⚙️ Controls for: `{file_name}` ({file_type}) of User `{script_owner_id}`\nStatus: {status_text}",
        call.message.chat.id, call.message.message_id, reply_markup=create_control_buttons(script_owner_id, file_name, is_now_running), parse_mode='Markdown')

def stop_bot_callback(call):
    _, script_owner_id_str, file_name = call.data.split('_', 2)
    script_owner_id = int(script_owner_id_str)
    script_key = f"{script_owner_id}_{file_name}"

    bot.answer_callback_query(call.id, "⏳ Stopping script...")
    process_info = bot_scripts.get(script_key)
    if process_info:
        process_info['manual_stop'] = True
        kill_process_tree(process_info)
        bot_scripts.pop(script_key, None)

    bot.edit_message_text(f"⚙️ Controls for: `{file_name}` of User `{script_owner_id}`\nStatus: 🔴 Stopped",
        call.message.chat.id, call.message.message_id, reply_markup=create_control_buttons(script_owner_id, file_name, False), parse_mode='Markdown')

def restart_bot_callback(call):
    _, script_owner_id_str, file_name = call.data.split('_', 2)
    script_owner_id = int(script_owner_id_str)
    script_key = f"{script_owner_id}_{file_name}"

    process_info = bot_scripts.get(script_key)
    if process_info:
        process_info['manual_stop'] = True
        kill_process_tree(process_info)
        bot_scripts.pop(script_key, None)
    time.sleep(1)
    start_bot_callback(call)

def delete_bot_callback(call):
    _, script_owner_id_str, file_name = call.data.split('_', 2)
    script_owner_id = int(script_owner_id_str)
    script_key = f"{script_owner_id}_{file_name}"

    if is_bot_running(script_owner_id, file_name):
        process_info = bot_scripts.get(script_key)
        if process_info:
            process_info['manual_stop'] = True
            kill_process_tree(process_info)
        bot_scripts.pop(script_key, None)

    user_folder = get_user_folder(script_owner_id)
    file_path = os.path.join(user_folder, file_name)
    log_path = os.path.join(user_folder, f"{os.path.splitext(file_name)[0]}.log")

    safe_remove(file_path)
    safe_remove(log_path)
    remove_user_file_db(script_owner_id, file_name)

    if not user_files.get(script_owner_id):
        safe_rmtree(user_folder)

    bot.edit_message_text(f"🗑️ `{file_name}` and associated logs deleted.", call.message.chat.id, call.message.message_id, reply_markup=None)

def logs_bot_callback(call):
    _, script_owner_id_str, file_name = call.data.split('_', 2)
    script_owner_id = int(script_owner_id_str)
    user_folder = get_user_folder(script_owner_id)
    log_path = os.path.join(user_folder, f"{os.path.splitext(file_name)[0]}.log")

    if not os.path.exists(log_path):
        bot.answer_callback_query(call.id, "⚠️ No logs available yet.", show_alert=True)
        return

    bot.answer_callback_query(call.id)
    try:
        with open(log_path, 'rb') as f:
            f.seek(0, os.SEEK_END)
            file_size = f.tell()
            f.seek(max(file_size - 3500, 0), os.SEEK_SET)
            log_content = f.read().decode('utf-8', errors='ignore')

        if not log_content.strip():
            log_content = "(Log file is empty)"
        bot.send_message(call.message.chat.id, f"📜 Logs for `{file_name}`:\n```\n{log_content}\n```", parse_mode='Markdown')
    except Exception as e:
        bot.send_message(call.message.chat.id, f"❌ Failed to read logs: {e}")

def speed_callback(call):
    bot.answer_callback_query(call.id)
    _logic_bot_speed(call.message)

def stats_callback(call):
    bot.answer_callback_query(call.id)
    _logic_statistics(call.message)

def lock_bot_callback(call):
    bot.answer_callback_query(call.id)
    _logic_toggle_lock_bot(call.message)

def unlock_bot_callback(call):
    bot.answer_callback_query(call.id)
    _logic_toggle_lock_bot(call.message)

def run_all_scripts_callback(call):
    _logic_run_all_scripts(call)

def admin_panel_callback(call):
    bot.answer_callback_query(call.id)
    bot.edit_message_text("🛡️ Admin Panel Options:", call.message.chat.id, call.message.message_id, reply_markup=create_admin_panel(call.from_user.id))

def subscription_management_callback(call):
    bot.answer_callback_query(call.id)
    bot.edit_message_text("💳 Subscription Management Options:", call.message.chat.id, call.message.message_id, reply_markup=create_subscription_menu())

def back_to_main_callback(call):
    bot.answer_callback_query(call.id)
    bot.edit_message_text("〽️ Welcome back! Choose an option:", call.message.chat.id, call.message.message_id, reply_markup=create_main_menu_inline(call.from_user.id))

def add_admin_callback(call):
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id, "👤 Send the *User ID* to add as an admin:", parse_mode="Markdown")
    bot.register_next_step_handler(msg, process_add_admin)

def process_add_admin(message):
    if not message.text: return
    try:
        new_admin_id = int(message.text.strip())
        add_admin_db(new_admin_id)
        safe_reply(message, f"✅ User `{new_admin_id}` added as Admin.", parse_mode="Markdown")
    except ValueError: safe_reply(message, "❌ Invalid format. Send a numeric User ID.")

def remove_admin_callback(call):
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id, "👤 Send the *User ID* to remove from admins:", parse_mode="Markdown")
    bot.register_next_step_handler(msg, process_remove_admin)

def process_remove_admin(message):
    if not message.text: return
    try:
        admin_id_to_remove = int(message.text.strip())
        if remove_admin_db(admin_id_to_remove): safe_reply(message, f"✅ User `{admin_id_to_remove}` removed from admins.", parse_mode="Markdown")
        else: safe_reply(message, f"❌ Failed. Target is not an admin or is Owner.", parse_mode="Markdown")
    except ValueError: safe_reply(message, "❌ Invalid format. Send a numeric User ID.")

def ban_user_callback(call):
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id, "🚫 Send the *User ID* or *@username* to ban:", parse_mode="Markdown")
    bot.register_next_step_handler(msg, process_ban_user_step)

def process_ban_user_step(message):
    if not message.text: return
    target = message.text.replace('@', '').strip().lower()
    target_id = int(target) if target.isdigit() else username_to_id.get(target)

    if target_id:
        if target_id == OWNER_ID or target_id in admin_ids:
            safe_reply(message, "❌ Cannot ban an admin or owner.")
            return
        ban_user_db(target_id)
        safe_reply(message, f"✅ User `{target_id}` has been successfully banned.", parse_mode="Markdown")
    else:
        safe_reply(message, "❌ User not found in database. Try their numerical ID.")

def unban_user_callback(call):
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id, "✅ Send the *User ID* or *@username* to unban:", parse_mode="Markdown")
    bot.register_next_step_handler(msg, process_unban_user_step)

def process_unban_user_step(message):
    if not message.text: return
    target = message.text.replace('@', '').strip().lower()
    target_id = int(target) if target.isdigit() else username_to_id.get(target)

    if target_id:
        unban_user_db(target_id)
        safe_reply(message, f"✅ User `{target_id}` has been unbanned.", parse_mode="Markdown")
    else:
        safe_reply(message, "❌ User not found.")

def list_admins_callback(call):
    bot.answer_callback_query(call.id)
    admin_list_text = "\n".join([f"• `{uid}`" for uid in admin_ids])
    bot.send_message(call.message.chat.id, f"📋 *Current Admins:*\n{admin_list_text}", parse_mode="Markdown")

def add_subscription_callback(call):
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id, "💳 Send the *User ID* and *Days* separated by space.\nExample: `123456789 30`", parse_mode="Markdown")
    bot.register_next_step_handler(msg, process_add_subscription)

def process_add_subscription(message):
    if not message.text: return
    try:
        parts = message.text.strip().split()
        if len(parts) != 2: raise ValueError
        user_id = int(parts[0])
        days = int(parts[1])
        expiry_date = datetime.now() + timedelta(days=days)
        save_subscription(user_id, expiry_date)
        safe_reply(message, f"✅ Subscription added for User `{user_id}`.\n⏳ Duration: *{days} days*\n📅 Expires: `{expiry_date.strftime('%Y-%m-%d %H:%M')}`", parse_mode="Markdown")
    except ValueError: safe_reply(message, "❌ Invalid format. Provide ID and days (e.g., `1234567 30`).", parse_mode="Markdown")

def remove_subscription_callback(call):
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id, "💳 Send the *User ID* to revoke their subscription:", parse_mode="Markdown")
    bot.register_next_step_handler(msg, process_remove_subscription)

def process_remove_subscription(message):
    if not message.text: return
    try:
        user_id = int(message.text.strip())
        remove_subscription_db(user_id)
        safe_reply(message, f"✅ Subscription revoked for User `{user_id}`.", parse_mode="Markdown")
    except ValueError: safe_reply(message, "❌ Invalid format. Send a numeric User ID.")

def check_subscription_callback(call):
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id, "🔍 Send the *User ID* to check status:", parse_mode="Markdown")
    bot.register_next_step_handler(msg, process_check_subscription)

def process_check_subscription(message):
    if not message.text: return
    try:
        user_id = int(message.text.strip())
        if user_id in user_subscriptions:
            expiry = user_subscriptions[user_id].get('expiry')
            if expiry and expiry > datetime.now():
                days_left = (expiry - datetime.now()).days
                safe_reply(message, f"⭐ User `{user_id}` has *Premium*.\n⏳ Expires in: *{days_left} days*\n📅 Date: `{expiry.strftime('%Y-%m-%d %H:%M')}`", parse_mode="Markdown")
            else:
                remove_subscription_db(user_id)
                safe_reply(message, f"❌ User `{user_id}`'s subscription has expired.", parse_mode="Markdown")
        else: safe_reply(message, f"🆓 User `{user_id}` has no active subscription.", parse_mode="Markdown")
    except ValueError: safe_reply(message, "❌ Invalid format. Send a numeric User ID.")

def manage_all_files_callback(call):
    bot.answer_callback_query(call.id)
    markup = types.InlineKeyboardMarkup(row_width=1)
    users_with_files = [uid for uid, files in user_files.items() if files]

    if not users_with_files:
        markup.add(colorful_btn("🔙 Back to Admin Panel", callback_data='admin_panel', style='primary'))
        bot.edit_message_text("📂 No users have uploaded files yet.", call.message.chat.id, call.message.message_id, reply_markup=markup)
        return

    id_to_username = {uid: uname for uname, uid in username_to_id.items()}

    for uid in users_with_files[:50]:
        files = user_files[uid]
        running_count = sum(1 for f in files if is_bot_running(uid, f[0]))
        uname = id_to_username.get(uid)
        display_name = f"@{uname}" if uname else f"{uid}"
        btn_text = f"👤 {display_name} - {len(files)} files ({running_count} running)"
        btn_style = 'success' if running_count > 0 else 'primary'
        markup.add(colorful_btn(btn_text, callback_data=f'admin_user_files_{uid}', style=btn_style))

    markup.add(colorful_btn("🔙 Back to Admin Panel", callback_data='admin_panel', style='primary'))
    bot.edit_message_text("🗂️ Select a user to manage files:", call.message.chat.id, call.message.message_id, reply_markup=markup)

def admin_user_files_callback(call):
    target_uid = int(call.data.replace('admin_user_files_', ''))
    bot.answer_callback_query(call.id)
    files_list = user_files.get(target_uid, [])
    markup = types.InlineKeyboardMarkup(row_width=1)

    if not files_list:
        markup.add(colorful_btn("🔙 Back to Users", callback_data='manage_all_files', style='primary'))
        bot.edit_message_text(f"📂 User `{target_uid}` has no files.", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode='Markdown')
        return

    for file_name, file_type in sorted(files_list):
        is_running = is_bot_running(target_uid, file_name)
        status_icon = "🟢 Running" if is_running else "🔴 Stopped"
        ar_icon = " 🔁" if f"{target_uid}_{file_name}" in auto_restart_scripts else ""
        btn_style = 'success' if is_running else 'danger'
        btn_text = f"{file_name} ({file_type}) - {status_icon}{ar_icon}"
        markup.add(colorful_btn(btn_text, callback_data=f'file_{target_uid}_{file_name}', style=btn_style))

    markup.add(colorful_btn("🔙 Back to Users", callback_data='manage_all_files', style='primary'))
    bot.edit_message_text(f"📂 Files for User `{target_uid}`:\nClick to manage.", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode='Markdown')

def users_list_callback(call):
    bot.answer_callback_query(call.id)
    user_data = []
    for uid in list(active_users):
        file_count = len(user_files.get(uid, []))
        user_data.append({'uid': uid, 'count': file_count})

    user_data.sort(key=lambda x: x['count'], reverse=True)
    id_to_username = {uid: uname for uname, uid in username_to_id.items()}

    lines = []
    for user in user_data[:60]:
        uid = user['uid']
        count = user['count']
        uname = id_to_username.get(uid)
        name_display = f"@{uname}" if uname else f"`{uid}`"
        lines.append(f"• {name_display} : {count} files")

    full_text = "👥 *All Users & Uploaded Files:*\n\n" + ("\n".join(lines) if lines else "(No active users)")
    if len(full_text) > 3900:
        full_text = full_text[:3850] + "\n\n... *(List truncated)*"

    markup = types.InlineKeyboardMarkup()
    markup.add(colorful_btn("🔙 Back to Admin Panel", callback_data='admin_panel', style='primary'))
    bot.edit_message_text(full_text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode='Markdown')

# --- Owner Factory Reset Logic ---
def execute_factory_reset():
    for script_key, process_info in list(bot_scripts.items()):
        process_info['manual_stop'] = True
        kill_process_tree(process_info)
    bot_scripts.clear()
    auto_restart_scripts.clear()
    crash_restart_counts.clear()

    safe_rmtree(UPLOAD_BOTS_DIR)
    os.makedirs(UPLOAD_BOTS_DIR, exist_ok=True)

    user_files.clear()
    user_subscriptions.clear()

    admin_ids.clear()
    admin_ids.add(OWNER_ID)
    if ADMIN_ID != OWNER_ID:
        admin_ids.add(ADMIN_ID)

    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, timeout=30, check_same_thread=False)
        c = conn.cursor()
        try:
            c.execute('DELETE FROM user_files')
            c.execute('DELETE FROM subscriptions')
            c.execute('DELETE FROM auto_restart_prefs')
            c.execute('DELETE FROM admins WHERE user_id != ? AND user_id != ?', (OWNER_ID, ADMIN_ID))
            conn.commit()
            logger.warning("♻️ Complete Factory Reset executed successfully.")
        except Exception as e:
            logger.error(f"❌ SQLite error during Factory Reset: {e}")
        finally:
            conn.close()

def factory_reset_callback(call):
    bot.answer_callback_query(call.id)
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        colorful_btn("✅ YES, WIPE EVERYTHING", callback_data='confirm_reset', style='danger'),
        colorful_btn("❌ CANCEL", callback_data='owner_panel', style='success')
    )

    warning_text = (
        "⚠️ *WARNING: COMPLETE FACTORY RESET* ⚠️\n\n"
        "Are you sure? This action cannot be undone.\n\n"
        "• ALL running scripts will be terminated.\n"
        "• ALL uploaded files will be permanently deleted.\n"
        "• ALL non-default admins will be removed.\n"
        "• ALL subscriptions & auto-restarts will be reset."
    )
    bot.edit_message_text(warning_text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode='Markdown')

def confirm_reset_callback(call):
    bot.answer_callback_query(call.id, "♻️ Wiping system...")
    bot.edit_message_text("♻️ Factory Reset in progress... Terminating processes and wiping data...", call.message.chat.id, call.message.message_id)

    execute_factory_reset()

    markup = types.InlineKeyboardMarkup()
    markup.add(colorful_btn("🔙 Back to Main Menu", callback_data='back_to_main', style='primary'))
    bot.edit_message_text("✅ *Factory Reset Complete!*\n\nSystem wiped cleanly.", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode='Markdown')

def auto_start_saved_scripts():
    logger.info("🔄 Auto-starting all saved user scripts...")
    all_user_files_snapshot = dict(user_files)
    for target_user_id, files_for_user in all_user_files_snapshot.items():
        if not files_for_user: continue

        user_folder = get_user_folder(target_user_id)
        for file_name, file_type in files_for_user:
            file_path = os.path.join(user_folder, file_name)
            if os.path.exists(file_path):
                dummy_user = type('User', (), {'id': target_user_id, 'first_name': 'System', 'username': None})()
                dummy_msg = PseudoMessage(dummy_user)
                logger.info(f"▶️ Auto-starting {file_name} for user {target_user_id}")
                try:
                    if file_type == 'py': threading.Thread(target=run_script, args=(file_path, target_user_id, user_folder, file_name, dummy_msg), daemon=True).start()
                    elif file_type == 'js': threading.Thread(target=run_js_script, args=(file_path, target_user_id, user_folder, file_name, dummy_msg), daemon=True).start()
                    time.sleep(1)
                except Exception as e: logger.error(f"❌ Failed to auto-start {file_name} for {target_user_id}: {e}")

def cleanup_on_exit():
    """Terminate all active child processes on bot shutdown."""
    logger.info("🛑 Bot shutting down. Terminating active child processes...")
    for script_key, script_info in list(bot_scripts.items()):
        try:
            script_info['manual_stop'] = True
            kill_process_tree(script_info)
        except Exception: pass

atexit.register(cleanup_on_exit)

# =========================================================================
# 🖥️  SMALL TERMINAL  —  Manual / automatic package downloader for files
# =========================================================================
TERMINAL_WELCOME = (
    "╔═══════════════════════════════╗\n"
    "║  🖥️  *REBEL HOSTING TERMINAL*  ║\n"
    "╚═══════════════════════════════╝\n\n"
    "📌 *Type commands below as normal text messages.*\n"
    "📌 _Type_ `help` _to see all commands._\n"
    "📌 _Type_ `exit` _to close the terminal._"
)

TERMINAL_HELP = (
    "🖥️ *TERMINAL — Available Commands*\n\n"
    "🐍 *Python (pip):*\n"
    "• `pip install <pkg>` — Install one or more packages\n"
    "• `pip install -r requirements.txt` — Install from file\n"
    "• `pip uninstall <pkg>` — Uninstall a package\n"
    "• `pip list` — Show installed packages\n"
    "• `pip freeze` — Show pip-format package list\n"
    "• `pip show <pkg>` — Show info about a package\n\n"
    "🟠 *Node.js (npm):*\n"
    "• `npm install <pkg>` — Install a package\n"
    "• `npm install` — Install all from package.json\n"
    "• `npm list` — Show installed node packages\n\n"
    "🪄 *Auto-download for files:*\n"
    "• `deps <file.py>` — Auto-detect + install Python imports\n"
    "• `deps <file.js>` — Auto-detect + install Node requires\n\n"
    "📂 *Files:*\n"
    "• `ls` — List your workspace files\n"
    "• `cat <file>` — Show file content (max ~200 KB)\n\n"
    "⚙️ *Other:*\n"
    "• `help` — Show this help\n"
    "• `exit` — Close terminal"
)

def _terminal_output_block(text):
    text = (text or "").strip()
    if not text:
        text = "(no output)"
    if len(text) > 3300:
        text = text[:3200] + "\n... (truncated)"
    return f"```\n{text}\n```"

def _is_module_importable(modname):
    try:
        import importlib.util
        return importlib.util.find_spec(modname) is not None
    except (ImportError, ModuleNotFoundError, ValueError):
        return False

def create_terminal_inline_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.row(
        colorful_btn('❓ Help', callback_data='term_help', style='primary'),
        colorful_btn('📋 List Files', callback_data='term_ls', style='success')
    )
    markup.row(colorful_btn('🔒 Close Terminal', callback_data='term_close', style='danger'))
    return markup

def open_terminal_for_user(chat_id, user_id):
    terminal_sessions[user_id] = True
    get_user_folder(user_id)
    bot.send_message(chat_id, TERMINAL_WELCOME, parse_mode='Markdown',
                     reply_markup=create_terminal_inline_menu())
    bot.send_message(
        chat_id,
        f"👤 *User:* `{user_id}`\n📁 *Workspace:* `upload_bots/{user_id}/`",
        parse_mode='Markdown'
    )

def _run_terminal_pip(message, cmd_args, user_id):
    action = (cmd_args[0] if cmd_args else "").lower()
    user_folder = get_user_folder(user_id)

    if action == 'list':
        try:
            r = subprocess.run([sys.executable, '-m', 'pip', 'list', '--format=columns'],
                               capture_output=True, text=True, timeout=60,
                               encoding='utf-8', errors='ignore')
            out = (r.stdout or r.stderr or "(no output)").strip()
            safe_reply(message, f"📦 *Installed Python packages:*\n{_terminal_output_block(out)}", parse_mode='Markdown')
        except Exception as e:
            safe_reply(message, f"❌ pip list error: `{e}`", parse_mode='Markdown')
        return

    if action == 'freeze':
        try:
            r = subprocess.run([sys.executable, '-m', 'pip', 'freeze'],
                               capture_output=True, text=True, timeout=60,
                               encoding='utf-8', errors='ignore')
            out = (r.stdout or "(no output)").strip()
            safe_reply(message, f"🧊 *pip freeze:*\n{_terminal_output_block(out)}", parse_mode='Markdown')
        except Exception as e:
            safe_reply(message, f"❌ pip freeze error: `{e}`", parse_mode='Markdown')
        return

    if action == 'show':
        if len(cmd_args) < 2:
            safe_reply(message, "❌ Usage: `pip show <package>`", parse_mode='Markdown')
            return
        try:
            r = subprocess.run([sys.executable, '-m', 'pip', 'show', cmd_args[1]],
                               capture_output=True, text=True, timeout=60,
                               encoding='utf-8', errors='ignore')
            out = (r.stdout or r.stderr or "(no output)").strip()
            safe_reply(message, f"ℹ️ *pip show {cmd_args[1]}:*\n{_terminal_output_block(out)}", parse_mode='Markdown')
        except Exception as e:
            safe_reply(message, f"❌ pip show error: `{e}`", parse_mode='Markdown')
        return

    if action in ('install', 'uninstall'):
        if len(cmd_args) > 20:
            safe_reply(message, "❌ Too many arguments.", parse_mode='Markdown')
            return
        for arg in cmd_args:
            if arg.lower().startswith(('--target', '--prefix', '--root', '--root-user-action')):
                safe_reply(message, f"❌ Flag `{arg}` not allowed in terminal.", parse_mode='Markdown')
                return

        safe_reply(message, f"⏳ Running `pip {' '.join(cmd_args)}`...\n_This can take 1–2 minutes._", parse_mode='Markdown')
        cmd = [sys.executable, '-m', 'pip'] + cmd_args
        try:
            run_cwd = user_folder if any(a in ('-r', '--requirement') for a in cmd_args) else None
            if run_cwd:
                r = subprocess.run(cmd, cwd=run_cwd, capture_output=True, text=True,
                                   check=False, encoding='utf-8', errors='ignore')
                if r.returncode != 0 and 'externally-managed-environment' in (r.stderr or ''):
                    if '--break-system-packages' not in cmd:
                        cmd.append('--break-system-packages')
                    r = subprocess.run(cmd, cwd=run_cwd, capture_output=True, text=True,
                                       check=False, encoding='utf-8', errors='ignore')
            else:
                r = run_pip_command(cmd)
            out = ((r.stdout or '') + '\n' + (r.stderr or '')).strip()
            icon = "✅" if r.returncode == 0 else "❌"
            safe_reply(message, f"{icon} *pip {action}* (exit `{r.returncode}`):\n{_terminal_output_block(out)}", parse_mode='Markdown')
        except Exception as e:
            safe_reply(message, f"❌ Error running pip: `{e}`", parse_mode='Markdown')
        return

    safe_reply(message, "❌ Unknown pip action. Allowed: `install`, `uninstall`, `list`, `freeze`, `show`.", parse_mode='Markdown')


def _run_terminal_npm(message, cmd_args, user_id):
    if not cmd_args:
        safe_reply(message, "❌ Usage: `npm install <package>` or `npm install`", parse_mode='Markdown')
        return
    action = cmd_args[0].lower()
    user_folder = get_user_folder(user_id)
    use_shell = (os.name == 'nt')

    if action in ('install', 'i'):
        if len(cmd_args) > 10:
            safe_reply(message, "❌ Too many arguments.", parse_mode='Markdown')
            return
        desc = ' '.join(cmd_args[1:]) if len(cmd_args) > 1 else '(from package.json)'
        safe_reply(message, f"⏳ Running `npm {action} {desc}` in your workspace...", parse_mode='Markdown')
        try:
            r = subprocess.run([NPM_BIN] + cmd_args, capture_output=True, text=True,
                               check=False, cwd=user_folder, shell=use_shell,
                               timeout=300, encoding='utf-8', errors='ignore')
            out = ((r.stdout or '') + '\n' + (r.stderr or '')).strip()
            icon = "✅" if r.returncode == 0 else "❌"
            safe_reply(message, f"{icon} *npm {action}* (exit `{r.returncode}`):\n{_terminal_output_block(out)}", parse_mode='Markdown')
        except FileNotFoundError:
            safe_reply(message, "❌ npm not found in PATH.", parse_mode='Markdown')
        except subprocess.TimeoutExpired:
            safe_reply(message, "⏱️ npm command timed out (5 min).", parse_mode='Markdown')
        except Exception as e:
            safe_reply(message, f"❌ npm error: `{e}`", parse_mode='Markdown')
        return

    if action in ('list', 'ls'):
        try:
            r = subprocess.run([NPM_BIN, 'list', '--depth=0'], capture_output=True, text=True,
                               check=False, cwd=user_folder, shell=use_shell,
                               timeout=60, encoding='utf-8', errors='ignore')
            out = ((r.stdout or '') + (r.stderr or '')).strip() or "(no output)"
            safe_reply(message, f"📦 *npm packages:*\n{_terminal_output_block(out)}", parse_mode='Markdown')
        except Exception as e:
            safe_reply(message, f"❌ npm list error: `{e}`", parse_mode='Markdown')
        return

    safe_reply(message, "❌ Unknown npm action. Allowed: `install`, `list`.", parse_mode='Markdown')


def _run_terminal_deps(message, fname, user_id):
    if not fname or '..' in fname or '/' in fname or '\\' in fname:
        safe_reply(message, "❌ Invalid filename.", parse_mode='Markdown')
        return
    user_folder = get_user_folder(user_id)
    fpath = os.path.join(user_folder, fname)
    if not os.path.exists(fpath):
        safe_reply(message, f"❌ File `{fname}` not found in your workspace.", parse_mode='Markdown')
        return

    try:
        with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except Exception as e:
        safe_reply(message, f"❌ Cannot read file: `{e}`", parse_mode='Markdown')
        return

    # ---- Python ----
    if fname.endswith('.py'):
        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            safe_reply(message, f"❌ Python syntax error at line {e.lineno}: `{e.msg}`", parse_mode='Markdown')
            return

        modules = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for a in node.names:
                    modules.add(a.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    modules.add(node.module.split('.')[0])

        to_install = []
        for m in sorted(modules):
            if _is_module_importable(m):
                continue
            to_install.append(TELEGRAM_MODULES.get(m.lower(), m))

        if not to_install:
            safe_reply(message,
                       f"✅ All imports in `{fname}` are already satisfied.\n\n_Detected:_ `{', '.join(sorted(modules)) or '(none)'}`",
                       parse_mode='Markdown')
            return

        safe_reply(message,
                   f"🔍 *{fname}* needs {len(to_install)} package(s):\n`{' '.join(to_install)}`\n\n⏳ Installing...",
                   parse_mode='Markdown')
        try:
            r = run_pip_command([sys.executable, '-m', 'pip', 'install'] + to_install)
            out = ((r.stdout or '') + '\n' + (r.stderr or '')).strip()
            icon = "✅" if r.returncode == 0 else "❌"
            safe_reply(message, f"{icon} *Dependency install finished* (exit `{r.returncode}`):\n{_terminal_output_block(out)}", parse_mode='Markdown')
        except Exception as e:
            safe_reply(message, f"❌ pip error: `{e}`", parse_mode='Markdown')
        return

    # ---- Node.js ----
    if fname.endswith('.js'):
        raw_reqs = set(re.findall(r"require\s*\(\s*['\"]([^'\"]+)['\"]\s*\)", content))
        raw_reqs |= set(re.findall(r"(?:from|import)\s+['\"]([^'\"]+)['\"]", content))
        raw_reqs = {r for r in raw_reqs if not r.startswith('.') and not r.startswith('/')}

        to_install = set()
        for r in raw_reqs:
            if r.startswith('@'):
                parts = r.split('/')
                to_install.add('/'.join(parts[:2]) if len(parts) >= 2 else r)
            else:
                to_install.add(r.split('/')[0])

        if not to_install:
            safe_reply(message, f"✅ No external npm packages found in `{fname}`.", parse_mode='Markdown')
            return

        pkgs = sorted(to_install)
        safe_reply(message,
                   f"🔍 *{fname}* needs {len(pkgs)} npm package(s):\n`{' '.join(pkgs)}`\n\n⏳ Installing...",
                   parse_mode='Markdown')
        use_shell = (os.name == 'nt')
        try:
            r = subprocess.run([NPM_BIN, 'install'] + pkgs, capture_output=True, text=True,
                               check=False, cwd=user_folder, shell=use_shell,
                               timeout=300, encoding='utf-8', errors='ignore')
            out = ((r.stdout or '') + '\n' + (r.stderr or '')).strip()
            icon = "✅" if r.returncode == 0 else "❌"
            safe_reply(message, f"{icon} *npm install finished* (exit `{r.returncode}`):\n{_terminal_output_block(out)}", parse_mode='Markdown')
        except Exception as e:
            safe_reply(message, f"❌ npm error: `{e}`", parse_mode='Markdown')
        return

    safe_reply(message, "❌ `deps` only supports `.py` and `.js` files.", parse_mode='Markdown')


def process_terminal_command(message):
    user_id = message.from_user.id
    if not terminal_sessions.get(user_id):
        return
    if not message.text:
        safe_reply(message, "❌ Please send a text command.")
        return

    raw = message.text.strip()
    lower = raw.lower()

    if lower in ('exit', 'quit', 'close', 'logout', 'q'):
        terminal_sessions.pop(user_id, None)
        safe_reply(message, "🔒 *Terminal session closed.*\n\nUse /terminal to reopen.", parse_mode='Markdown')
        return

    if lower in ('help', '?', 'man', 'commands'):
        safe_reply(message, TERMINAL_HELP, parse_mode='Markdown')
        return

    if lower in ('ls', 'dir', 'files', 'list'):
        user_folder = get_user_folder(user_id)
        try:
            entries = []
            for item in sorted(os.listdir(user_folder)):
                full = os.path.join(user_folder, item)
                if os.path.isdir(full):
                    entries.append(f"📁 {item}/")
                else:
                    size = os.path.getsize(full)
                    size_str = f"{size}B" if size < 1024 else f"{size/1024:.1f}KB" if size < 1024*1024 else f"{size/1024/1024:.1f}MB"
                    entries.append(f"📄 {item} ({size_str})")
            if not entries:
                safe_reply(message, "📂 *(empty workspace)*", parse_mode='Markdown')
            else:
                safe_reply(message, f"📂 *Workspace files:*\n{_terminal_output_block(chr(10).join(entries))}", parse_mode='Markdown')
        except Exception as e:
            safe_reply(message, f"❌ ls error: `{e}`", parse_mode='Markdown')
        return

    if lower.startswith('cat '):
        fname = raw[4:].strip().strip('"\'')
        if not fname or '..' in fname or '/' in fname or '\\' in fname or fname.startswith('.'):
            safe_reply(message, "❌ Invalid or unsafe filename.")
            return
        user_folder = get_user_folder(user_id)
        fpath = os.path.join(user_folder, fname)
        if not os.path.exists(fpath) or not os.path.isfile(fpath):
            safe_reply(message, f"❌ File `{fname}` not found.", parse_mode='Markdown')
            return
        try:
            size = os.path.getsize(fpath)
            if size > 200 * 1024:
                safe_reply(message, f"❌ File too large ({size/1024:.1f} KB > 200 KB).", parse_mode='Markdown')
                return
            with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(3500)
            safe_reply(message, f"📄 *{fname}:*\n{_terminal_output_block(content)}", parse_mode='Markdown')
        except Exception as e:
            safe_reply(message, f"❌ cat error: `{e}`", parse_mode='Markdown')
        return

    if lower.startswith('pip ') or lower.startswith('pip3 '):
        cmd_args = raw.split()[1:]
        if not cmd_args:
            safe_reply(message, "❌ Usage: `pip install <package>`", parse_mode='Markdown')
            return
        allowed = {'install', 'uninstall', 'list', 'freeze', 'show'}
        if cmd_args[0].lower() not in allowed:
            safe_reply(message, f"❌ pip action `{cmd_args[0]}` not allowed.\nUse: `{', '.join(sorted(allowed))}`", parse_mode='Markdown')
            return
        _run_terminal_pip(message, cmd_args, user_id)
        return

    if lower.startswith('npm '):
        cmd_args = raw.split()[1:]
        if not cmd_args:
            safe_reply(message, "❌ Usage: `npm install <package>`", parse_mode='Markdown')
            return
        allowed = {'install', 'i', 'list', 'ls'}
        if cmd_args[0].lower() not in allowed:
            safe_reply(message, f"❌ npm action `{cmd_args[0]}` not allowed. Use: `install` or `list`.", parse_mode='Markdown')
            return
        _run_terminal_npm(message, cmd_args, user_id)
        return

    if lower.startswith('deps '):
        fname = raw[5:].strip().strip('"\'')
        if not fname:
            safe_reply(message, "❌ Usage: `deps <file.py|file.js>`", parse_mode='Markdown')
            return
        _run_terminal_deps(message, fname, user_id)
        return

    safe_reply(message, f"❓ Unknown command: `{raw[:40]}`\n\nType `help` to list commands.", parse_mode='Markdown')


# --- Terminal commands & callbacks ---
@bot.message_handler(commands=['terminal'])
def command_terminal(message):
    if not check_joined(message.from_user.id, message.chat.id): return
    if message.from_user.id in banned_users:
        safe_reply(message, "❌ You are banned.")
        return
    open_terminal_for_user(message.chat.id, message.from_user.id)


@bot.message_handler(commands=['exit'])
def command_terminal_exit(message):
    if not terminal_sessions.get(message.from_user.id):
        safe_reply(message, "❌ No active terminal session.")
        return
    terminal_sessions.pop(message.from_user.id, None)
    safe_reply(message, "🔒 Terminal closed.", parse_mode='Markdown')


def _logic_open_terminal(message):
    if message.from_user.id in banned_users:
        safe_reply(message, "❌ You are banned.")
        return
    open_terminal_for_user(message.chat.id, message.from_user.id)


def term_open_callback(call):
    bot.answer_callback_query(call.id, "🖥️ Opening terminal...")
    open_terminal_for_user(call.message.chat.id, call.from_user.id)


def term_close_callback(call):
    terminal_sessions.pop(call.from_user.id, None)
    bot.answer_callback_query(call.id, "🔒 Terminal closed.")
    try:
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
    except Exception:
        pass
    bot.send_message(call.message.chat.id, "🔒 *Terminal session closed.*", parse_mode='Markdown')


def term_help_callback(call):
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, TERMINAL_HELP, parse_mode='Markdown')


def term_ls_callback(call):
    bot.answer_callback_query(call.id)
    user_id = call.from_user.id
    user_folder = get_user_folder(user_id)
    entries = []
    for item in sorted(os.listdir(user_folder)):
        full = os.path.join(user_folder, item)
        if os.path.isdir(full):
            entries.append(f"📁 {item}/")
        else:
            size = os.path.getsize(full)
            size_str = f"{size}B" if size < 1024 else f"{size/1024:.1f}KB" if size < 1024*1024 else f"{size/1024/1024:.1f}MB"
            entries.append(f"📄 {item} ({size_str})")
    if not entries:
        bot.send_message(call.message.chat.id, "📂 *(empty workspace)*", parse_mode='Markdown')
    else:
        bot.send_message(call.message.chat.id, f"📂 *Workspace files:*\n{_terminal_output_block(chr(10).join(entries))}", parse_mode='Markdown')


# Register text-button → logic (safe here because _logic_open_terminal is now defined)
BUTTON_TEXT_TO_LOGIC["🖥️ Terminal"] = _logic_open_terminal


# Message handler for terminal input (defined AFTER button handler so menu buttons win)
@bot.message_handler(func=lambda m: (
    terminal_sessions.get(m.from_user.id)
    and m.content_type == 'text'
    and m.text
    and not m.text.startswith('/')
    and m.text not in BUTTON_TEXT_TO_LOGIC
))
def terminal_message_handler(message):
    if not check_joined(message.from_user.id, message.chat.id): return
    process_terminal_command(message)
# =========================================================================
# End of small terminal block
# =========================================================================


if __name__ == '__main__':
    keep_alive()
    # Start background RAM/CPU cap & Auto-Restart watchdog thread
    threading.Thread(target=resource_watchdog_loop, daemon=True).start()
    logger.info("Bot starting on Windows...")
    auto_start_saved_scripts()

    # Infinity polling with connection retry
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
