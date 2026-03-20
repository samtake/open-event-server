#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Elasticsearch定时任务模块 - Open Event Server Elasticsearch索引管理

警告：此文件包含Elasticsearch的定时任务，请使用纯Python进行操作，
需要Flask应用上下文的对象可能无法正常工作。

此模块提供Elasticsearch索引的重建和同步功能。

作者: FOSSASIA
"""

from app.api.helpers.tasks import celery
from app.models.event import Event
from app.models.search.sync import rebuild_indices, sync, sync_event_from_database
from app.views.elastic_search import connect_from_config
from app.views.postgres import get_session_from_config


@celery.task(name='rebuild.events.elasticsearch')
def cron_rebuild_events_elasticsearch():
    """
    重建Elasticsearch事件索引
    
    重新插入所有符合条件的事件到Elasticsearch，删除现有事件。
    这是一个Celery定时任务。
    """
    # 创建Elasticsearch客户端
    elastic = connect_from_config()
    # 创建数据库会话
    session = get_session_from_config()
    
    # 重建所有索引
    rebuild_indices(client=elastic)

    # 同步所有已发布的事件
    for event in session.query(Event).filter_by(state='published'):
        sync_event_from_database(event)


def sync_events_elasticsearch():
    """
    同步所有新建、更新或删除的事件
    
    同步所有最新创建、更新或删除的事件到Elasticsearch。
    """
    sync()
