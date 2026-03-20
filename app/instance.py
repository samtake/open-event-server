#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
应用实例模块 - Open Event Server 主应用实例

此模块负责创建和配置Flask应用实例，包括：
- 应用初始化
- 扩展配置
- 路由注册
- 中间件设置
- 健康检查
- 第三方服务集成

作者: FOSSASIA
"""

import logging
import os.path
import secrets
import sys
from datetime import timedelta

import sentry_sdk
import sqlalchemy as sa
import stripe
from celery.signals import after_task_publish
from flask_babel import Babel
from envparse import env
from flask import Flask, json, make_response, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_login import current_user
from flask_migrate import Migrate
from healthcheck import HealthCheck
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.flask import FlaskIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from werkzeug.middleware.profiler import ProfilerMiddleware

from app.api import routes  # noqa: 用于注册路由
from app.api.custom.check_in_stats import check_in_stats_routes
from app.api.helpers.auth import AuthManager, is_token_blacklisted
from app.api.helpers.cache import cache
from app.api.helpers.errors import ErrorResponse
from app.api.helpers.jwt import jwt_user_loader
from app.api.helpers.mail_recorder import MailRecorder
from app.extensions import limiter, shell
from app.models import db
from app.models.utils import add_engine_pidguard, sqlite_datetime_fix
from app.templates.flask_ext.jinja.filters import init_filters
from app.views.blueprints import BlueprintsManager
from app.views.healthcheck import (
    health_check_celery,
    health_check_db,
    health_check_migrations,
)
from app.views.redis_store import redis_store
from app.graphql import views as graphql_views

# 基础目录路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 静态文件和模板目录
static_dir = os.path.dirname(os.path.dirname(__file__)) + "/static"
template_dir = os.path.dirname(__file__) + "/templates"

# 创建Flask应用实例
app = Flask(__name__, static_folder=static_dir, template_folder=template_dir)

# 读取环境变量文件
env.read_envfile()


class ReverseProxied:
    """
    反向代理WSGI应用包装器
    
    处理反向代理环境下的协议和URL方案。
    来源于: http://stackoverflow.com/a/37842465/1562480 by aldel
    """

    def __init__(self, wsgi_app):
        """初始化包装器"""
        self.app = wsgi_app

    def __call__(self, environ, start_response):
        """
        处理WSGI请求
        
        参数:
            environ: WSGI环境变量
            start_response: WSGI响应回调函数
        """
        # 获取代理协议
        scheme = environ.get('HTTP_X_FORWARDED_PROTO')
        if scheme:
            environ['wsgi.url_scheme'] = scheme
        
        # 如果强制SSL，则设置HTTPS协议
        if os.getenv('FORCE_SSL', 'no') == 'yes':
            environ['wsgi.url_scheme'] = 'https'
            
        return self.app(environ, start_response)


# 应用WSGI中间件
app.wsgi_app = ReverseProxied(app.wsgi_app)

# 应用创建标志 - 防止重复创建
app_created = False


def create_app():
    """
    创建和配置Flask应用
    
    初始化应用配置、扩展、数据库、认证、缓存等组件。
    确保应用只创建一次。
    
    返回:
        Flask应用实例
    """
    global app_created
    
    # 注册蓝图和GraphQL视图（仅首次创建时）
    if not app_created:
        BlueprintsManager.register(app)
        graphql_views.init_app(app)
    
    # 初始化数据库迁移
    Migrate(app, db)

    # 加载配置
    app.config.from_object(env('APP_CONFIG', default='config.ProductionConfig'))

    # 安全密钥验证
    if not app.config['SECRET_KEY']:
        if app.config['PRODUCTION']:
            # 生产环境必须设置SECRET_KEY
            app.logger.error(
                'SECRET_KEY must be set in .env or environment variables in production'
            )
            exit(1)
        else:
            # 开发环境使用随机密钥（不推荐）
            random_secret = secrets.token_hex()
            app.logger.warning(
                f'Using random secret "{ random_secret }" for development server. '
                'This is NOT recommended. Set proper SECRET_KEY in .env or environment variables'
            )
            app.config['SECRET_KEY'] = random_secret

    # 初始化数据库
    db.init_app(app)

    # 初始化缓存
    if app.config['CACHING']:
        cache.init_app(app, config={'CACHE_TYPE': 'simple'})
    else:
        cache.init_app(app, config={'CACHE_TYPE': 'null'})

    # Stripe支付配置
    stripe.api_key = 'SomeStripeKey'
    app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False
    app.config['FILE_SYSTEM_STORAGE_FILE_VIEW'] = 'static'

    # 日志配置
    app.logger.addHandler(logging.StreamHandler(sys.stdout))
    app.logger.setLevel(logging.ERROR)

    # JWT认证配置
    app.config['JWT_HEADER_TYPE'] = 'JWT'
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=1)      # 访问令牌过期时间
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=365)  # 刷新令牌过期时间
    app.config['JWT_ERROR_MESSAGE_KEY'] = 'error'
    app.config['JWT_TOKEN_LOCATION'] = ['cookies', 'headers']      # 令牌位置
    app.config['JWT_REFRESH_COOKIE_PATH'] = '/v1/auth/token/refresh'
    app.config['JWT_SESSION_COOKIE'] = False
    app.config['JWT_BLACKLIST_ENABLED'] = True                     # 启用令牌黑名单
    app.config['JWT_BLACKLIST_TOKEN_CHECKS'] = ['refresh']         # 检查刷新令牌
    
    # 初始化JWT管理器
    _jwt = JWTManager(app)
    _jwt.user_loader_callback_loader(jwt_user_loader)
    _jwt.token_in_blacklist_loader(is_token_blacklisted)

    # Celery配置
    app.config['broker_url'] = app.config['REDIS_URL']
    app.config['result_backend'] = app.config['broker_url']
    app.config['accept_content'] = ['json', 'application/text']

    # 邮件记录器
    app.config['MAIL_RECORDER'] = MailRecorder(use_env=True)

    # CORS配置 - 允许所有来源
    CORS(app, resources={r"/*": {"origins": "*"}})
    
    # 初始化认证管理器
    AuthManager.init_login(app)

    # 性能分析（仅在测试和性能分析模式下）
    if app.config['TESTING'] and app.config['PROFILE']:
        app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions=[30])

    # 注册API路由蓝图
    with app.app_context():
        # 导入各种API蓝图
        from app.api.admin_statistics_api.events import event_statistics
        from app.api.auth import auth_routes
        from app.api.custom.attendees import attendee_blueprint
        from app.api.bootstrap import api_v1
        from app.api.celery_tasks import celery_routes
        from app.api.event_copy import event_copy
        from app.api.exports import export_routes
        from app.api.imports import import_routes
        from app.api.uploads import upload_routes
        from app.api.users import user_misc_routes
        from app.api.orders import order_misc_routes
        from app.api.role_invites import role_invites_misc_routes
        from app.api.speaker_invites import speaker_invites_misc_routes
        from app.api.auth import authorised_blueprint
        from app.api.admin_translations import admin_blueprint
        from app.api.orders import alipay_blueprint, stripe_blueprint
        from app.api.sessions import sessions_blueprint
        from app.api.settings import admin_misc_routes
        from app.api.server_version import info_route
        from app.api.custom.orders import ticket_blueprint
        from app.api.custom.orders import order_blueprint
        from app.api.custom.invoices import event_blueprint
        from app.api.custom.calendars import calendar_routes
        from app.api.tickets import tickets_routes
        from app.api.custom.role_invites import role_invites_routes
        from app.api.custom.users_groups_roles import users_groups_roles_routes
        from app.api.custom.events import events_routes
        from app.api.custom.groups import groups_routes
        from app.api.custom.group_role_invite import group_role_invites_routes
        from app.api.video_stream import streams_routes
        from app.api.events import events_blueprint
        from app.api.custom.badge_forms import badge_forms_routes
        from app.api.custom.tickets import ticket_routes
        from app.api.custom.users import users_routes
        from app.api.custom.users_check_in import users_check_in_routes

        # 注册所有API蓝图
        app.register_blueprint(api_v1)
        app.register_blueprint(event_copy)
        app.register_blueprint(upload_routes)
        app.register_blueprint(export_routes)
        app.register_blueprint(import_routes)
        app.register_blueprint(celery_routes)
        app.register_blueprint(auth_routes)
        app.register_blueprint(event_statistics)
        app.register_blueprint(user_misc_routes)
        app.register_blueprint(attendee_blueprint)
        app.register_blueprint(order_misc_routes)
        app.register_blueprint(role_invites_misc_routes)
        app.register_blueprint(speaker_invites_misc_routes)
        app.register_blueprint(authorised_blueprint)
        app.register_blueprint(admin_blueprint)
        app.register_blueprint(alipay_blueprint)
        app.register_blueprint(stripe_blueprint)
        app.register_blueprint(admin_misc_routes)
        app.register_blueprint(info_route)
        app.register_blueprint(ticket_blueprint)
        app.register_blueprint(order_blueprint)
        app.register_blueprint(event_blueprint)
        app.register_blueprint(sessions_blueprint)
        app.register_blueprint(calendar_routes)
        app.register_blueprint(streams_routes)
        app.register_blueprint(role_invites_routes)
        app.register_blueprint(users_groups_roles_routes)
        app.register_blueprint(events_routes)
        app.register_blueprint(groups_routes)
        app.register_blueprint(events_blueprint)
        app.register_blueprint(tickets_routes)
        app.register_blueprint(group_role_invites_routes)
        app.register_blueprint(badge_forms_routes)
        app.register_blueprint(ticket_routes)
        app.register_blueprint(users_routes)
        app.register_blueprint(check_in_stats_routes)
        app.register_blueprint(users_check_in_routes)

        # 数据库引擎保护
        add_engine_pidguard(db.engine)

        # SQLite日期时间修复
        if app.config[  # pytype: disable=attribute-error
            'SQLALCHEMY_DATABASE_URI'
        ].startswith("sqlite://"):
            sqlite_datetime_fix()

    # 配置SQLAlchemy映射
    sa.orm.configure_mappers()

    # 静态文件服务
    if app.config['SERVE_STATIC']:
        app.add_url_rule(
            '/static/<path:filename>', endpoint='static', view_func=app.send_static_file
        )

    # Sentry错误监控集成
    if not app_created and 'SENTRY_DSN' in app.config:
        sentry_sdk.init(
            app.config['SENTRY_DSN'],
            integrations=[
                FlaskIntegration(),      # Flask集成
                RedisIntegration(),      # Redis集成
                CeleryIntegration(),     # Celery集成
                SqlalchemyIntegration(), # SQLAlchemy集成
            ],
            release=app.config['SENTRY_RELEASE_NAME'],
            traces_sample_rate=app.config['SENTRY_TRACES_SAMPLE_RATE'],
        )

    # Redis存储初始化
    redis_store.init_app(app)

    # 初始化扩展
    shell.init_app(app)
    limiter.init_app(app)

    # 标记应用已创建
    app_created = True
    return app


# 创建应用实例
current_app = create_app()

# 初始化Jinja过滤器
init_filters(app)

# 国际化支持 - Babel
babel = Babel(current_app)


@babel.localeselector
def get_locale():
    """
    语言选择器
    
    从用户浏览器的Accept-Language头部中选择最佳匹配的语言。
    根据current_app.config['ACCEPTED_LANGUAGES']中配置的语言列表进行匹配。
    
    返回:
        选择的语言代码
    """
    # 尝试从用户浏览器发送的Accept-Language头部猜测语言
    # 我们在ACCEPTED_LANGUAGES中支持多种语言，最佳匹配将获胜
    # pytype: disable=mro-error
    return request.accept_languages.best_match(current_app.config['ACCEPTED_LANGUAGES'])
    # pytype: enable=mro-error


# 用户跟踪中间件
# 来源: http://stackoverflow.com/questions/26724623/
@app.before_request
def track_user():
    """
    跟踪用户活动
    
    在每个请求前更新已认证用户的最后访问时间。
    """
    if current_user.is_authenticated:
        current_user.update_lat()


# 健康检查端点
health = HealthCheck(current_app, "/health-check")
health.add_check(health_check_celery)    # Celery健康检查
health.add_check(health_check_db)        # 数据库健康检查
health.add_check(health_check_migrations) # 迁移状态健康检查


# 注册Celery任务
# 重要：不要删除这些导入，删除会导致任务无法正常工作
# 必须在celery定义后注册，以解决循环导入问题

from .api.helpers import tasks

# Celery实例
celery = tasks.celery

# 注册定时任务
from app.api.helpers.scheduled_jobs import setup_scheduled_task
setup_scheduled_task(celery)


# http://stackoverflow.com/questions/9824172/find-out-whether-celery-task-exists
@after_task_publish.connect
def update_sent_state(sender=None, headers=None, **kwargs):
    # the task may not exist if sent using `send_task` which
    # sends tasks by name, so fall back to the default result backend
    # if that is the case.
    task = celery.tasks.get(sender)
    backend = task.backend if task else celery.backend
    backend.store_result(headers['id'], None, 'WAITING')


@app.errorhandler(500)
def internal_server_error(error):
    if current_app.config['PROPOGATE_ERROR'] is True:
        exc = ErrorResponse(str(error))
    else:
        exc = ErrorResponse('Unknown error')
    return exc.respond()


@app.errorhandler(429)
def ratelimit_handler(error):
    return make_response(
        json.dumps({'status': 429, 'title': 'Request Limit Exceeded'}),
        429,
        {'Content-Type': 'application/vnd.api+json'},
    )


@app.errorhandler(ErrorResponse)
def handle_exception(error: ErrorResponse):
    return error.respond()


if __name__ == '__main__':
    current_app.run()
