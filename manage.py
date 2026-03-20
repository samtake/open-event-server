#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
管理脚本 - Open Event Server 命令行管理工具

此脚本提供各种管理命令，用于数据库初始化、数据修复等操作。

作者: FOSSASIA
"""

import logging
import os

from flask_migrate import MigrateCommand, stamp
from flask_script import Manager
from sqlalchemy import or_
from sqlalchemy.engine import reflection

from app.api.helpers.db import save_to_db
from app.instance import current_app as app
from app.api.helpers.tasks import (
    resize_event_images_task,
    resize_speaker_images_task,
    resize_exhibitor_images_task,
    resize_group_images_task,
)
from app.models import db
from app.models.event import Event, get_new_event_identifier
from app.models.group import Group
from app.models.speaker import Speaker
from app.models.exhibitor import Exhibitor
from populate_db import populate
from tests.all.integration.auth_helper import create_super_admin

logger = logging.getLogger(__name__)

# 创建管理器实例
manager = Manager(app)
manager.add_command('db', MigrateCommand)


@manager.command
def list_routes():
    """
    列出所有路由
    
    显示应用中所有注册的路由信息。
    """
    import urllib

    output = []
    for rule in app.url_map.iter_rules():
        methods = ','.join(rule.methods)
        line = urllib.parse.unquote(f"{rule.endpoint:50s} {methods:20s} {rule}")
        output.append(line)

    for line in sorted(output):
        print(line)


@manager.command
def add_event_identifier():
    """
    为事件添加标识符
    
    为所有事件生成新的标识符。
    """
    events = Event.query.all()
    for event in events:
        event.identifier = get_new_event_identifier()
        save_to_db(event)


@manager.command
def fix_exhibitor_images():
    """
    修复参展商图片
    
    为缺少缩略图的参展商重新生成图片。
    """
    exhibitors = Exhibitor.query.filter(
        Exhibitor.banner_url.isnot(None), Exhibitor.thumbnail_image_url == None
    ).all()
    print(f'正在调整 { len(exhibitors) } 个参展商的图片大小...')
    for exhibitor in exhibitors:
        print(f'正在调整参展商 { exhibitor.id } 的图片')
        resize_exhibitor_images_task.delay(exhibitor.id, exhibitor.banner_url)


@manager.command
def fix_group_images():
    """
    修复组图片
    
    为缺少缩略图的组重新生成图片。
    """
    groups = Group.query.filter(
        Group.banner_url.isnot(None), Group.thumbnail_image_url == None
    ).all()
    print(f'正在调整 { len(groups) } 个组的图片大小...')
    for group in groups:
        print(f'正在调整组 { group.id } 的图片')
        resize_group_images_task.delay(group.id, group.banner_url)


@manager.command
def fix_event_and_speaker_images():
    """
    修复事件和演讲者图片
    
    为缺少各种尺寸图片的事件和演讲者重新生成图片。
    """
    # 修复事件图片
    events = Event.query.filter(
        Event.original_image_url.isnot(None),
        or_(
            Event.thumbnail_image_url == None,
            Event.large_image_url == None,
            Event.icon_image_url == None,
        ),
    ).all()
    logger.info('正在调整 %s 个事件的图片大小...', len(events))
    for event in events:
        logger.info('正在调整事件 %s 的图片', event.id)
        resize_event_images_task.delay(event.id, event.original_image_url)

    # 修复演讲者图片
    speakers = Speaker.query.filter(
        Speaker.photo_url.isnot(None),
        or_(
            Speaker.icon_image_url == None,
            Speaker.small_image_url == None,
            Speaker.thumbnail_image_url == None,
        ),
    ).all()

    logger.info('正在调整 %s 个演讲者的图片大小...', len(speakers))
    for speaker in speakers:
        logging.info('正在调整演讲者 %s 的图片', speaker.id)
        resize_speaker_images_task.delay(speaker.id, speaker.photo_url)


@manager.command
def fix_digit_identifier():
    """
    修复数字标识符
    
    为只包含数字的标识符生成新的标识符。
    """
    events = Event.query.filter(Event.identifier.op('~')(r'^[0-9\.]+$')).all()
    for event in events:
        event.identifier = get_new_event_identifier()
        db.session.add(event)
    db.session.commit()


@manager.option(
    '-c', '--credentials', help='超级管理员凭据。例如: username:password'
)
def initialize_db(credentials):
    """
    初始化数据库
    
    创建数据库表并填充初始数据。
    
    参数:
        credentials: 超级管理员凭据，格式为 username:password
    """
    with app.app_context():
        populate_data = True
        inspector = reflection.Inspector.from_engine(db.engine)
        table_name = 'events'
        table_names = inspector.get_table_names()
        print("[LOG] 现有表:")
        print("[LOG] " + ','.join(table_names))
        if table_name not in table_names:
            print("[LOG] 未找到表。尝试创建")
            try:
                db.engine.execute('create extension if not exists citext')
                db.create_all()
                stamp()
            except Exception:
                populate_data = False
                print(
                    "[LOG] 无法创建表。数据库不存在或表已创建"
                )
            if populate_data:
                credentials = credentials.split(":")
                admin_email = os.environ.get('SUPER_ADMIN_EMAIL', credentials[0])
                admin_password = os.environ.get('SUPER_ADMIN_PASSWORD', credentials[1])
                create_super_admin(admin_email, admin_password)
                populate()
        else:
            print("[LOG] 表已存在。跳过数据填充和创建。")


@manager.command
def prepare_db(credentials='open_event_test_user@fossasia.org:fossasia'):
    """
    准备数据库
    
    初始化数据库并创建超级管理员。
    
    参数:
        credentials: 超级管理员凭据，默认为测试凭据
    """
    with app.app_context():
        initialize_db(credentials)


if __name__ == "__main__":
    # 运行管理器
    manager.run()
