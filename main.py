#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Quicker-like软件主程序
支持自定义按键映射快捷键功能
"""

import sys
import os

# 添加src目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.keyboard_manager import KeyboardManager
from src.config_manager import ConfigManager
from src.ui_manager import UIManager

def main():
    """主函数"""
    # 初始化配置管理器
    config_manager = ConfigManager()
    
    # 初始化键盘管理器
    keyboard_manager = KeyboardManager(config_manager)
    
    # 初始化UI管理器
    ui_manager = UIManager(config_manager, keyboard_manager)
    
    # 启动键盘监听
    keyboard_manager.start_listening()
    
    # 启动UI
    ui_manager.run()

if __name__ == "__main__":
    main()