#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
配置管理模块
负责读取和保存用户自定义的按键映射配置
"""

import json
import os

class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_file="config.json"):
        """初始化配置管理器"""
        self.config_file = config_file
        self.config = {}
        self.load_config()
    
    def load_config(self):
        """加载配置文件"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
            except Exception as e:
                print(f"加载配置文件失败: {e}")
                self.config = {}
        else:
            # 默认配置
            self.config = {
                "mappings": {
                    "copy": "ctrl+c",
                    "paste": "ctrl+v",
                    "cut": "ctrl+x",
                    "undo": "ctrl+z",
                    "redo": "ctrl+y"
                },
                "mouse_mappings": {}
            }
            self.save_config()
    
    def save_config(self):
        """保存配置文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"保存配置文件失败: {e}")
    
    def get_mappings(self):
        """获取所有按键映射"""
        return self.config.get("mappings", {})
    
    def get_mouse_mappings(self):
        """获取所有鼠标点击映射"""
        return self.config.get("mouse_mappings", {})
    
    def add_mapping(self, key, hotkey):
        """添加按键映射"""
        if "mappings" not in self.config:
            self.config["mappings"] = {}
        self.config["mappings"][key] = hotkey
        self.save_config()
    
    def add_mouse_mapping(self, key, position):
        """添加鼠标点击映射"""
        if "mouse_mappings" not in self.config:
            self.config["mouse_mappings"] = {}
        # 位置格式: "x,y" 例如: "100,200"
        self.config["mouse_mappings"][key] = position
        self.save_config()
    
    def remove_mapping(self, key):
        """删除按键映射"""
        if "mappings" in self.config and key in self.config["mappings"]:
            del self.config["mappings"][key]
            self.save_config()
    
    def remove_mouse_mapping(self, key):
        """删除鼠标点击映射"""
        if "mouse_mappings" in self.config and key in self.config["mouse_mappings"]:
            del self.config["mouse_mappings"][key]
            self.save_config()
    
    def update_mapping(self, old_key, new_key, hotkey):
        """更新按键映射"""
        self.remove_mapping(old_key)
        self.add_mapping(new_key, hotkey)