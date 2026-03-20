#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置文件 - Open Event Server 配置管理模块

此文件包含所有环境的配置类，定义了应用程序在不同环境下的配置参数。
包括数据库连接、缓存设置、安全密钥、第三方服务集成等。

作者: FOSSASIA
版本: 1.19.1
"""

import os
import sys

from envparse import env

# 读取环境变量文件
env.read_envfile()

# 基础目录路径
basedir = os.path.abspath(os.path.dirname(__file__))

# 应用程序版本号
VERSION_NAME = '1.19.1'

# 支持的语言列表
# 用于国际化和本地化功能
LANGUAGES = {
    'en': 'English',           # 英语
    'bn': 'Bengali/Bangla',    # 孟加拉语
    'zh_Hans': 'Chinese (Simplified)',  # 简体中文
    'zh_Hant': 'Chinese (Traditional)', # 繁体中文
    'fr': 'French',            # 法语
    'de': 'German',            # 德语
    'id': 'Indonesian',        # 印尼语
    'ko': 'Korean',            # 韩语
    'pl': 'Polish',            # 波兰语
    'es': 'Spanish',           # 西班牙语
    'th': 'Thai',              # 泰语
    'vi': 'Vietnamese',        # 越南语
    'hi': 'Hindi',             # 印地语
    'ja': 'Japanese',          # 日语
    'ru': 'Russian',           # 俄语
}


class Config:
    """
    基础配置类 - 包含默认配置选项
    
    此类定义了所有环境共享的默认配置参数，其他环境配置类继承此类。
    包括数据库设置、缓存配置、安全设置、第三方服务集成等。
    """

    # 调试模式开关 - 生产环境应设为False
    DEBUG = False

    # 环境标识 - 用于区分不同运行环境
    DEVELOPMENT = False    # 开发环境
    STAGING = False      # 预发布环境
    PRODUCTION = False   # 生产环境
    TESTING = False      # 测试环境

    # 安全密钥 - 用于会话加密等安全相关功能
    # 生产环境必须设置，否则应用无法启动
    SECRET_KEY = env.str('SECRET_KEY', default=None)

    # 缓存相关设置
    CACHING = False              # 是否启用缓存
    PROFILE = False             # 是否启用性能分析
    SQLALCHEMY_RECORD_QUERIES = False  # 是否记录SQL查询

    # Flask-Admin主题设置
    FLASK_ADMIN_SWATCH = 'lumen'

    # 应用程序版本
    VERSION = VERSION_NAME
    
    # 接受的语言列表 - 用于国际化
    ACCEPTED_LANGUAGES = [
        'en',        # 英语
        'bn',        # 孟加拉语
        'de',        # 德语
        'es',        # 西班牙语
        'fr',        # 法语
        'hi',        # 印地语
        'id',        # 印尼语
        'ja',        # 日语
        'ko',        # 韩语
        'pl',        # 波兰语
        'ru',        # 俄语
        'th',        # 泰语
        'vi',        # 越南语
        'zh_Hans',   # 简体中文
        'zh_Hant',   # 繁体中文
    ]
    
    # SQLAlchemy配置
    SQLALCHEMY_TRACK_MODIFICATIONS = True  # 跟踪对象修改
    ERROR_404_HELP = False                 # 404错误是否提供帮助信息
    CSRF_ENABLED = True                   # 启用CSRF保护
    
    # 服务器配置
    SERVER_NAME = env('SERVER_NAME', default=None)  # 服务器名称
    CORS_HEADERS = 'Content-Type'                   # CORS头部设置
    
    # 数据库配置
    SQLALCHEMY_DATABASE_URI = env('DATABASE_URL', default=None)  # 数据库连接URI
    SQLALCHEMY_ENGINE_OPTIONS = {'pool_pre_ping': True}         # 数据库引擎选项
    
    # 静态文件服务配置
    SERVE_STATIC = env.bool('SERVE_STATIC', default=False)  # 是否提供静态文件服务
    
    # 性能监控配置
    DATABASE_QUERY_TIMEOUT = 0.1  # 数据库查询超时时间(秒)
    
    # 错误监控配置 - Sentry集成
    SENTRY_DSN = env('SENTRY_DSN', default=None)  # Sentry DSN
    SENTRY_RELEASE_NAME = (
        env('SENTRY_PROJECT_NAME', default='eventyay-server') + '@' + VERSION_NAME
    )
    SENTRY_TRACES_SAMPLE_RATE = env.float('SENTRY_TRACES_SAMPLE_RATE', default=0.1)
    
    # 搜索配置 - Elasticsearch集成
    ENABLE_ELASTICSEARCH = env.bool('ENABLE_ELASTICSEARCH', default=False)  # 是否启用Elasticsearch
    ELASTICSEARCH_HOST = env('ELASTICSEARCH_HOST', default='localhost:9200')  # Elasticsearch主机地址
    
    # 缓存和消息队列配置 - Redis
    REDIS_URL = env('REDIS_URL', default='redis://localhost:6379/0')  # Redis连接URL
    CELERY_BACKKEND = env('CELERY_BACKEND', default='redis')        # Celery后端
    
    # API配置
    SOFT_DELETE = True  # 是否启用软删除
    PROPOGATE_ERROR = env.bool('PROPOGATE_ERROR', default=False)  # 是否传播错误
    DASHERIZE_API = True  # API响应是否使用短横线命名
    API_PROPOGATE_UNCAUGHT_EXCEPTIONS = env.bool(
        'API_PROPOGATE_UNCAUGHT_EXCEPTIONS', default=True
    )  # 是否传播未捕获的异常
    ETAG = True  # 是否启用ETag缓存
    ATTACH_ORDER_PDF = env.bool('ATTACH_ORDER_PDF', default=True)  # 订单是否附加PDF
    
    # 订单配置
    # 允许未验证用户购买免费门票，默认: False
    ALLOW_UNVERIFIED_FREE_ORDERS = env.bool('ALLOW_UNVERIFIED_FREE_ORDERS', default=False)

    # 数据库URI验证 - 必须设置DATABASE_URL环境变量
    if not SQLALCHEMY_DATABASE_URI:
        print('`DATABASE_URL` either not exported or empty')
        sys.exit()

    # 基础目录设置
    BASE_DIR = basedir
    
    # SSL强制设置
    FORCE_SSL = os.getenv('FORCE_SSL', 'no') == 'yes'

    # 静态文件路径配置
    if SERVE_STATIC:
        UPLOADS_FOLDER = BASE_DIR + '/static/uploads/'              # 上传文件夹
        TEMP_UPLOADS_FOLDER = BASE_DIR + '/static/uploads/temp/'    # 临时上传文件夹
        UPLOAD_FOLDER = UPLOADS_FOLDER                             # 上传文件夹别名
        STATIC_URL = '/static/'                                    # 静态文件URL
        STATIC_ROOT = 'staticfiles'                               # 静态文件根目录
        STATICFILES_DIRS = (os.path.join(BASE_DIR, 'static'),)    # 静态文件目录列表

    # HTTPS配置
    if FORCE_SSL:
        PREFERRED_URL_SCHEME = 'https'  # 优先URL方案设为HTTPS


class ProductionConfig(Config):
    """
    生产环境配置类
    
    用于生产环境的配置，启用性能优化和安全设置。
    包括页面压缩、缓存等生产环境特性。
    """

    ENV = 'production'      # 环境标识设为生产环境
    MINIFY_PAGE = True      # 启用页面压缩
    PRODUCTION = True       # 生产环境标志
    CACHING = True          # 启用缓存


class StagingConfig(ProductionConfig):
    """
    预发布环境配置类
    
    继承自生产环境配置，用于预发布/测试环境。
    与生产环境类似但标记为预发布环境。
    """

    PRODUCTION = False  # 非生产环境
    STAGING = True      # 预发布环境标志


class DevelopmentConfig(Config):
    """
    开发环境配置类
    
    用于开发环境的配置，启用调试模式和错误传播。
    便于开发过程中的调试和问题定位。
    """

    ENV = 'development'            # 环境标识设为开发环境
    DEVELOPMENT = True             # 开发环境标志
    DEBUG = True                   # 启用调试模式
    CACHING = True                 # 启用缓存
    PROPOGATE_ERROR = True         # 传播错误信息
    
    # 测试数据库性能
    SQLALCHEMY_RECORD_QUERIES = True  # 记录SQL查询用于性能分析


class TestingConfig(Config):
    """
    测试环境配置类
    
    用于自动化测试的配置，优化测试执行速度。
    使用内存数据库和同步任务执行。
    """

    ENV = 'testing'                              # 环境标识设为测试环境
    TESTING = True                              # 测试环境标志
    CELERY_TASK_ALWAYS_EAGER = True             # Celery任务立即执行（同步）
    CELERY_TASK_EAGER_PROPAGATES = True         # 任务错误立即传播
    SQLALCHEMY_RECORD_QUERIES = True            # 记录SQL查询
    DEBUG_TB_ENABLED = False                    # 禁用调试工具栏
    BROKER_BACKEND = 'memory'                   # 使用内存作为消息代理
    SQLALCHEMY_DATABASE_URI = env('TEST_DATABASE_URL', default=None)  # 测试数据库URL
    PROPOGATE_ERROR = True                      # 传播错误信息
