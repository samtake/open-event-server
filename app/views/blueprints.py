#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
蓝图管理模块 - Open Event Server 路由和后台管理

此模块负责管理Flask蓝图和Flask-Admin后台管理界面。

作者: FOSSASIA
"""

import flask_login as login
import requests
from flask import Blueprint, make_response, redirect, request, url_for
from flask_admin import Admin, AdminIndexView, expose
from flask_admin import helpers as admin_helpers
from flask_admin.contrib.sqla import ModelView
from wtforms import fields, form, validators

from app.models import db
from app.models.user import User


class AdminModelView(ModelView):
    """
    管理员模型视图
    """
    
    def is_accessible(self):
        """
        检查当前用户是否有权限访问
        
        返回:
            bool: 是否有权限访问
        """
        return login.current_user.is_authenticated

    def inaccessible_callback(self, name, **kwargs):
        """
        当用户无权限访问时的回调
        
        参数:
            name: 视图名称
            **kwargs: 其他参数
            
        返回:
            Response: 重定向到登录页面
        """
        # 如果用户没有访问权限，重定向到登录页面
        return redirect(url_for('admin.index', next=request.url))


class LoginForm(form.Form):
    """
    管理员登录表单
    """
    
    login = fields.TextField(
        validators=[validators.required(), validators.email()],
        render_kw={"placeholder": "john.doe@example.com"},
    )
    password = fields.PasswordField(
        validators=[validators.required()], render_kw={"placeholder": "密码"}
    )

    def validate_login(self, field):
        """
        验证登录信息
        
        参数:
            field: 表单字段
            
        异常:
            validators.ValidationError: 当验证失败时抛出
        """
        user = self.get_user()

        if user is None:
            raise validators.ValidationError('用户不存在。')

        if not user.is_correct_password(self.password.data):
            raise validators.ValidationError('凭据不正确。')

        if not user.is_admin and not user.is_super_admin:
            raise validators.ValidationError('访问被禁止。需要管理员权限')

    def get_user(self):
        """
        根据邮箱获取用户
        
        返回:
            User: 用户对象，如果不存在则返回None
        """
        return User.query.filter_by(email=self.login.data).first()


class MyAdminIndexView(AdminIndexView):
    """
    自定义管理员索引视图
    """
    
    @expose('/')
    def index(self):
        """
        /admin 路由
        
        返回:
            Response: 响应对象
        """
        if not login.current_user.is_authenticated:
            return redirect(url_for('.login_view'))
        return super().index()

    @expose('/login/', methods=('GET', 'POST'))
    def login_view(self):
        """
        Flask-Admin登录视图
        
        返回:
            Response: 响应对象
        """
        # 处理用户登录
        form = LoginForm(request.form)
        if admin_helpers.validate_form_on_submit(form):
            user = form.get_user()
            login.login_user(user)

        if login.current_user.is_authenticated:
            return redirect(url_for('.index'))
        self._template_args['form'] = form
        return super().index()

    @expose('/logout/')
    def logout_view(self):
        """
        登出视图
        
        返回:
            Response: 重定向到登录页面
        """
        login.logout_user()
        return redirect(url_for('.index'))


# 主页路由
home_routes = Blueprint('home', __name__)


@home_routes.route('/')
def index():
    """
    首页路由
    
    返回:
        Response: API文档页面
    """
    r = requests.get(
        'https://raw.githubusercontent.com/fossasia/open-event-server/gh-pages/api/v1/index.html'
    )
    response = make_response(r.content)
    response.headers["Content-Type"] = "text/html"
    return response


class BlueprintsManager:
    """
    蓝图管理器
    """
    
    def __init__(self):
        pass

    @staticmethod
    def register(app):
        """
        注册蓝图
        
        参数:
            app: Flask应用实例
            
        返回:
            None
        """
        # 注册主页路由
        app.register_blueprint(home_routes)
        
        # 创建Flask-Admin实例
        admin = Admin(
            app,
            name='Open Event API',
            template_mode='bootstrap3',
            index_view=MyAdminIndexView(),
            base_template='admin_base.html',
        )

        # 获取数据库中的所有模型，所有模型都应该有明确的__tablename__
        classes, models, table_names = [], [], []
        # noinspection PyProtectedMember
        for class_ in list(db.Model._decl_class_registry.values()):
            try:
                table_names.append(class_.__tablename__)
                classes.append(class_)
            except:
                pass
        for table in list(db.metadata.tables.items()):
            if table[0] in table_names:
                models.append(classes[table_names.index(table[0])])

        for model in models:
            admin.add_view(AdminModelView(model, db.session))
