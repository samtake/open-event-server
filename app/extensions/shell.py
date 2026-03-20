#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Shell扩展模块 - Open Event Server Flask Shell配置

此模块配置Flask Shell上下文，使所有数据库模型在Shell中可用。

作者: FOSSASIA
"""

from app.models import db


def init_app(app):
    """
    初始化Shell上下文
    
    配置Flask Shell的上下文，自动导入所有数据库模型。
    
    参数:
        app: Flask应用实例
    """
    @app.shell_context_processor
    def shell_context():
        """
        Shell上下文处理器
        
        返回包含所有数据库模型的字典，便于在Shell中直接访问。
        
        返回:
            dict: 包含db和所有模型的字典
        """
        # 收集所有注册的模型类
        models = {
            model.__name__: model
            for model in list(db.Model._decl_class_registry.values())
            if getattr(model, '__table__', None) is not None
        }
        return dict(db=db, **models)
