#!/bin/sh
# -*- coding: utf-8 -*-
"""
测试数据库启动脚本 - Open Event Server 测试环境数据库

此脚本用于启动测试用的PostgreSQL数据库容器。

作者: FOSSASIA
"""

# 启动PostgreSQL测试数据库容器
# -d: 后台运行
# -e POSTGRES_USER=test: 设置数据库用户为test
# -e POSTGRES_HOST_AUTH_METHOD=trust: 设置认证方式为信任
# --mount type=tmpfs: 使用内存文件系统存储数据（临时）
# --rm: 容器停止后自动删除
# -p 5433:5432: 端口映射，主机5433映射到容器5432
# --name opev-test-db: 容器名称
# postgis/postgis:12-3.0-alpine: 使用PostGIS镜像
docker run -d -e POSTGRES_USER=test -e POSTGRES_HOST_AUTH_METHOD=trust \
       --mount type=tmpfs,destination=/var/lib/postgresql/data \
       --rm -p 5433:5432 --name opev-test-db postgis/postgis:12-3.0-alpine
