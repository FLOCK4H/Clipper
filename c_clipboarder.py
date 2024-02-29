# c_clipboarder.py
import ctypes
import ctypes.wintypes as w
import time
import threading
import os
from uuid import uuid4
import json
from json import JSONDecodeError
user32 = ctypes.WinDLL('user32')
kernel32 = ctypes.WinDLL('kernel32')

user32.OpenClipboard.argtypes = [w.HWND]
user32.OpenClipboard.restype = w.BOOL
user32.EmptyClipboard.argtypes = []
user32.EmptyClipboard.restype = w.BOOL
user32.SetClipboardData.argtypes = [w.UINT, w.HANDLE]
user32.SetClipboardData.restype = w.HANDLE
user32.GetClipboardData.argtypes = [w.UINT]
user32.GetClipboardData.restype = w.HANDLE
user32.CloseClipboard.argtypes = []
user32.CloseClipboard.restype = w.BOOL
kernel32.GlobalAlloc.argtypes = [w.UINT, ctypes.c_size_t]
kernel32.GlobalAlloc.restype = w.HGLOBAL
kernel32.GlobalLock.argtypes = [w.HGLOBAL]
kernel32.GlobalLock.restype = w.LPVOID
kernel32.GlobalUnlock.argtypes = [w.HGLOBAL]
kernel32.GlobalUnlock.restype = w.BOOL

CF_UNICODETEXT = 13
GMEM_MOVEABLE = 0x0002

def get():
    text = None
    if user32.OpenClipboard(None):
        handle = user32.GetClipboardData(CF_UNICODETEXT)
        if handle:
            pointer = kernel32.GlobalLock(handle)
            if pointer:
                text = ctypes.wstring_at(pointer)
                kernel32.GlobalUnlock(handle)
        user32.CloseClipboard()
    return text

def clear():
    if user32.OpenClipboard(None):
        user32.EmptyClipboard()
        user32.CloseClipboard()

def append(text):
    current_data = get()
    if current_data is not None:
        text = current_data + str(text)
    else:
        text = str(text)

    if user32.OpenClipboard(None):
        user32.EmptyClipboard()
        h_global_mem = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(text) * 2 + 2)
        p_global_mem = kernel32.GlobalLock(h_global_mem)
        ctypes.memmove(p_global_mem, ctypes.create_unicode_buffer(text), len(text) * 2 + 2)
        kernel32.GlobalUnlock(h_global_mem)
        user32.SetClipboardData(CF_UNICODETEXT, h_global_mem)
        user32.CloseClipboard()

def set_text(text=""):
    clear()
    append(text)

def generate_unique_id():
    return str(uuid4()).replace('-', '')[:16]

class Collector:
    def __init__(self, filepath, **kwargs):
        self.filepath = filepath
        self.print_it = kwargs.get('print_it', False)
        self.last_clipboard_content = None
        self.seen_content = set()
        try:
            if os.path.exists(self.filepath):
                with open(self.filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.seen_content.update(entry['clipboard'] for entry in data)
        except JSONDecodeError as e:
            with open(self.filepath, 'w', encoding='utf-8') as f:
                f.write("[]")

    def check_clipboard(self):
        current_content = get()
        if current_content != self.last_clipboard_content and current_content not in self.seen_content:
            self.last_clipboard_content = current_content
            return True
        return False

    def clear(self):
        with open(self.filepath, 'w', encoding='utf-8') as f:
            f.write('[]')

    def write_to_file(self):
        try:
            if self.last_clipboard_content:
                unique_id = str(uuid4()).replace('-', '')[:16]
                self.seen_content.add(self.last_clipboard_content)
                new_entry = {
                    "id": unique_id,
                    "clipboard": self.last_clipboard_content
                }
                if os.path.exists(self.filepath):
                    with open(self.filepath, 'r+', encoding='utf-8') as f:
                        data = json.load(f)
                        data.append(new_entry)
                        f.seek(0)
                        json.dump(data, f, indent=4)
                else:
                    with open(self.filepath, 'w', encoding='utf-8') as f:
                        json.dump([new_entry], f, indent=4)

                if self.print_it:
                    print(f"Clipboard content saved with ID {unique_id}: {self.last_clipboard_content}")
        except Exception as e:
            print(str(e))
    def start_listening(self, interval=1):
        while True:
            if self.check_clipboard():
                self.write_to_file()
            time.sleep(interval)
