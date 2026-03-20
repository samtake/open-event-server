#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户模型 - Open Event Server 用户管理模块

此文件定义了用户模型类及其相关功能，包括：
- 用户基本信息管理
- 认证和授权
- 角色权限管理
- 社交媒体集成
- 事件关联

作者: FOSSASIA
"""

import random
from datetime import datetime

import humanize
import pytz
from citext import CIText
from coolname import generate
from flask import url_for
from flask_scrypt import generate_password_hash, generate_random_salt
from slugify import slugify
from sqlalchemy import desc, event
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound
from sqlalchemy.sql import func

from app.api.helpers.db import get_count
from app.api.helpers.utilities import get_serializer
from app.models import db
from app.models.base import SoftDeletionModel
from app.models.custom_system_role import UserSystemRole
from app.models.event import Event
from app.models.helpers.versioning import clean_html, clean_up_string
from app.models.notification import Notification
from app.models.panel_permission import PanelPermission
from app.models.permission import Permission
from app.models.role import Role
from app.models.service import Service
from app.models.session import Session
from app.models.speaker import Speaker
from app.models.user_permission import UserPermission
from app.models.users_events_role import UsersEventsRoles as UER

# 系统级角色定义
ADMIN = 'admin'           # 管理员
SUPERADMIN = 'super_admin'  # 超级管理员

MARKETER = 'Marketer'         # 市场营销人员
SALES_ADMIN = 'Sales Admin'   # 销售管理员

# 系统角色列表
SYS_ROLES_LIST = [
    ADMIN,
    SUPERADMIN,
]

# 事件特定角色定义
TRACK_ORGANIZER = 'track_organizer'  # 轨道组织者
MODERATOR = 'moderator'              # 主持人
REGISTRAR = 'registrar'            # 注册员

# 所有事件角色列表
EVENT_ROLES_LIST = [
    'owner',            # 所有者
    'organizer',        # 组织者
    'coorganizer',      # 共同组织者
    TRACK_ORGANIZER,    # 轨道组织者
    MODERATOR,          # 主持人
    REGISTRAR,          # 注册员
]


class User(SoftDeletionModel):
    """
    用户模型类
    
    此类代表系统中的用户，包含用户基本信息、认证信息、
    权限信息以及与事件相关的各种关联。
    """

    __tablename__ = 'users'  # 数据库表名

    # 基本身份信息
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # 用户ID
    _email = db.Column(CIText, unique=True, nullable=False)  # 邮箱地址（不区分大小写）
    _password = db.Column(db.String(128), nullable=False)  # 加密密码
    facebook_id = db.Column(db.BigInteger, unique=True, nullable=True, name='facebook_id')  # Facebook ID
    facebook_login_hash = db.Column(db.String, nullable=True)  # Facebook登录哈希
    reset_password = db.Column(db.String(128))  # 重置密码令牌
    salt = db.Column(db.String(128))  # 密码盐值
    
    # 头像和图像
    avatar_url = db.Column(db.String)  # 头像URL
    original_image_url = db.Column(db.String, nullable=True, default=None)  # 原始图片URL
    thumbnail_image_url = db.Column(db.String)  # 缩略图URL
    small_image_url = db.Column(db.String)  # 小图URL
    icon_image_url = db.Column(db.String)  # 图标URL
    
    # 个人信息
    first_name = db.Column(db.String, nullable=True)  # 名字
    last_name = db.Column(db.String, nullable=True)   # 姓氏
    details = db.Column(db.String)  # 详细信息
    contact = db.Column(db.String)  # 联系方式
    public_name = db.Column(db.String)  # 公开显示名称
    
    # 社交媒体链接
    facebook_url = db.Column(db.String)   # Facebook链接
    twitter_url = db.Column(db.String)    # Twitter链接
    instagram_url = db.Column(db.String)  # Instagram链接
    google_plus_url = db.Column(db.String)  # Google+链接
    
    # 系统权限
    is_super_admin = db.Column(db.Boolean, default=False)  # 是否为超级管理员
    is_admin = db.Column(db.Boolean, default=False)       # 是否为管理员
    is_sales_admin = db.Column(db.Boolean, default=False) # 是否为销售管理员
    is_marketer = db.Column(db.Boolean, default=False)   # 是否为市场营销人员
    is_verified = db.Column(db.Boolean, default=False)   # 是否已验证邮箱
    is_blocked = db.Column(db.Boolean, nullable=False, default=False)  # 是否被屏蔽
    is_profile_public = db.Column(
        db.Boolean, nullable=False, default=False, server_default='False'
    )  # 个人资料是否公开
    
    # 注册和访问信息
    was_registered_with_order = db.Column(db.Boolean, default=False)  # 是否通过订单注册
    last_accessed_at = db.Column(db.DateTime(timezone=True))  # 最后访问时间
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())  # 创建时间
    
    # 账单信息（用于发票）
    billing_contact_name = db.Column(db.String)  # 账单联系人姓名
    billing_phone = db.Column(db.String)         # 账单联系电话
    billing_state = db.Column(db.String)         # 账单州/省
    billing_country = db.Column(db.String)       # 账单国家
    billing_tax_info = db.Column(db.String)      # 账单税务信息
    company = db.Column(db.String)               # 公司名称
    billing_address = db.Column(db.String)       # 账单地址
    billing_city = db.Column(db.String)          # 账单城市
    language_prefrence = db.Column(db.String)    # 语言偏好
    billing_zip_code = db.Column(db.String)      # 账单邮编
    billing_additional_info = db.Column(db.String)  # 账单附加信息
    
    # Rocket.Chat集成
    rocket_chat_token = db.Column(db.String)  # Rocket.Chat令牌
    
    # 社交登录令牌
    tokens = db.Column(db.Text)  # 第三方登录令牌

    # 关联关系
    speaker = db.relationship('Speaker', backref="user")  # 演讲者关联
    favourite_events = db.relationship('UserFavouriteEvent', backref="user")  # 收藏事件
    session = db.relationship('Session', backref="user")  # 会话关联
    feedback = db.relationship('Feedback', backref="user")  # 反馈关联
    access_codes = db.relationship('AccessCode', backref="user")  # 访问码关联
    discount_codes = db.relationship('DiscountCode', backref="user")  # 折扣码关联
    
    # 市场营销人员关联的事件
    marketer_events = db.relationship(
        'Event',
        viewonly=True,
        secondary='join(UserSystemRole, CustomSysRole,'
        ' and_(CustomSysRole.id == UserSystemRole.role_id, CustomSysRole.name == "Marketer"))',
        primaryjoin='UserSystemRole.user_id == User.id',
        secondaryjoin='Event.id == UserSystemRole.event_id',
    )
    
    # 销售管理员关联的事件
    sales_admin_events = db.relationship(
        'Event',
        viewonly=True,
        secondary='join(UserSystemRole, CustomSysRole,'
        ' and_(CustomSysRole.id == UserSystemRole.role_id, CustomSysRole.name == "Sales Admin"))',
        primaryjoin='UserSystemRole.user_id == User.id',
        secondaryjoin='Event.id == UserSystemRole.event_id',
    )

    @hybrid_property
    def password(self):
        """
        密码混合属性
        
        返回加密后的密码字符串
        
        返回:
            str: 加密后的密码
        """
        return self._password

    @password.setter
    def password(self, password):
        """
        密码设置器
        
        设置密码时自动生成盐值并加密密码
        
        参数:
            password (str): 明文密码
        """
        salt = str(generate_random_salt(), 'utf-8')
        self._password = str(generate_password_hash(password, salt), 'utf-8')
        hash_ = random.getrandbits(128)
        self.reset_password = str(hash_)
        self.salt = salt

    @hybrid_property
    def email(self):
        """
        邮箱混合属性
        
        返回用户的邮箱地址
        
        返回:
            str: 用户邮箱地址
        """
        return self._email

    @email.setter
    def email(self, email):
        """
        邮箱设置器
        
        更新邮箱地址时将用户标记为未验证
        
        参数:
            email (str): 新的邮箱地址
        """
        if self._email != email:
            self._email = email
            self.is_verified = False

    # 用户权限相关方法
    def can_publish_event(self):
        """
        检查用户是否可以发布事件
        
        根据用户权限设置和验证状态判断用户是否有权发布事件。
        
        返回:
            bool: 是否可以发布事件
        """
        perm = UserPermission.query.filter_by(name='publish_event').first()
        if not perm:
            return self.is_verified

        if self.is_verified is False:
            return perm.unverified_user

        return True

    def can_create_event(self):
        """
        检查用户是否可以创建事件
        
        根据用户权限设置和验证状态判断用户是否有权创建事件。
        
        返回:
            bool: 是否可以创建事件
        """
        perm = UserPermission.query.filter_by(name='create_event').first()
        if not perm:
            return self.is_verified

        if self.is_verified is False:
            return perm.unverified_user

        return True

    def _is_role(self, role_name, event_id=None):
        """
        检查用户是否拥有特定事件角色
        
        检查用户在指定事件中是否拥有特定角色，包括组权限。
        
        参数:
            role_name (str): 角色名称
            event_id (int, optional): 事件ID
            
        返回:
            bool: 是否拥有该角色
        """
        from app.models.users_groups_role import UsersGroupsRoles

        role = Role.query.filter_by(name=role_name).first()
        uer = UER.query.filter_by(user=self, role=role)
        ugr = UsersGroupsRoles.query.filter_by(user=self, role=role, accepted=True)
        
        if event_id:
            uer = uer.filter_by(event_id=event_id)
            event = Event.query.get(event_id)
            # 验证事件不为None
            if event is not None and event.group is not None:
                ugr = ugr.filter_by(group=event.group)
                
        return bool(uer.first() or ugr.first())

    def is_owner(self, event_id):
        """
        检查用户是否为事件所有者
        
        参数:
            event_id (int): 事件ID
            
        返回:
            bool: 是否为事件所有者
        """
        return self._is_role(Role.OWNER, event_id)

    def is_organizer(self, event_id):
        """
        检查用户是否为事件组织者
        
        参数:
            event_id (int): 事件ID
            
        返回:
            bool: 是否为事件组织者
        """
        return self._is_role(Role.ORGANIZER, event_id)

    def is_coorganizer(self, event_id):
        """
        检查用户是否为事件共同组织者
        
        参数:
            event_id (int): 事件ID
            
        返回:
            bool: 是否为事件共同组织者
        """
        return self._is_role(Role.COORGANIZER, event_id)

    def is_track_organizer(self, event_id):
        """
        检查用户是否为轨道组织者
        
        参数:
            event_id (int): 事件ID
            
        返回:
            bool: 是否为轨道组织者
        """
        return self._is_role(TRACK_ORGANIZER, event_id)

    def is_moderator(self, event_id):
        """
        检查用户是否为事件主持人
        
        参数:
            event_id (int): 事件ID
            
        返回:
            bool: 是否为事件主持人
        """
        return self._is_role(MODERATOR, event_id)

    def is_registrar(self, event_id):
        """
        检查用户是否为注册员
        
        参数:
            event_id (int): 事件ID
            
        返回:
            bool: 是否为注册员
        """
        return self._is_role(REGISTRAR, event_id)

    def has_event_access(self, event_id):
        """
        检查用户是否有事件访问权限
        
        检查用户是否为事件所有者、组织者或共同组织者。
        
        参数:
            event_id (int): 事件ID
            
        返回:
            bool: 是否有事件访问权限
        """
        return (
            self._is_role(Role.OWNER, event_id)
            or self._is_role(Role.ORGANIZER, event_id)
            or self._is_role(Role.COORGANIZER, event_id)
        )

    @hybrid_property
    def is_user_owner(self):
        """
        检查用户是否为任意事件的所有者
        
        返回:
            bool: 是否为任意事件的所有者
        """
        return self._is_role(Role.OWNER)

    @hybrid_property
    def is_user_organizer(self):
        """
        检查用户是否为任意事件的组织者
        
        返回:
            bool: 是否为任意事件的组织者
        """
        return self._is_role(Role.ORGANIZER)

    @hybrid_property
    def is_user_coorganizer(self):
        """
        检查用户是否为任意事件的共同组织者
        
        返回:
            bool: 是否为任意事件的共同组织者
        """
        return self._is_role(Role.COORGANIZER)

    @hybrid_property
    def is_user_track_organizer(self):
        """
        检查用户是否为任意事件的轨道组织者
        
        返回:
            bool: 是否为任意事件的轨道组织者
        """
        return self._is_role(TRACK_ORGANIZER)

    @hybrid_property
    def is_user_moderator(self):
        """
        检查用户是否为任意事件的主持人
        
        返回:
            bool: 是否为任意事件的主持人
        """
        return self._is_role(MODERATOR)

    @hybrid_property
    def is_user_registrar(self):
        """
        检查用户是否为任意事件的注册员
        
        返回:
            bool: 是否为任意事件的注册员
        """
        return self._is_role(REGISTRAR)

    def _has_perm(self, operation, service_class, event_id):
        """
        检查用户对特定服务的操作权限
        
        参数:
            operation (str): 操作类型 ('create', 'read', 'update', 'delete')
            service_class: 服务类
            event_id (int): 事件ID
            
        返回:
            bool: 是否有权限执行该操作
            
        异常:
            ValueError: 当操作类型无效时抛出
        """
        # 操作名称及其在Permissions中的对应权限
        operations = {
            'create': 'can_create',
            'read': 'can_read',
            'update': 'can_update',
            'delete': 'can_delete',
        }
        if operation not in list(operations.keys()):
            raise ValueError('No such operation defined')

        try:
            service_name = service_class.get_service_name()
        except AttributeError:
            # 如果service_class没有get_service_name()方法
            return False

        # 超级管理员拥有所有权限
        if self.is_super_admin:
            return True

        service = Service.query.filter_by(name=service_name).first()

        uer_querylist = UER.query.filter_by(user=self, event_id=event_id)
        for uer in uer_querylist:
            role = uer.role
            perm = Permission.query.filter_by(role=role, service=service).first()
            if getattr(perm, operations[operation]):
                return True

        return False

    def can_create(self, service_class, event_id):
        """
        检查用户是否可以创建指定服务
        
        参数:
            service_class: 服务类
            event_id (int): 事件ID
            
        返回:
            bool: 是否可以创建
        """
        return self._has_perm('create', service_class, event_id)

    def can_read(self, service_class, event_id):
        """
        检查用户是否可以读取指定服务
        
        参数:
            service_class: 服务类
            event_id (int): 事件ID
            
        返回:
            bool: 是否可以读取
        """
        return self._has_perm('read', service_class, event_id)

    def can_update(self, service_class, event_id):
        """
        检查用户是否可以更新指定服务
        
        参数:
            service_class: 服务类
            event_id (int): 事件ID
            
        返回:
            bool: 是否可以更新
        """
        return self._has_perm('update', service_class, event_id)

    def can_delete(self, service_class, event_id):
        """
        检查用户是否可以删除指定服务
        
        参数:
            service_class: 服务类
            event_id (int): 事件ID
            
        返回:
            bool: 是否可以删除
        """
        return self._has_perm('delete', service_class, event_id)

    def can_delete(self, service_class, event_id):
        """
        检查用户是否可以删除指定服务
        
        参数:
            service_class: 服务类
            event_id (int): 事件ID
            
        返回:
            bool: 是否可以删除
        """
        return self._has_perm('delete', service_class, event_id)

    def is_speaker_at_session(self, session_id):
        """
        检查用户是否为特定会话的演讲者
        
        参数:
            session_id (int): 会话ID
            
        返回:
            bool: 是否为该会话的演讲者
        """
        try:
            session = (
                Session.query.filter(Session.speakers.any(Speaker.user_id == self.id))
                .filter(Session.id == session_id)
                .one()
            )
            return bool(session)
        except MultipleResultsFound:
            return False
        except NoResultFound:
            return False

    def is_speaker_at_event(self, event_id):
        """
        检查用户是否为特定事件的演讲者
        
        参数:
            event_id (int): 事件ID
            
        返回:
            bool: 是否为该事件的演讲者
        """
        try:
            session = (
                Session.query.filter(Session.speakers.any(Speaker.user_id == self.id))
                .filter(Session.event_id == event_id)
                .first()
            )
            return bool(session)
        except MultipleResultsFound:
            return False
        except NoResultFound:
            return False

    # Flask-Login集成方法
    def is_authenticated(self):
        """
        检查用户是否已认证
        
        Flask-Login要求的方法，始终返回True表示用户已认证。
        
        返回:
            bool: 是否已认证
        """
        return True

    def is_active(self):
        """
        检查用户是否活跃
        
        Flask-Login要求的方法，始终返回True表示用户活跃。
        
        返回:
            bool: 是否活跃
        """
        return True

    def is_anonymous(self):
        """
        检查用户是否为匿名用户
        
        Flask-Login要求的方法，始终返回False表示不是匿名用户。
        
        返回:
            bool: 是否为匿名用户
        """
        return False

    def get_id(self):
        """
        获取用户ID
        
        Flask-Login要求的方法，返回用户的唯一标识符。
        
        返回:
            str: 用户ID字符串
        """
        return str(self.id)

    def is_correct_password(self, password):
        """
        验证密码是否正确
        
        使用存储的盐值对提供的密码进行加密，并与存储的密码进行比较。
        
        参数:
            password (str): 要验证的密码
            
        返回:
            bool: 密码是否正确
        """
        salt = self.salt
        password = str(generate_password_hash(password, salt), 'utf-8')
        if password == self._password:
            return True
        return False

    @property
    def is_staff(self):
        """
        检查用户是否为系统员工
        
        员工包括超级管理员和管理员。
        
        返回:
            bool: 是否为系统员工
        """
        return self.is_super_admin or self.is_admin

    def is_sys_role(self, role_id):
        """
        检查用户是否拥有自定义系统角色
        
        参数:
            role_id (int): CustomSysRole实例的ID
            
        返回:
            bool: 是否拥有该系统角色
        """
        role = UserSystemRole.query.filter_by(user=self, role_id=role_id).first()
        return bool(role)

    def first_access_panel(self):
        """
        获取用户可访问的第一个管理面板
        
        检查用户是否被分配了自定义角色，并返回可访问的面板名称。
        
        返回:
            str or False: 面板名称（如果存在）或False
        """
        custom_role = UserSystemRole.query.filter_by(user=self).first()
        if not custom_role:
            return False
        perm = PanelPermission.query.filter(
            PanelPermission.custom_system_roles.any(id=custom_role.role_id)
        ).first()
        if not perm:
            return False
        return perm.panel_name

    def can_access_panel(self, panel_name):
        """
        检查用户是否可以访问特定管理面板
        
        参数:
            panel_name (str): 面板名称
            
        返回:
            bool: 是否可以访问该面板
        """
        if self.is_staff:
            return True

        custom_sys_roles = UserSystemRole.query.filter_by(user=self)
        for custom_role in custom_sys_roles:
            if custom_role.role.can_access(panel_name):
                return True

        return False

    def get_unread_notif_count(self):
        """
        获取未读通知数量
        
        返回:
            int: 未读通知数量
        """
        return get_count(Notification.query.filter_by(user=self, is_read=False))

    def get_unread_notifs(self):
        """
        获取未读通知列表
        
        获取包含标题、人性化接收时间和标记已读链接的未读通知。
        
        返回:
            list: 未读通知列表，每个通知包含title, received_at, mark_read字段
        """
        notifs = []
        unread_notifs = Notification.query.filter_by(user=self, is_read=False).order_by(
            desc(Notification.received_at)
        )
        for notif in unread_notifs:
            notifs.append(
                {
                    'title': notif.title,
                    'received_at': humanize.naturaltime(
                        datetime.now(pytz.utc) - notif.received_at
                    ),
                    'mark_read': url_for(
                        'notifications.mark_as_read', notification_id=notif.id
                    ),
                }
            )

        return notifs

    # 更新最后访问时间
    def update_lat(self):
        """
        更新用户最后访问时间
        
        将当前时间设置为用户的最后访问时间。
        """
        self.last_accessed_at = datetime.now()

    # 已弃用
    @property
    def fullname(self):
        """
        获取用户全名（已弃用）
        
        返回:
            str: 用户全名
        """
        return self.full_name

    @property
    def full_name(self):
        """
        获取用户全名
        
        将名字和姓氏用空格连接。
        
        返回:
            str: 用户全名
        """
        return ' '.join(filter(None, [self.first_name, self.last_name]))

    def get_full_billing_address(self, sep: str = '\n') -> str:
        """
        获取完整账单地址
        
        将账单地址的各个部分用指定分隔符连接。
        
        参数:
            sep (str): 分隔符，默认为换行符
            
        返回:
            str: 完整账单地址
        """
        return sep.join(
            filter(
                None,
                [
                    self.billing_address,
                    self.billing_city,
                    self.billing_state,
                    self.billing_zip_code,
                    self.billing_country,
                ],
            )
        )

    full_billing_address = property(get_full_billing_address)

    @property
    def anonymous_name(self):
        """
        获取匿名名称
        
        生成一个随机的匿名名称，用于保护隐私。
        
        返回:
            str: 匿名名称
        """
        return ' '.join(map(lambda x: x.capitalize(), generate(2)))

    @property
    def rocket_chat_username(self):
        """
        获取Rocket.Chat用户名
        
        根据用户的公开名称或全名生成Rocket.Chat用户名。
        
        返回:
            str: Rocket.Chat用户名
        """
        name = self.public_name or self.full_name or f'user_{self.id}'
        return slugify(name, word_boundary=True, max_length=32, separator='.')

    @property
    def rocket_chat_password(self):
        """
        获取Rocket.Chat密码
        
        为用户生成Rocket.Chat密码。
        
        返回:
            str: Rocket.Chat密码
        """
        return get_serializer().dumps(f'rocket_chat_user_{self.id}')

    @property
    def is_rocket_chat_registered(self) -> bool:
        """
        检查用户是否已注册Rocket.Chat
        
        返回:
            bool: 是否已注册Rocket.Chat
        """
        return self.rocket_chat_token is not None

    def __repr__(self):
        """
        用户对象的字符串表示
        
        返回:
            str: 用户对象的字符串表示
        """
        return '<User %r>' % self.email

    def __setattr__(self, name, value):
        """
        设置属性时的自定义处理
        
        对details字段进行HTML清理和内容清理。
        
        参数:
            name (str): 属性名称
            value: 属性值
        """
        if name == 'details':
            super().__setattr__(name, clean_html(clean_up_string(value)))
        else:
            super().__setattr__(name, value)


@event.listens_for(User, 'init')
def receive_init(target, args, kwargs):
    """
    用户初始化监听器
    
    在用户实例初始化时自动设置注册时间。
    
    参数:
        target: 用户实例
        args: 位置参数
        kwargs: 关键字参数
    """
    target.signup_at = datetime.now(pytz.utc)
