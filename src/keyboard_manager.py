#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
键盘管理模块
负责监听键盘事件和执行快捷键
"""

import threading
from pynput import keyboard, mouse
import time
import pyperclip

class KeyboardManager:
    """键盘管理器"""
    
    def __init__(self, config_manager):
        """初始化键盘管理器"""
        self.config_manager = config_manager
        self.listener = None
        self.active = False
        self.current_keys = set()
        self.key_buffer = []
        self.buffer_timeout = 1.0  # 缓冲区超时时间(秒)
        self.last_key_time = 0
        # 实时按键记录
        self.current_input = ""
        # 定义启动/停止监听的组合键 (Ctrl+Shift+F12)
        self.toggle_key_combination = {keyboard.Key.ctrl_l, keyboard.Key.shift_l, keyboard.Key.f12}
        # 状态变化回调函数
        self.status_callback = None
        # 悬浮窗口回调函数
        self.overlay_callback = None
        # 用于在非活动状态下监听启动组合键的监听器
        self.toggle_listener = None
        # 鼠标控制器
        self.mouse_controller = mouse.Controller()
        # 在初始化时就启动用于监听启动组合键的监听器
        self._start_toggle_listener()
    
    def _start_toggle_listener(self):
        """启动专门用于监听启动组合键的监听器"""
        if not self.active and not self.toggle_listener:
            self.toggle_listener = keyboard.Listener(
                on_press=self._toggle_on_press,
                on_release=self.on_release
            )
            self.toggle_listener.start()
    
    def start_listening(self):
        """开始监听键盘事件"""
        self.active = True
        # 停止专门用于监听启动组合键的监听器
        if self.toggle_listener:
            self.toggle_listener.stop()
            self.toggle_listener = None
            
        self.listener = keyboard.Listener(
            on_press=self.on_press,
            on_release=self.on_release
        )
        self.listener.start()
        print("键盘监听已启动")
    
    def stop_listening(self):
        """停止监听键盘事件"""
        self.active = False
        if self.listener:
            self.listener.stop()
            self.listener = None
            
        # 启动一个专门用于监听启动组合键的监听器
        self.toggle_listener = keyboard.Listener(
            on_press=self._toggle_on_press,
            on_release=self.on_release
        )
        self.toggle_listener.start()
        print("键盘监听已停止")
    
    def toggle_listening(self):
        """切换键盘监听状态"""
        if self.active:
            self.stop_listening()
            print("键盘监听已停止 - 按 Ctrl+Shift+F12 再次启动")
            self._notify_status_change(False)
        else:
            # 清空按键集合以避免重复触发
            self.current_keys.clear()
            self.start_listening()
            print("键盘监听已启动 - 按 Ctrl+Shift+F12 停止监听")
            self._notify_status_change(True)
    
    def on_press(self, key):
        """按键按下事件处理"""
        if not self.active:
            # 即使在非活动状态下也要检查组合键
            self.current_keys.add(key)
            
            # 检查是否按下了启动/停止监听的组合键
            if self.current_keys.issuperset(self.toggle_key_combination):
                self.toggle_listening()
                # 清空按键集合以避免重复触发
                self.current_keys.clear()
                return False  # 抑制该按键事件
            
            return True
            
        # 记录当前按下的键
        self.current_keys.add(key)
        
        # 检查是否按下了启动/停止监听的组合键
        if self.current_keys.issuperset(self.toggle_key_combination):
            self.toggle_listening()
            # 清空按键集合以避免重复触发
            self.current_keys.clear()
            return False  # 抑制该按键事件
        
        # 将按键转换为字符串形式并更新实时输入显示
        try:
            if hasattr(key, 'char') and key.char:
                key_str = key.char
                # 更新实时输入
                self.current_input += key_str
            else:
                key_str = str(key).replace('Key.', '')
                # 对于特殊键，添加方括号标记
                self.current_input += f"[{key_str}]"
            
            # 更新悬浮窗口显示
            self._notify_overlay_update(self.current_input)
            
            # 添加到缓冲区
            current_time = time.time()
            if current_time - self.last_key_time > self.buffer_timeout:
                # 超时清空缓冲区
                self.key_buffer = []
            
            self.key_buffer.append(key_str.lower())
            self.last_key_time = current_time
            
            # 检查是否匹配自定义映射
            buffer_str = ''.join(self.key_buffer)
            self.check_custom_mapping(buffer_str)
            
        except AttributeError:
            pass
        
        # 返回False会抑制该按键事件传播到其他应用程序
        # 但我们只在匹配到自定义映射时才抑制
        return True
    
    def on_release(self, key):
        """按键释放事件处理"""
        try:
            self.current_keys.discard(key)
            
            # 检查是否所有键都已释放，如果是则在超时后清空输入显示
            if not self.current_keys:
                # 启动一个定时器，在超时后清空输入显示
                threading.Timer(self.buffer_timeout, self._clear_input_display).start()
        except KeyError:
            pass
    
    def _toggle_on_press(self, key):
        """在非活动状态下监听启动组合键的专用方法"""
        # 记录当前按下的键
        self.current_keys.add(key)
        
        # 检查是否按下了启动/停止监听的组合键
        if self.current_keys.issuperset(self.toggle_key_combination):
            self.toggle_listening()
            # 清空按键集合以避免重复触发
            self.current_keys.clear()
            return False  # 抑制该按键事件
        
        return True
    
    def check_custom_mapping(self, key_str):
        """检查自定义按键映射"""
        # 获取按键映射
        mappings = self.config_manager.get_mappings()
        
        # 检查是否匹配任何按键映射
        if key_str in mappings:
            hotkey = mappings[key_str]
            # 检查是否是获取鼠标位置的特殊指令
            if hotkey == "GET_MOUSE_POSITION":
                # 在新线程中获取鼠标位置，避免阻塞键盘监听
                threading.Thread(target=self.get_mouse_position, daemon=True).start()
                return True
            else:
                # 在新线程中执行快捷键，避免阻塞键盘监听
                threading.Thread(target=self.execute_hotkey, args=(hotkey,), daemon=True).start()
                return True
        
        # 获取鼠标点击映射
        mouse_mappings = self.config_manager.get_mouse_mappings()
        
        # 检查是否匹配任何鼠标点击映射
        if key_str in mouse_mappings:
            position = mouse_mappings[key_str]
            # 在新线程中执行鼠标点击，避免阻塞键盘监听
            threading.Thread(target=self.execute_mouse_click, args=(position,), daemon=True).start()
            return True
        
        return False
    
    def get_mouse_position(self):
        """获取鼠标位置并复制到剪贴板"""
        try:
            # 获取当前鼠标位置
            x, y = self.mouse_controller.position
            
            # 格式化位置字符串
            position_str = f"{int(x)},{int(y)}"
            
            # 复制到剪贴板
            pyperclip.copy(position_str)
            
            print(f"鼠标位置 {position_str} 已复制到剪贴板")
        except Exception as e:
            print(f"获取鼠标位置失败: {e}")
    
    def execute_hotkey(self, hotkey):
        """执行快捷键"""
        try:
            print(f"执行快捷键: {hotkey}")
            
            # 解析快捷键字符串
            keys = hotkey.split('+')
            key_combination = []
            
            # 控制键
            ctrl = False
            shift = False
            alt = False
            
            for key in keys:
                k = key.strip().lower()
                if k == 'ctrl':
                    ctrl = True
                elif k == 'shift':
                    shift = True
                elif k == 'alt':
                    alt = True
                else:
                    # 普通按键
                    key_combination.append(k)
            
            # 使用pynput执行快捷键
            controller = keyboard.Controller()
            # 按下控制键
            if ctrl:
                controller.press(keyboard.Key.ctrl)
            if shift:
                controller.press(keyboard.Key.shift)
            if alt:
                controller.press(keyboard.Key.alt)
            
            # 按下普通键
            for key_char in key_combination:
                if len(key_char) == 1:
                    # 字符键
                    controller.press(key_char)
                    controller.release(key_char)
                else:
                    # 特殊键
                    special_keys = {
                        'enter': keyboard.Key.enter,
                        'space': keyboard.Key.space,
                        'tab': keyboard.Key.tab,
                        'esc': keyboard.Key.esc,
                        'backspace': keyboard.Key.backspace,
                        'delete': keyboard.Key.delete,
                        'home': keyboard.Key.home,
                        'end': keyboard.Key.end,
                        'pageup': keyboard.Key.page_up,
                        'pagedown': keyboard.Key.page_down,
                        'up': keyboard.Key.up,
                        'down': keyboard.Key.down,
                        'left': keyboard.Key.left,
                        'right': keyboard.Key.right,
                        'f1': keyboard.Key.f1,
                        'f2': keyboard.Key.f2,
                        'f3': keyboard.Key.f3,
                        'f4': keyboard.Key.f4,
                        'f5': keyboard.Key.f5,
                        'f6': keyboard.Key.f6,
                        'f7': keyboard.Key.f7,
                        'f8': keyboard.Key.f8,
                        'f9': keyboard.Key.f9,
                        'f10': keyboard.Key.f10,
                        'f11': keyboard.Key.f11,
                        'f12': keyboard.Key.f12,
                    }
                    
                    if key_char in special_keys:
                        controller.press(special_keys[key_char])
                        controller.release(special_keys[key_char])
            
            # 释放控制键
            if alt:
                controller.release(keyboard.Key.alt)
            if shift:
                controller.release(keyboard.Key.shift)
            if ctrl:
                controller.release(keyboard.Key.ctrl)
                    
        except Exception as e:
            print(f"执行快捷键失败: {e}")
    
    def execute_mouse_click(self, position):
        """执行鼠标点击"""
        try:
            print(f"执行鼠标点击: {position}")
            
            # 解析位置字符串 "x,y"
            x, y = map(int, position.split(','))
            
            # 移动鼠标到指定位置
            self.mouse_controller.position = (x, y)
            
            # 执行鼠标左键点击
            self.mouse_controller.click(mouse.Button.left, 1)
            
        except Exception as e:
            print(f"执行鼠标点击失败: {e}")
    
    def is_active(self):
        """检查键盘监听是否处于活动状态"""
        return self.active
    
    def set_status_callback(self, callback):
        """设置状态变化回调函数"""
        self.status_callback = callback
    
    def _notify_status_change(self, is_active):
        """通知状态变化"""
        if self.status_callback:
            try:
                self.status_callback(is_active)
            except Exception as e:
                print(f"状态回调执行失败: {e}")
    
    def set_overlay_callback(self, callback):
        """设置悬浮窗口更新回调函数"""
        self.overlay_callback = callback
    
    def _notify_overlay_update(self, text):
        """通知悬浮窗口更新显示"""
        if self.overlay_callback:
            try:
                self.overlay_callback(text)
            except Exception as e:
                print(f"悬浮窗口回调执行失败: {e}")
    
    def _clear_input_display(self):
        """清空输入显示"""
        self.current_input = ""
        self._notify_overlay_update("")