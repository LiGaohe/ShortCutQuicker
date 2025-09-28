#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
UI管理模块
负责图形界面和系统托盘
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import sys
import os

# 添加src目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__)))

from overlay_window import OverlayWindow

# 导入鼠标控制和剪贴板操作库
from pynput import mouse
import pyperclip


class UIManager:
    """UI管理器"""
    
    def __init__(self, config_manager, keyboard_manager):
        """初始化UI管理器"""
        self.config_manager = config_manager
        self.keyboard_manager = keyboard_manager
        self.root = None
        self.mapping_window = None
        # 保存对状态标签和按钮的引用，以便更新
        self.status_label = None
        self.toggle_button = None
        self.status_var = None
        
        # 初始化悬浮窗口
        self.overlay_window = OverlayWindow()
        self.overlay_window.start_window_thread()
        
        # 设置键盘管理器的状态回调
        self.keyboard_manager.set_status_callback(self.update_ui_status)
        # 设置键盘管理器的悬浮窗口回调
        self.keyboard_manager.set_overlay_callback(self.update_overlay_text)
    
    def run(self):
        """运行UI"""
        self.create_main_window()
        
        # 注册退出时清理函数
        def on_closing():
            # 销毁悬浮窗口
            if self.overlay_window:
                self.overlay_window.destroy_window()
            # 关闭主窗口
            self.root.quit()
            self.root.destroy()
        
        self.root.protocol("WM_DELETE_WINDOW", on_closing)
        self.root.mainloop()
    
    def create_main_window(self):
        """创建主窗口"""
        self.root = tk.Tk()
        self.root.title("Quicker-like 软件")
        self.root.geometry("600x400")
        self.root.resizable(True, True)
        
        # 创建菜单栏
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="退出", command=self.root.quit)
        
        # 设置菜单
        settings_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="设置", menu=settings_menu)
        settings_menu.add_command(label="按键映射", command=self.open_mapping_window)
        
        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="关于", command=self.show_about)
        
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # 标题
        title_label = ttk.Label(main_frame, text="Quicker-like 软件", font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, pady=(0, 20))
        
        # 状态框架
        status_frame = ttk.LabelFrame(main_frame, text="状态", padding="10")
        status_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 20))
        status_frame.columnconfigure(1, weight=1)
        
        # 监听状态
        ttk.Label(status_frame, text="键盘监听:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.status_var = tk.StringVar(value="运行中" if self.keyboard_manager.is_active() else "已停止")
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var, foreground="green" if self.keyboard_manager.is_active() else "red")
        self.status_label.grid(row=0, column=1, sticky=tk.W)
        
        # 控制按钮框架
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=2, column=0, pady=(0, 20))
        
        # 启动/停止按钮
        self.toggle_button = ttk.Button(
            control_frame, 
            text="停止监听" if self.keyboard_manager.is_active() else "开始监听",
            command=self.toggle_listening
        )
        self.toggle_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # 配置按钮
        config_button = ttk.Button(control_frame, text="配置映射", command=self.open_mapping_window)
        config_button.pack(side=tk.LEFT)
        
        # 映射列表框架
        mapping_frame = ttk.LabelFrame(main_frame, text="当前按键映射", padding="10")
        mapping_frame.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 20))
        mapping_frame.columnconfigure(0, weight=1)
        mapping_frame.rowconfigure(0, weight=1)
        
        # 创建Treeview显示映射
        columns = ('按键序列', '快捷键')
        self.mapping_tree = ttk.Treeview(mapping_frame, columns=columns, show='headings', height=8)
        self.mapping_tree.heading('按键序列', text='按键序列')
        self.mapping_tree.heading('快捷键', text='快捷键')
        self.mapping_tree.column('按键序列', width=150)
        self.mapping_tree.column('快捷键', width=150)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(mapping_frame, orient=tk.VERTICAL, command=self.mapping_tree.yview)
        self.mapping_tree.configure(yscroll=scrollbar.set)
        
        self.mapping_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # 加载映射数据
        self.load_mapping_data()
        
        # 底部信息
        info_frame = ttk.Frame(main_frame)
        info_frame.grid(row=4, column=0, sticky=(tk.W, tk.E))
        
        ttk.Label(info_frame, text="提示: 按下自定义按键序列可触发对应快捷键", foreground="gray").pack()
    
    def load_mapping_data(self):
        """加载并显示按键映射数据"""
        # 清空现有数据
        for item in self.mapping_tree.get_children():
            self.mapping_tree.delete(item)
        
        # 获取映射数据
        mappings = self.config_manager.get_mappings()
        
        # 添加到Treeview
        for key, hotkey in mappings.items():
            # 特殊处理GET_MOUSE_POSITION映射，显示为"获取鼠标位置"
            display_hotkey = "获取鼠标位置" if hotkey == "GET_MOUSE_POSITION" else hotkey
            self.mapping_tree.insert('', tk.END, values=(key, display_hotkey))
    
    def toggle_listening(self):
        """切换键盘监听状态"""
        if self.keyboard_manager.is_active():
            self.keyboard_manager.stop_listening()
            self.update_ui_status(False)
        else:
            self.keyboard_manager.start_listening()
            self.update_ui_status(True)
    
    def update_ui_status(self, is_active):
        """更新UI状态显示"""
        if is_active:
            self.status_var.set("运行中")
            if self.status_label:
                self.status_label.config(foreground="green")
            if self.toggle_button:
                self.toggle_button.config(text="停止监听")
        else:
            self.status_var.set("已停止")
            if self.status_label:
                self.status_label.config(foreground="red")
            if self.toggle_button:
                self.toggle_button.config(text="开始监听")
    
    def open_mapping_window(self):
        """打开按键映射配置窗口"""
        if self.mapping_window and self.mapping_window.winfo_exists():
            self.mapping_window.lift()
            return
        
        self.mapping_window = tk.Toplevel(self.root)
        self.mapping_window.title("按键映射配置")
        self.mapping_window.geometry("600x500")
        self.mapping_window.resizable(True, True)
        
        # 居中显示
        self.mapping_window.transient(self.root)
        self.mapping_window.grab_set()
        
        # 创建框架
        main_frame = ttk.Frame(self.mapping_window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建Notebook用于分隔按键映射和鼠标映射
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # 按键映射标签页
        key_frame = ttk.Frame(notebook)
        notebook.add(key_frame, text="按键映射")
        
        # 鼠标映射标签页
        mouse_frame = ttk.Frame(notebook)
        notebook.add(mouse_frame, text="鼠标点击映射")
        
        # ========== 按键映射部分 ==========
        # 输入框架
        key_input_frame = ttk.LabelFrame(key_frame, text="添加新按键映射", padding="10")
        key_input_frame.pack(fill=tk.X, pady=(0, 20))
        
        # 按键序列输入
        ttk.Label(key_input_frame, text="按键序列:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.key_sequence_var = tk.StringVar()
        key_sequence_entry = ttk.Entry(key_input_frame, textvariable=self.key_sequence_var, width=20)
        key_sequence_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        key_sequence_entry.bind('<FocusIn>', lambda e: self.start_capture())
        
        # 快捷键输入
        ttk.Label(key_input_frame, text="快捷键:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.hotkey_var = tk.StringVar()
        hotkey_entry = ttk.Entry(key_input_frame, textvariable=self.hotkey_var, width=20)
        hotkey_entry.grid(row=0, column=3, sticky=(tk.W, tk.E))
        hotkey_entry.bind('<FocusIn>', lambda e: self.start_hotkey_capture())
        
        # 添加按钮
        add_key_button = ttk.Button(key_input_frame, text="添加", command=self.add_mapping)
        add_key_button.grid(row=0, column=4, padx=(10, 0))
        
        # 配置列权重
        key_input_frame.columnconfigure(1, weight=1)
        key_input_frame.columnconfigure(3, weight=1)
        
        # 提示信息
        key_hint_label = ttk.Label(
            key_input_frame, 
            text="点击输入框后按下相应按键进行录制", 
            foreground="blue",
            font=("Arial", 9)
        )
        key_hint_label.grid(row=1, column=0, columnspan=5, sticky=tk.W, pady=(5, 0))
        
        # 按键映射列表框架
        key_list_frame = ttk.LabelFrame(key_frame, text="现有按键映射", padding="10")
        key_list_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建Treeview
        key_columns = ('按键序列', '快捷键')
        self.key_mapping_tree = ttk.Treeview(key_list_frame, columns=key_columns, show='headings', height=8)
        self.key_mapping_tree.heading('按键序列', text='按键序列')
        self.key_mapping_tree.heading('快捷键', text='快捷键')
        self.key_mapping_tree.column('按键序列', width=150)
        self.key_mapping_tree.column('快捷键', width=150)
        
        # 添加滚动条
        key_scrollbar = ttk.Scrollbar(key_list_frame, orient=tk.VERTICAL, command=self.key_mapping_tree.yview)
        self.key_mapping_tree.configure(yscroll=key_scrollbar.set)
        
        self.key_mapping_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        key_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 按键映射按钮框架
        key_button_frame = ttk.Frame(key_list_frame)
        key_button_frame.pack(fill=tk.X, pady=(10, 0))
        
        # 删除按钮
        delete_key_button = ttk.Button(key_button_frame, text="删除选中", command=self.delete_key_mapping)
        delete_key_button.pack(side=tk.LEFT)
        
        # 刷新按钮
        refresh_key_button = ttk.Button(key_button_frame, text="刷新", command=self.load_key_mapping_data)
        refresh_key_button.pack(side=tk.RIGHT)
        
        # ========== 鼠标映射部分 ==========
        # 输入框架
        mouse_input_frame = ttk.LabelFrame(mouse_frame, text="添加新鼠标点击映射", padding="10")
        mouse_input_frame.pack(fill=tk.X, pady=(0, 20))
        
        # 按键序列输入
        ttk.Label(mouse_input_frame, text="按键序列:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.mouse_key_sequence_var = tk.StringVar()
        mouse_key_sequence_entry = ttk.Entry(mouse_input_frame, textvariable=self.mouse_key_sequence_var, width=20)
        mouse_key_sequence_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        mouse_key_sequence_entry.bind('<FocusIn>', lambda e: self.start_capture_mouse())
        
        # 鼠标位置输入
        ttk.Label(mouse_input_frame, text="鼠标位置 (X,Y):").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.mouse_position_var = tk.StringVar()
        mouse_position_entry = ttk.Entry(mouse_input_frame, textvariable=self.mouse_position_var, width=20)
        mouse_position_entry.grid(row=0, column=3, sticky=(tk.W, tk.E))
        
        # 添加按钮
        add_mouse_button = ttk.Button(mouse_input_frame, text="添加", command=self.add_mouse_mapping)
        add_mouse_button.grid(row=0, column=4, padx=(10, 0))
        
        # 配置列权重
        mouse_input_frame.columnconfigure(1, weight=1)
        mouse_input_frame.columnconfigure(3, weight=1)
        
        # 提示信息
        mouse_hint_label = ttk.Label(
            mouse_input_frame, 
            text="点击输入框后按下相应按键进行录制，鼠标位置格式: X,Y (例如: 100,200)", 
            foreground="blue",
            font=("Arial", 9)
        )
        mouse_hint_label.grid(row=1, column=0, columnspan=5, sticky=tk.W, pady=(5, 0))
        
        # 鼠标映射列表框架
        mouse_list_frame = ttk.LabelFrame(mouse_frame, text="现有鼠标点击映射", padding="10")
        mouse_list_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建Treeview
        mouse_columns = ('按键序列', '鼠标位置')
        self.mouse_mapping_tree = ttk.Treeview(mouse_list_frame, columns=mouse_columns, show='headings', height=8)
        self.mouse_mapping_tree.heading('按键序列', text='按键序列')
        self.mouse_mapping_tree.heading('鼠标位置', text='鼠标位置')
        self.mouse_mapping_tree.column('按键序列', width=150)
        self.mouse_mapping_tree.column('鼠标位置', width=150)
        
        # 添加滚动条
        mouse_scrollbar = ttk.Scrollbar(mouse_list_frame, orient=tk.VERTICAL, command=self.mouse_mapping_tree.yview)
        self.mouse_mapping_tree.configure(yscroll=mouse_scrollbar.set)
        
        self.mouse_mapping_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        mouse_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 鼠标映射按钮框架
        mouse_button_frame = ttk.Frame(mouse_list_frame)
        mouse_button_frame.pack(fill=tk.X, pady=(10, 0))
        
        # 删除按钮
        delete_mouse_button = ttk.Button(mouse_button_frame, text="删除选中", command=self.delete_mouse_mapping)
        delete_mouse_button.pack(side=tk.LEFT)
        
        # 刷新按钮
        refresh_mouse_button = ttk.Button(mouse_button_frame, text="刷新", command=self.load_mouse_mapping_data)
        refresh_mouse_button.pack(side=tk.RIGHT)
        
        # 加载数据
        self.load_key_mapping_data()
        self.load_mouse_mapping_data()
        
        # 双击编辑
        self.key_mapping_tree.bind('<Double-1>', self.edit_key_mapping)
        self.mouse_mapping_tree.bind('<Double-1>', self.edit_mouse_mapping)
    
    def load_key_mapping_data(self):
        """加载按键映射数据到表格"""
        # 清空现有数据
        for item in self.key_mapping_tree.get_children():
            self.key_mapping_tree.delete(item)
        
        # 获取映射数据
        mappings = self.config_manager.get_mappings()
        
        # 添加数据到表格
        for key_seq, hotkey in mappings.items():
            # 特殊处理GET_MOUSE_POSITION映射，显示为"获取鼠标位置"
            display_hotkey = "获取鼠标位置" if hotkey == "GET_MOUSE_POSITION" else hotkey
            self.key_mapping_tree.insert('', tk.END, values=(key_seq, display_hotkey))
    
    def load_mouse_mapping_data(self):
        """加载鼠标映射数据到表格"""
        # 清空现有数据
        for item in self.mouse_mapping_tree.get_children():
            self.mouse_mapping_tree.delete(item)
        
        # 获取映射数据
        mouse_mappings = self.config_manager.get_mouse_mappings()
        
        # 添加数据到表格
        for key_seq, position in mouse_mappings.items():
            self.mouse_mapping_tree.insert('', tk.END, values=(key_seq, position))
    
    def start_capture(self):
        """开始捕获按键序列"""
        self.current_capture = "mapping"
        self.key_sequence_var.set("请按键...")
    
    def start_hotkey_capture(self):
        """开始捕获快捷键"""
        self.current_capture = "hotkey"
        self.hotkey_var.set("请按键...")
    
    def add_mapping(self):
        """添加新的按键映射"""
        key_sequence = self.key_sequence_var.get().strip()
        hotkey = self.hotkey_var.get().strip()
        
        if not key_sequence or not hotkey:
            messagebox.showwarning("输入错误", "请填写完整的按键序列和快捷键")
            return
        
        # 添加映射
        self.config_manager.add_mapping(key_sequence, hotkey)
        
        # 清空输入框
        self.key_sequence_var.set("")
        self.hotkey_var.set("")
        
        # 刷新显示
        self.load_key_mapping_data()
        
        messagebox.showinfo("成功", "按键映射添加成功")
    
    def start_capture_mouse(self):
        """开始捕获鼠标相关的按键序列"""
        self.current_capture = "mouse"
        self.mouse_key_sequence_var.set("请按键...")
    
    def add_mouse_mapping(self):
        """添加新的鼠标点击映射"""
        key_sequence = self.mouse_key_sequence_var.get().strip()
        position = self.mouse_position_var.get().strip()
        
        if not key_sequence or not position:
            messagebox.showwarning("输入错误", "请填写完整的按键序列和鼠标位置")
            return
        
        # 验证鼠标位置格式
        try:
            x, y = map(int, position.split(','))
        except ValueError:
            messagebox.showerror("格式错误", "鼠标位置格式不正确，请使用 X,Y 格式（例如: 100,200）")
            return
        
        # 添加映射
        self.config_manager.add_mouse_mapping(key_sequence, position)
        
        # 清空输入框
        self.mouse_key_sequence_var.set("")
        self.mouse_position_var.set("")
        
        # 刷新显示
        self.load_mouse_mapping_data()
        
        messagebox.showinfo("成功", "鼠标点击映射添加成功")
    
    def delete_key_mapping(self):
        """删除选中的按键映射"""
        selected = self.key_mapping_tree.selection()
        if not selected:
            messagebox.showwarning("选择错误", "请先选择要删除的按键映射")
            return
        
        # 获取选中项的值
        item = self.key_mapping_tree.item(selected[0])
        key_sequence = item['values'][0]
        
        # 删除映射
        self.config_manager.remove_mapping(key_sequence)
        
        # 刷新显示
        self.load_key_mapping_data()
        
        messagebox.showinfo("成功", "按键映射删除成功")
    
    def delete_mouse_mapping(self):
        """删除选中的鼠标映射"""
        selected = self.mouse_mapping_tree.selection()
        if not selected:
            messagebox.showwarning("选择错误", "请先选择要删除的鼠标点击映射")
            return
        
        # 获取选中项的值
        item = self.mouse_mapping_tree.item(selected[0])
        key_sequence = item['values'][0]
        
        # 删除映射
        self.config_manager.remove_mouse_mapping(key_sequence)
        
        # 刷新显示
        self.load_mouse_mapping_data()
        
        messagebox.showinfo("成功", "鼠标点击映射删除成功")
    
    def edit_key_mapping(self, event):
        """编辑选中的按键映射"""
        selected = self.key_mapping_tree.selection()
        if not selected:
            return
        
        # 获取选中项的值
        item = self.key_mapping_tree.item(selected[0])
        key_sequence = item['values'][0]
        hotkey = item['values'][1]
        
        # 特殊处理GET_MOUSE_POSITION映射，显示原始值
        display_hotkey = "GET_MOUSE_POSITION" if hotkey == "获取鼠标位置" else hotkey
        
        # 填充到输入框
        self.key_sequence_var.set(key_sequence)
        self.hotkey_var.set(display_hotkey)
    
    def edit_mouse_mapping(self, event):
        """编辑选中的鼠标映射"""
        selected = self.mouse_mapping_tree.selection()
        if not selected:
            return
        
        # 获取选中项的值
        item = self.mouse_mapping_tree.item(selected[0])
        key_sequence = item['values'][0]
        position = item['values'][1]
        
        # 填充到输入框
        self.mouse_key_sequence_var.set(key_sequence)
        self.mouse_position_var.set(position)
    
    def show_about(self):
        """显示关于对话框"""
        messagebox.showinfo(
            "关于", 
            "Quicker-like 软件\n\n"
            "一个类似于Quicker的快捷键工具\n"
            "支持自定义按键映射到快捷键功能\n"
            "版本: 1.0.0"
        )
    
    def update_overlay_text(self, text):
        """更新悬浮窗口文本"""
        if self.overlay_window:
            # 限制显示长度，避免窗口过大
            display_text = text[-50:] if len(text) > 50 else text
            self.overlay_window.update_text(display_text)