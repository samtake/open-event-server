#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Elasticsearch模块 - Open Event Server Elasticsearch客户端

此模块提供Elasticsearch客户端和连接管理功能。

作者: FOSSASIA
"""

from elasticsearch import Elasticsearch
from elasticsearch_dsl.connections import connections
from flask_elasticsearch import FlaskElasticsearch

from config import Config

# 创建Flask-Elasticsearch客户端实例
client = FlaskElasticsearch()


def connect_from_config():
    """
    从配置创建Elasticsearch连接
    
    为elasticsearch_dsl创建连接。
    
    返回:
        Elasticsearch: Elasticsearch客户端实例
    """
    # 创建Elasticsearch存储实例
    es_store = Elasticsearch([Config.ELASTICSEARCH_HOST])
    # 为elasticsearch_dsl创建连接
    connections.create_connection(hosts=[Config.ELASTICSEARCH_HOST])

    return es_store
