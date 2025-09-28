#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
悬浮窗口模块
负责创建和管理悬浮输入框，显示用户按键输入
"""

import tkinter as tk
from tkinter import ttk
import threading

class OverlayWindow:
    """悬浮窗口类"""
    
    def __init__(self):
        """初始化悬浮窗口"""
        self.root = None
        self.text_var = None
        self.window_visible = False
        self.window_thread = None
        self.window_lock = threading.Lock()
        
    def create_overlay_window(self):
        """创建悬浮窗口"""
        with self.window_lock:
            if self.root is not None:
                return
                
            # 创建顶层窗口
            self.root = tk.Tk()
            self.root.title("按键输入显示")
            self.root.geometry("300x60+100+100")
            self.root.overrideredirect(True)  # 无边框窗口
            self.root.attributes('-topmost', True)  # 置顶显示
            self.root.attributes('-alpha', 0.8)  # 半透明效果
            
            # 设置窗口背景色
            self.root.configure(bg='#2c3e50')
            
            # 创建文本标签
            self.text_var = tk.StringVar(value="")
            label = tk.Label(
                self.root,
                textvariable=self.text_var,
                bg='#2c3e50',
                fg='white',
                font=('Arial', 12),
                padx=10,
                pady=10
            )
            label.pack(fill=tk.BOTH, expand=True)
            
            # 隐藏窗口直到有内容显示
            self.root.withdraw()
            self.window_visible = False
            
            # 绑定鼠标事件用于移动窗口
            self.root.bind('<Button-1>', self.start_move)
            self.root.bind('<B1-Motion>', self.do_move)
            
            # 启动窗口事件循环
            self.root.mainloop()
    
    def start_move(self, event):
        """开始移动窗口"""
        self.x = event.x
        self.y = event.y
    
    def do_move(self, event):
        """移动窗口"""
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.root.winfo_x() + deltax
        y = self.root.winfo_y() + deltay
        self.root.geometry(f"+{x}+{y}")
    
    def start_window_thread(self):
        """启动悬浮窗口线程"""
        if self.window_thread is None or not self.window_thread.is_alive():
            self.window_thread = threading.Thread(target=self.create_overlay_window, daemon=True)
            self.window_thread.start()
    
    def update_text(self, text):
        """更新显示文本"""
        if self.root is None:
            return
            
        # 在主线程中更新UI
        self.root.after(0, self._update_text_ui, text)
    
    def _update_text_ui(self, text):
        """在UI线程中更新文本"""
        if self.text_var:
            self.text_var.set(text)
            
            # 根据文本内容决定是否显示窗口
            if text and not self.window_visible:
                self.root.deiconify()  # 显示窗口
                self.window_visible = True
            elif not text and self.window_visible:
                self.root.withdraw()  # 隐藏窗口
                self.window_visible = False
    
    def hide_window(self):
        """隐藏悬浮窗口"""
        if self.root and self.window_visible:
            self.root.withdraw()
            self.window_visible = False
    
    def show_window(self):
        """显示悬浮窗口"""
        if self.root and not self.window_visible:
            self.root.deiconify()
            self.window_visible = True
    
    def destroy_window(self):
        """销毁悬浮窗口"""
        if self.root:
            try:
                self.root.quit()
                self.root.destroy()
            except:
                pass
            finally:
                self.root = None
                self.window_visible = False