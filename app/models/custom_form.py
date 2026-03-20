#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自定义表单模型 - Open Event Server 自定义表单管理模块

此文件定义了自定义表单模型类，用于管理事件的自定义表单。
自定义表单允许事件组织者自定义参与者、演讲者和会话的注册表单。

作者: FOSSASIA
"""

import json

from sqlalchemy.event import listens_for
from sqlalchemy.schema import UniqueConstraint

from app.api.helpers.utilities import to_snake_case
from app.models import db

# 会话表单配置
SESSION_FORM = {
    "title": {"include": 1, "require": 1},  # 标题（包含：是，必填：是）
    "subtitle": {"include": 0, "require": 0},  # 副标题
    "short_abstract": {"include": 1, "require": 0},  # 简短摘要
    "long_abstract": {"include": 0, "require": 0},  # 详细摘要
    "comments": {"include": 1, "require": 0},  # 评论
    "track": {"include": 0, "require": 0},  # 轨道
    "session_type": {"include": 0, "require": 0},  # 会话类型
    "language": {"include": 0, "require": 0},  # 语言
    "slides": {"include": 1, "require": 0},  # 幻灯片
    "video": {"include": 0, "require": 0},  # 视频
    "audio": {"include": 0, "require": 0},  # 音频
}

# 会话自定义表单字段映射
SESSION_CUSTOM_FORM = {
    "title": "标题",
    "subtitle": "副标题",
    "shortAbstract": "简短摘要",
    "longAbstract": "详细摘要",
    "comments": "评论",
    "track": "轨道",
    "sessionType": "会话类型",
    "level": "级别",
    "language": "语言",
    "slidesUrl": "幻灯片",
    "slides": "幻灯片",
    "videoUrl": "视频",
    "audioUrl": "音频",
    "website": "网站",
    "facebook": "Facebook",
    "twitter": "Twitter",
    "github": "GitHub",
    "linkedin": "Linkedin",
    "instagram": "Instagram",
    "gitlab": "Gitlab",
    "mastodon": "Mastodon",
}

# 演讲者表单配置
SPEAKER_FORM = {
    "name": {"include": 1, "require": 1},  # 姓名
    "email": {"include": 1, "require": 1},  # 邮箱
    "photo": {"include": 1, "require": 0},  # 照片
    "organisation": {"include": 1, "require": 0},  # 组织
    "position": {"include": 1, "require": 0},  # 职位
    "country": {"include": 1, "require": 0},  # 国家
    "short_biography": {"include": 1, "require": 0},  # 简短传记
    "long_biography": {"include": 0, "require": 0},  # 详细传记
    "mobile": {"include": 0, "require": 0},  # 手机
    "website": {"include": 1, "require": 0},  # 网站
    "facebook": {"include": 0, "require": 0},  # Facebook
    "twitter": {"include": 1, "require": 0},  # Twitter
    "github": {"include": 0, "require": 0},  # GitHub
    "linkedin": {"include": 0, "require": 0},  # LinkedIn
}

# 演讲者自定义表单字段映射
SPEAKER_CUSTOM_FORM = {
    "name": "姓名",
    "email": "邮箱",
    "photoUrl": "照片",
    "organisation": "组织",
    "position": "职位",
    "address": "地址",
    "country": "国家",
    "city": "城市",
    "longBiography": "详细传记",
    "shortBiography": "简短传记",
    "speakingExperience": "演讲经验",
    "sponsorshipRequired": "需要赞助",
    "gender": "性别",
    "heardFrom": "从哪里听说",
    "mobile": "手机",
    "website": "网站",
    "facebook": "Facebook",
    "twitter": "Twitter",
    "github": "GitHub",
    "linkedin": "Linkedin",
    "instagram": "Instagram",
    "mastodon": "Mastodon",
}

# 参与者表单配置
ATTENDEE_FORM = {
    "firstname": {"include": 1, "require": 1},  # 名字
    "lastname": {"include": 1, "require": 1},  # 姓氏
    "email": {"include": 1, "require": 1},  # 邮箱
    "address": {"include": 1, "require": 0},  # 地址
    "city": {"include": 1, "require": 0},  # 城市
    "state": {"include": 1, "require": 0},  # 州/省
    "country": {"include": 1, "require": 0},  # 国家
    "job_title": {"include": 1, "require": 0},  # 职位
    "phone": {"include": 1, "require": 0},  # 电话
    "tax_business_info": {"include": 1, "require": 0},  # 税务信息
    "billing_address": {"include": 0, "require": 0},  # 账单地址
    "home_address": {"include": 0, "require": 0},  # 家庭地址
    "shipping_address": {"include": 0, "require": 0},  # 收货地址
    "company": {"include": 1, "require": 0},  # 公司
    "work_address": {"include": 0, "require": 0},  # 工作地址
    "work_phone": {"include": 0, "require": 0},  # 工作电话
    "website": {"include": 1, "require": 0},  # 网站
    "blog": {"include": 0, "require": 0},  # 博客
    "twitter": {"include": 1, "require": 0},  # Twitter
    "facebook": {"include": 0, "require": 0},  # Facebook
    "github": {"include": 1, "require": 0},  # GitHub
    "gender": {"include": 0, "require": 0},  # 性别
    "age_group": {"include": 0, "require": 0},  # 年龄组
    "home_wiki": {"include": 0, "require": 0},  # 主页wiki
    "wiki_scholarship": {"include": 0, "require": 0},  # wiki奖学金
    "accept_video_recording": {"include": 0, "require": 0},  # 接受视频录制
    "is_consent_of_refund_policy": {"include": 0, "require": 0},  # 退款政策同意
    "native_language": {"include": 0, "require": 0},  # 母语
    "fluent_language": {"include": 0, "require": 0},  # 流利语言
    "is_consent_form_field": {"include": 0, "require": 0},  # 同意表单字段
    "is_consent_form_field_photo": {"include": 0, "require": 0},  # 照片同意表单字段
    "is_consent_form_field_email": {"include": 0, "require": 0},  # 邮件同意表单字段
}

# 参与者自定义表单字段映射
ATTENDEE_CUSTOM_FORM = {
    "firstname": "名字",
    "lastname": "姓氏",
    "email": "邮箱",
    "address": "地址",
    "city": "城市",
    "state": "州/省",
    "country": "国家",
    "jobTitle": "职位",
    "phone": "电话",
    "taxBusinessInfo": "税务信息",
    "billingAddress": "账单地址",
    "homeAddress": "家庭地址",
    "shippingAddress": "收货地址",
    "company": "组织",
    "workAddress": "工作地址",
    "workPhone": "工作电话",
    "website": "网站",
    "blog": "博客",
    "twitter": "Twitter",
    "facebook": "Facebook",
    "github": "GitHub",
    "linkedin": "LinkedIn",
    "instagram": "Instagram",
    "gender": "这些类别中哪些描述了您的性别认同？（可多选）",
    "ageGroup": "年龄组",
    "acceptVideoRecording": "照片、视频和文本同意",
    "acceptShareDetails": "合作伙伴联系同意",
    "acceptReceiveEmails": "邮件同意",
    "is_consent_form_field": "行为准则同意",
    "is_consent_form_field_photo": "Wikimania照片同意",
    "is_consent_form_field_email": "Wikimania邮件更新",
    "is_consent_of_refund_policy": "退款政策同意",
    "native_language": "您的母语是什么，或者您最流利的语言是什么？",
    "fluent_language": "您还流利掌握以下哪些语言？",
    "home_wiki": "您的主页wiki是什么",
    "wiki_scholarship": "您是否获得过Wikimania奖学金？",
}

# 将表单配置转换为JSON字符串
session_form_str = json.dumps(SESSION_FORM, separators=(',', ':'))
speaker_form_str = json.dumps(SPEAKER_FORM, separators=(',', ':'))
attendee_form_str = json.dumps(ATTENDEE_FORM, separators=(',', ':'))

# 自定义表单标识符名称映射
CUSTOM_FORM_IDENTIFIER_NAME_MAP = {
    "session": SESSION_CUSTOM_FORM,
    "speaker": SPEAKER_CUSTOM_FORM,
    "attendee": ATTENDEE_CUSTOM_FORM,
}


class CustomForms(db.Model):
    """
    自定义表单模型类
    
    此类代表自定义表单，用于定义事件的参与者、演讲者和会话的注册表单字段。
    每个自定义表单记录包含字段标识符、表单类型、字段类型等信息。
    """
    
    # 表单类型定义
    class TYPE:
        ATTENDEE = 'attendee'  # 参与者
        SESSION = 'session'  # 会话
        SPEAKER = 'speaker'  # 演讲者

    __tablename__ = 'custom_forms'  # 数据库表名
    __table_args__ = (
        UniqueConstraint(
            'event_id',
            'field_identifier',
            'form',
            'form_id',
            name='custom_form_identifier',
        ),
    )  # 唯一约束

    # 基本信息
    id = db.Column(db.Integer, primary_key=True)  # 自定义表单ID
    field_identifier = db.Column(db.String, nullable=False)  # 字段标识符
    form = db.Column(db.String, nullable=False)  # 表单类型
    type = db.Column(db.String, nullable=False)  # 字段类型
    name = db.Column(db.String, nullable=False)  # 字段名称
    description = db.Column(db.String, nullable=True)  # 字段描述
    is_required = db.Column(db.Boolean, default=False)  # 是否必填
    is_included = db.Column(db.Boolean, default=False)  # 是否包含
    is_fixed = db.Column(db.Boolean, default=False)  # 是否固定
    position = db.Column(db.Integer, default=0, nullable=False)  # 位置
    is_public = db.Column(db.Boolean, nullable=False, default=False)  # 是否公开
    is_complex = db.Column(db.Boolean, nullable=False, default=False)  # 是否复杂
    event_id = db.Column(db.Integer, db.ForeignKey('events.id', ondelete='CASCADE'))  # 事件ID
    form_id = db.Column(db.String)  # 表单ID
    min = db.Column(db.Integer, default=0, nullable=True)  # 最小值
    max = db.Column(db.Integer, default=10, nullable=True)  # 最大值
    main_language = db.Column(db.String)  # 主要语言
    is_allow_edit = db.Column(db.Boolean, default=False, nullable=False)  # 是否允许编辑
    
    # 关联关系
    custom_form_options = db.relationship('CustomFormOptions', backref="custom_form")  # 自定义表单选项

    @property
    def identifier(self):
        """
        获取标识符
        
        将字段标识符转换为蛇形命名法
        
        返回:
            str: 蛇形命名法的字段标识符
        """
        return to_snake_case(self.field_identifier)

    def __repr__(self):
        """
        字符串表示
        
        返回:
            str: 自定义表单对象的字符串表示
        """
        return f'<CustomForm {self.id!r} {self.identifier!r}>'


def get_set_field_name(target: CustomForms) -> str:
    """
    获取并设置字段名称
    
    根据表单类型和字段标识符从映射表中获取字段名称
    
    参数:
        target (CustomForms): 自定义表单对象
        
    返回:
        str: 字段名称
    """
    form_map = CUSTOM_FORM_IDENTIFIER_NAME_MAP[target.form]
    target_name = form_map.get(target.field_identifier)
    if target_name:
        target.name = target_name

    return target.name


@listens_for(CustomForms, 'before_insert')
@listens_for(CustomForms, 'before_update')
def generate_name(mapper, connect, target: CustomForms) -> None:
    """
    在插入或更新前生成字段名称
    
    参数:
        mapper: SQLAlchemy映射器
        connect: 数据库连接
        target (CustomForms): 自定义表单对象
    """
    get_set_field_name(target)


def assign_field_names(session) -> None:
    """
    为现有表单字段分配名称
    
    用于迁移现有数据库中的表单字段。请勿修改。
    
    参数:
        session: 数据库会话
    """
    statements = []

    for form, dict_map in CUSTOM_FORM_IDENTIFIER_NAME_MAP.items():
        for identifier, name in dict_map.items():
            statements.append(
                f"UPDATE custom_forms SET name = '{name}' WHERE form = '{form}' and field_identifier = '{identifier}';"
            )

    for statement in statements:
        session.execute(statement)