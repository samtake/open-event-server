#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
认证API模块 - Open Event Server 用户认证和授权接口

此模块提供用户认证、授权和第三方登录功能，包括：
- 用户名/密码登录
- JWT令牌管理
- 第三方OAuth登录（Facebook, Google, Twitter, Instagram）
- 邮箱验证
- 密码重置

作者: FOSSASIA
"""

import base64
import logging
import random
import string
from datetime import timedelta
from functools import wraps

import requests
from flask import Blueprint, jsonify, make_response, request, send_file
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    current_user,
    fresh_jwt_required,
    get_jwt_identity,
    jwt_refresh_token_required,
    jwt_required,
    set_refresh_cookies,
    unset_jwt_cookies,
)
from healthcheck import EnvironmentDump
from sqlalchemy.orm.exc import NoResultFound

from app.api.helpers.auth import AuthManager, blacklist_token
from app.api.helpers.db import get_count, save_to_db
from app.api.helpers.errors import (
    BadRequestError,
    NotFoundError,
    UnprocessableEntityError,
)
from app.api.helpers.files import make_frontend_url
from app.api.helpers.jwt import jwt_authenticate
from app.api.helpers.mail import (
    send_email_confirmation,
    send_password_change_email,
    send_password_reset_email,
)
from app.api.helpers.third_party_auth import (
    FbOAuth,
    GoogleOAuth,
    InstagramOAuth,
    TwitterOAuth,
)
from app.api.helpers.utilities import get_serializer, str_generator
from app.extensions.limiter import limiter
from app.models import db
from app.models.user import User

# 日志记录器
logger = logging.getLogger(__name__)

# 认证相关蓝图
authorised_blueprint = Blueprint('authorised_blueprint', __name__, url_prefix='/')
auth_routes = Blueprint('auth', __name__, url_prefix='/v1/auth')


def authenticate(allow_refresh_token=False, existing_identity=None):
    """
    用户认证函数
    
    处理用户名/密码认证，支持JWT令牌生成和刷新令牌。
    
    参数:
        allow_refresh_token (bool): 是否允许生成刷新令牌
        existing_identity: 现有用户身份（用于新鲜登录验证）
        
    返回:
        Response: JSON响应，包含访问令牌和可选的刷新令牌
    """
    # 获取请求数据
    data = request.get_json()
    username = data.get('email', data.get('username'))
    password = data.get('password')
    criterion = [username, password]

    # 验证必要参数
    if not all(criterion):
        logging.error('用户名或密码缺失')
        return jsonify(error='用户名或密码缺失'), 400

    # 执行JWT认证
    identity = jwt_authenticate(username, password)

    # 验证认证结果
    if not identity or (existing_identity and identity != existing_identity):
        # 新鲜登录时，凭据应与现有用户匹配
        logging.error('无效凭据')
        return jsonify(error='无效凭据'), 401

    # 检查用户是否被屏蔽
    if identity.is_blocked:
        logging.info('管理员已将此账户标记为垃圾账户')
        return jsonify(error='管理员已将此账户标记为垃圾账户'), 401

    # 处理记住我选项
    remember_me = data.get('remember-me')
    include_in_response = data.get('include-in-response')
    add_refresh_token = allow_refresh_token and remember_me

    # 设置令牌过期时间
    expiry_time = timedelta(minutes=90) if add_refresh_token else None
    access_token = create_access_token(identity.id, fresh=True, expires_delta=expiry_time)
    response_data = {'access_token': access_token}

    # 生成刷新令牌（如果需要）
    if add_refresh_token:
        refresh_token = create_refresh_token(identity.id)
        if include_in_response:
            response_data['refresh_token'] = refresh_token

    response = jsonify(response_data)

    # 设置刷新令牌cookie（如果不包含在响应中）
    if add_refresh_token and not include_in_response:
        set_refresh_cookies(response, refresh_token)

    return response


@authorised_blueprint.route('/auth/session', methods=['POST'])
@auth_routes.route('/login', methods=['POST'])
def login():
    """
    用户登录端点
    
    提供标准的用户名/密码登录功能，支持刷新令牌。
    
    方法: POST
    
    请求体:
        {
            "email": "user@example.com",
            "password": "password123",
            "remember-me": true
        }
        
    返回:
        JSON响应，包含访问令牌和刷新令牌（如果remember-me为true）
    """
    return authenticate(allow_refresh_token=True)


@auth_routes.route('/fresh-login', methods=['POST'])
@jwt_required
def fresh_login():
    """
    新鲜登录端点
    
    要求用户重新输入凭据以获取新鲜令牌。
    
    方法: POST
    需要: JWT认证
    
    返回:
        JSON响应，包含新鲜访问令牌
    """
    return authenticate(existing_identity=current_user)


@auth_routes.route('/token/refresh', methods=['POST'])
@jwt_refresh_token_required
def refresh_token():
    """
    令牌刷新端点
    
    使用刷新令牌获取新的访问令牌。
    
    方法: POST
    需要: 刷新令牌
    
    返回:
        JSON响应，包含新的访问令牌
    """
    current_user = get_jwt_identity()
    expiry_time = timedelta(minutes=90)
    new_token = create_access_token(
        identity=current_user, fresh=False, expires_delta=expiry_time
    )
    return jsonify({'access_token': new_token})


@auth_routes.route('/logout', methods=['POST'])
def logout():
    """
    用户登出端点
    
    清除JWT令牌cookie。
    
    方法: POST
    
    返回:
        JSON响应，表示登出成功
    """
    response = jsonify({'success': True})
    unset_jwt_cookies(response)
    return response


@auth_routes.route('/blacklist', methods=['POST'])
@jwt_required
def blacklist_token_rquest():
    """
    令牌加入黑名单端点
    
    将当前用户的刷新令牌加入黑名单。
    
    方法: POST
    需要: JWT认证
    
    返回:
        JSON响应，表示操作成功
    """
    blacklist_token(current_user)
    return jsonify({'success': True})


@auth_routes.route('/oauth/<provider>', methods=['GET'])
def redirect_uri(provider):
    """
    获取OAuth重定向URI
    
    生成第三方OAuth提供商的授权URL。
    
    方法: GET
    
    参数:
        provider (str): 提供商名称 (facebook, google, twitter, instagram)
        
    返回:
        JSON响应，包含授权URL
    """
    # 根据提供商选择对应的OAuth类
    if provider == 'facebook':
        provider_class = FbOAuth()
    elif provider == 'google':
        provider_class = GoogleOAuth()
    elif provider == 'twitter':
        provider_class = TwitterOAuth()
    elif provider == 'instagram':
        provider_class = InstagramOAuth()
    else:
        return make_response(jsonify(message=f"不支持 {provider}"), 404)

    # 获取客户端ID
    client_id = provider_class.get_client_id()
    if not client_id:
        return make_response(
            jsonify(message=f"服务器上未配置{provider}客户端ID"),
            404,
        )

    # 构建授权URL
    url = (
        provider_class.get_auth_uri()
        + '?client_id='
        + client_id
        + '&redirect_uri='
        + provider_class.get_redirect_uri()
    )
    return make_response(jsonify(url=url), 200)


@auth_routes.route('/oauth/token/<provider>', methods=['GET'])
def get_token(provider):
    """
    获取OAuth访问令牌
    
    从第三方提供商获取访问令牌。
    
    方法: GET
    
    参数:
        provider (str): 提供商名称
        
    返回:
        JSON响应，包含访问令牌
    """
    if provider == 'facebook':
        provider_class = FbOAuth()
        payload = {
            'grant_type': 'client_credentials',
            'client_id': provider_class.get_client_id(),
            'client_secret': provider_class.get_client_secret(),
        }
    elif provider == 'google':
        provider_class = GoogleOAuth()
        payload = {
            'client_id': provider_class.get_client_id(),
            'client_secret': provider_class.get_client_secret(),
        }
    elif provider == 'twitter':
        provider_class = TwitterOAuth()
        payload = {
            'client_id': provider_class.get_client_id(),
            'client_secret': provider_class.get_client_secret(),
        }
    elif provider == 'instagram':
        provider_class = InstagramOAuth()
        payload = {
            'client_id': provider_class.get_client_id(),
            'client_secret': provider_class.get_client_secret(),
        }
    else:
        return make_response(jsonify(message=f"不支持 {provider}"), 200)
    response = requests.post(provider_class.get_token_uri(), params=payload)
    return make_response(jsonify(token=response.json()), 200)


@auth_routes.route('/oauth/login/<provider>', methods=['POST'])
def login_user(provider):
    """
    第三方OAuth登录
    
    处理第三方提供商的OAuth登录流程。
    
    方法: POST
    
    参数:
        provider (str): 提供商名称
        
    返回:
        JSON响应，包含用户信息和OAuth哈希
    """
    if provider == 'facebook':
        provider_class = FbOAuth()
        payload = {
            'client_id': provider_class.get_client_id(),
            'redirect_uri': provider_class.get_redirect_uri(),
            'client_secret': provider_class.get_client_secret(),
            'code': request.args.get('code'),
        }
        if not payload['client_id'] or not payload['client_secret']:
            raise NotImplementedError({'source': ''}, 'Facebook登录未配置')
        access_token = requests.get(
            'https://graph.facebook.com/v3.0/oauth/access_token', params=payload
        ).json()
        payload_details = {
            'input_token': access_token['access_token'],
            'access_token': provider_class.get_client_id()
            + '|'
            + provider_class.get_client_secret(),
        }
        details = requests.get(
            'https://graph.facebook.com/debug_token', params=payload_details
        ).json()
        user_details = requests.get(
            'https://graph.facebook.com/v3.0/' + details['data']['user_id'],
            params={
                'access_token': access_token['access_token'],
                'fields': 'first_name, last_name, email',
            },
        ).json()

        # 检查用户是否已存在
        if get_count(db.session.query(User).filter_by(email=user_details['email'])) > 0:
            user = db.session.query(User).filter_by(email=user_details['email']).one()
            if not user.facebook_id:
                user.facebook_id = user_details['id']
                user.facebook_login_hash = random.getrandbits(128)
                save_to_db(user)
            return make_response(
                jsonify(
                    user_id=user.id, email=user.email, oauth_hash=user.facebook_login_hash
                ),
                200,
            )

        # 创建新用户
        user = User()
        user.first_name = user_details['first_name']
        user.last_name = user_details['last_name']
        user.facebook_id = user_details['id']
        user.facebook_login_hash = random.getrandbits(128)
        user.password = ''.join(
            random.SystemRandom().choice(string.ascii_uppercase + string.digits)
            for _ in range(8)
        )
        if user_details['email']:
            user.email = user_details['email']

        save_to_db(user)
        return make_response(
            jsonify(
                user_id=user.id, email=user.email, oauth_hash=user.facebook_login_hash
            ),
            200,
        )

    if provider == 'google':
        provider_class = GoogleOAuth()
        payload = {
            'client_id': provider_class.get_client_id(),
            'client_secret': provider_class.get_client_secret(),
        }
    elif provider == 'twitter':
        provider_class = TwitterOAuth()
        payload = {
            'client_id': provider_class.get_client_id(),
            'client_secret': provider_class.get_client_secret(),
        }
    elif provider == 'instagram':
        provider_class = InstagramOAuth()
        payload = {
            'client_id': provider_class.get_client_id(),
            'client_secret': provider_class.get_client_secret(),
        }
    else:
        return make_response(jsonify(message=f"不支持 {provider}"), 200)
    response = requests.post(provider_class.get_token_uri(), params=payload)
    return make_response(jsonify(token=response.json()), 200)


@auth_routes.route('/verify-email', methods=['POST'])
def verify_email():
    """
    邮箱验证端点
    
    验证用户的邮箱地址。
    
    方法: POST
    
    请求体:
        {
            "data": {
                "token": "base64编码的验证令牌"
            }
        }
        
    返回:
        JSON响应，表示验证成功
    """
    try:
        # 解码验证令牌
        token = base64.b64decode(request.json['data']['token'])
    except base64.binascii.Error:
        logging.error('无效令牌')
        raise BadRequestError({'source': ''}, '无效令牌')
    
    # 获取序列化器
    s = get_serializer()

    try:
        # 解析令牌数据
        data = s.loads(token)
    except Exception:
        logging.error('无效令牌')
        raise BadRequestError({'source': ''}, '无效令牌')

    try:
        # 查找用户
        user = User.query.filter_by(email=data[0]).one()
    except Exception:
        logging.error('无效令牌')
        raise BadRequestError({'source': ''}, '无效令牌')
    else:
        # 标记邮箱为已验证
        user.is_verified = True
        save_to_db(user)
        logging.info('邮箱已验证')
        return make_response(jsonify(message="邮箱已验证"), 200)


@auth_routes.route('/resend-verification-email', methods=['POST'])
def resend_verification_email():
    """
    重新发送验证邮件端点
    
    重新发送邮箱验证邮件给用户。
    
    方法: POST
    
    请求体:
        {
            "data": {
                "email": "user@example.com"
            }
        }
        
    返回:
        JSON响应，表示验证邮件已重新发送
    """
    try:
        email = request.json['data']['email']
    except TypeError:
        logging.error('错误请求')
        raise BadRequestError({'source': ''}, '错误请求')

    try:
        # 查找用户
        user = User.query.filter_by(email=email).one()
    except NoResultFound:
        logging.info('未找到邮箱为 %s 的用户。', email)
        raise UnprocessableEntityError(
            {'source': ''}, '未找到邮箱为 ' + email + ' 的用户。'
        )
    else:
        # 生成新的验证令牌
        serializer = get_serializer()
        hash_ = str(
            base64.b64encode(
                str(serializer.dumps([user.email, str_generator()])).encode()
            ),
            'utf-8',
        )
        link = make_frontend_url('/verify', {'token': hash_})
        # 发送验证邮件
        send_email_confirmation(user.email, link)
        logging.info('验证邮件已重新发送')
        return make_response(jsonify(message="验证邮件已重新发送"), 200)


@auth_routes.route('/reset-password', methods=['POST'])
@limiter.limit(
    '3/hour',
    key_func=lambda: request.json['data']['email'],
    error_message='Limit for this action exceeded',
)
@limiter.limit('1/minute', error_message='Limit for this action exceeded')
def reset_password_post():
    """
    重置密码请求端点
    
    发送密码重置邮件给用户。
    
    方法: POST
    
    请求体:
        {
            "data": {
                "email": "user@example.com"
            }
        }
        
    返回:
        JSON响应，表示重置邮件已发送
    """
    try:
        email = request.json['data']['email']
    except TypeError:
        logging.error('错误请求')
        raise BadRequestError({'source': ''}, '错误请求')

    try:
        # 查找用户
        user = User.query.filter_by(email=email).one()
    except NoResultFound:
        logging.info('尝试重置不存在邮箱 %s 的密码', email)
    else:
        # 发送密码重置邮件
        send_password_reset_email(user)

    return make_response(
        jsonify(
            message="如果您的邮箱已注册，您将很快收到包含重置链接的邮件",
            email=email,
        ),
        200,
    )


@auth_routes.route('/reset-password', methods=['PATCH'])
def reset_password_patch():
    """
    重置密码确认端点
    
    使用重置令牌设置新密码。
    
    方法: PATCH
    
    请求体:
        {
            "data": {
                "token": "重置令牌",
                "password": "新密码"
            }
        }
        
    返回:
        JSON响应，包含用户信息
    """
    token = request.json['data']['token']
    password = request.json['data']['password']

    try:
        # 查找用户
        user = User.query.filter_by(reset_password=token).one()
    except NoResultFound:
        logging.info('用户未找到')
        raise NotFoundError({'source': ''}, '用户未找到')
    else:
        # 设置新密码
        user.password = password
        # 如果用户未验证，标记为已验证
        if not user.is_verified:
            user.is_verified = True
        save_to_db(user)

    return jsonify(
        {
            "id": user.id,
            "email": user.email,
            "name": user.fullname if user.fullname else None,
        }
    )


@auth_routes.route('/change-password', methods=['POST'])
@fresh_jwt_required
def change_password():
    """
    修改密码端点
    
    允许已认证用户修改密码。
    
    方法: POST
    需要: 新鲜JWT令牌
    
    请求体:
        {
            "data": {
                "old-password": "旧密码",
                "new-password": "新密码"
            }
        }
        
    返回:
        JSON响应，包含用户信息
    """
    old_password = request.json['data']['old-password']
    new_password = request.json['data']['new-password']

    try:
        # 查找当前用户
        user = User.query.filter_by(id=current_user.id).one()
    except NoResultFound:
        logging.info('用户未找到')
        raise NotFoundError({'source': ''}, '用户未找到')
    else:
        # 验证旧密码
        if user.is_correct_password(old_password):
            # 检查新密码是否与旧密码不同
            if user.is_correct_password(new_password):
                logging.error('新旧密码必须不同')
                raise BadRequestError(
                    {'source': ''}, '新旧密码必须不同'
                )
            # 检查密码长度
            if len(new_password) < 8:
                logging.error('密码至少需要8个字符')
                raise BadRequestError(
                    {'source': ''}, '密码至少需要8个字符'
                )
            # 设置新密码
            user.password = new_password
            save_to_db(user)
            # 发送密码修改通知邮件
            send_password_change_email(user)
        else:
            logging.error('密码错误，请输入正确的当前密码')
            raise BadRequestError(
                {'source': ''}, '密码错误，请输入正确的当前密码'
            )

    return jsonify(
        {
            "id": user.id,
            "email": user.email,
            "name": user.fullname if user.fullname else None,
            "password-changed": True,
        }
    )


def return_file(file_name_prefix, file_path, identifier):
    """
    返回文件响应
    
    生成带有正确文件名的文件下载响应。
    
    参数:
        file_name_prefix (str): 文件名前缀
        file_path (str): 文件路径
        identifier: 标识符
        
    返回:
        Response: 文件下载响应
    """
    response = make_response(send_file(file_path))
    response.headers['Content-Disposition'] = 'attachment; filename={}-{}.pdf'.format(
        file_name_prefix,
        identifier,
    )
    return response


# 环境详情访问和基本认证支持
def requires_basic_auth(f):
    """
    基本认证装饰器
    
    要求请求提供基本认证凭据。
    
    参数:
        f: 被装饰的函数
        
    返回:
        装饰后的函数
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not AuthManager.check_auth_admin(auth.username, auth.password):
            return make_response(
                '无法验证您对该URL的访问级别。\n'
                '您必须使用正确的凭据登录',
                401,
                {'WWW-Authenticate': 'Basic realm="Login Required"'},
            )
        return f(*args, **kwargs)

    return decorated


@authorised_blueprint.route('/environment')
@requires_basic_auth
def environment_details():
    """
    环境详情端点
    
    返回应用程序的环境详情。
    
    方法: GET
    需要: 基本认证
    
    返回:
        环境详情
    """
    envdump = EnvironmentDump(include_config=False)
    return envdump.dump_environment()


@auth_routes.route('/verify-password', methods=['POST'])
@jwt_required
def verify_password():
    """
    验证密码端点
    
    验证用户提供的密码是否正确。
    
    方法: POST
    需要: JWT认证
    
    请求体:
        {
            "password": "要验证的密码"
        }
        
    返回:
        JSON响应，包含验证结果
    """
    data = request.get_json()
    password = data.get('password')

    if not all([current_user.id, password]):
        logging.error('用户或密码缺失')
        return jsonify(error='用户或密码缺失'), 400

    try:
        # 查找用户
        user = User.query.filter_by(id=current_user.id).one()
    except NoResultFound:
        logging.info('用户未找到')
        raise NotFoundError({'source': ''}, '用户未找到')

    # 验证密码
    result = False
    if user.is_correct_password(password):
        result = True

    return jsonify(
        {
            "result": result,
        }
    )
