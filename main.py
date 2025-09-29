#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ShortcutsEasier软件主程序
支持自定义按键映射快捷键功能
"""

import sys
import os
import pyperclip

# 添加src目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.keyboard_manager import KeyboardManager
from src.config_manager import ConfigManager
from src.ui_manager import UIManager

def get_mouse_position(keyboard_manager=None):
    """获取鼠标位置并复制到剪贴板"""
    try:
        from pynput import mouse
        # 创建鼠标控制器
        mouse_controller = mouse.Controller()
        
        # 获取当前鼠标位置
        x, y = mouse_controller.position
        
        # 格式化位置字符串
        position_str = f"{int(x)},{int(y)}"
        
        # 复制到剪贴板
        pyperclip.copy(position_str)
        
        print(f"鼠标位置 {position_str} 已复制到剪贴板")
        
        # 重新启动键盘监听器以清除按键状态
        if keyboard_manager:
            keyboard_manager.stop_listening()
            keyboard_manager.start_listening()
        
        return position_str
    except Exception as e:
        print(f"获取鼠标位置失败: {str(e)}")
        return None

def main():
    """主函数"""
    # 初始化配置管理器
    config_manager = ConfigManager()
    
    # 初始化键盘管理器
    keyboard_manager = KeyboardManager(config_manager)
    
    # 设置获取鼠标位置的回调函数
    keyboard_manager.set_get_mouse_position_callback(lambda: get_mouse_position(keyboard_manager))
    
    # 初始化UI管理器
    ui_manager = UIManager(config_manager, keyboard_manager)
    
    # 启动键盘监听
    keyboard_manager.start_listening()
    
    # 启动UI
    ui_manager.run()

if __name__ == "__main__":
    main()