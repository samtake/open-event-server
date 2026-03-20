import logging
from datetime import datetime

from flask import Blueprint, abort, jsonify, make_response, request
from flask_jwt_extended import current_user, verify_fresh_jwt_in_request
from flask_rest_jsonapi import ResourceDetail, ResourceList, ResourceRelationship
from sqlalchemy import or_
from sqlalchemy.orm.exc import NoResultFound

from app.api.bootstrap import api
from app.api.helpers.db import get_count, safe_query_by, safe_query_kwargs
from app.api.helpers.errors import ConflictError, ForbiddenError, UnprocessableEntityError
from app.api.helpers.mail import send_email_change_user_email, send_user_register_email
from app.api.helpers.permission_manager import has_access
from app.api.helpers.permissions import is_user_itself
from app.api.helpers.user import (
    modify_email_for_user_to_be_deleted,
    modify_email_for_user_to_be_restored,
)
from app.api.schema.users import UserSchema, UserSchemaPublic
from app.models import db
from app.models.access_code import AccessCode
from app.models.discount_code import DiscountCode
from app.models.email_notification import EmailNotification
from app.models.event import Event
from app.models.event_invoice import EventInvoice
from app.models.feedback import Feedback
from app.models.group import Group
from app.models.notification import Notification
from app.models.order import Order
from app.models.session import Session
from app.models.speaker import Speaker
from app.models.ticket_holder import TicketHolder
from app.models.user import User
from app.models.user_follow_group import UserFollowGroup
from app.models.users_events_role import UsersEventsRoles
from app.models.video_stream_moderator import VideoStreamModerator

logger = logging.getLogger(__name__)

user_misc_routes = Blueprint('user_misc', __name__, url_prefix='/v1')


class UserList(ResourceList):
    """
    用户列表和创建类
    """

    def before_create_object(self, data, view_kwargs):
        """
        创建对象前的检查方法，用于检查是否存在与新用户相同邮箱的现有用户
        以及密码是否至少8个字符长
        :param data: 数据
        :param view_kwargs: 视图关键字参数
        :return:
        """
        # 检查密码长度是否至少8个字符
        if len(data['password']) < 8:
            logging.error('密码应至少8个字符长')
            raise UnprocessableEntityError(
                {'source': '/data/attributes/password'},
                '密码应至少8个字符长',
            )
        # 检查邮箱是否已存在
        if (
            db.session.query(User.id).filter_by(email=data['email'].strip()).scalar()
            is not None
        ):
            logging.error('邮箱已存在')
            raise ConflictError(
                {'pointer': '/data/attributes/email'}, "邮箱已存在"
            )

        # 不允许用户直接设置验证状态
        if data.get('is_verified'):
            logging.error("您不允许提交此字段")
            raise UnprocessableEntityError(
                {'pointer': '/data/attributes/is-verified'},
                "您不允许提交此字段",
            )

    def after_create_object(self, user, data, view_kwargs):
        """
        创建对象后的方法，用于发送：
        - 邮件通知
        - 注册验证邮件链接
        - 添加图片URL
        :param user: 用户对象
        :param data: 数据
        :param view_kwargs: 视图关键字参数
        :return:
        """

        # 发送用户注册邮件
        send_user_register_email(user)
        # TODO 在celery任务中处理
        # if data.get('original_image_url'):
        #     try:
        #         uploaded_images = create_save_image_sizes(data['original_image_url'], 'speaker-image', user.id)
        #     except (urllib.error.HTTPError, urllib.error.URLError):
        #         raise UnprocessableEntityError(
        #             {'source': 'attributes/original-image-url'}, '图片URL无效'
        #         )
        #     uploaded_images['small_image_url'] = uploaded_images['thumbnail_image_url']
        #     del uploaded_images['large_image_url']
        #     self.session.query(User).filter_by(id=user.id).update(uploaded_images)

        # 如果提供了头像URL，则开始图片调整任务
        if data.get('avatar_url'):
            start_image_resizing_tasks(user, data['avatar_url'])

    # 权限装饰器，只有管理员才能执行GET方法
    decorators = (api.has_permission('is_admin', methods="GET"),)
    schema = UserSchema
    data_layer = {
        'session': db.session,
        'model': User,
        'methods': {
            'before_create_object': before_create_object,
            'after_create_object': after_create_object,
        },
    }


class UserDetail(ResourceDetail):
    """
    User detail by id
    """

    def before_get(self, args, kwargs):
        if current_user.is_admin or current_user.is_super_admin or current_user:
            self.schema = UserSchema
        else:
            self.schema = UserSchemaPublic

    def before_get_object(self, view_kwargs):
        """
        before get method for user object
        :param view_kwargs:
        :return:
        """
        if view_kwargs.get('notification_id') is not None:
            notification = safe_query_kwargs(
                Notification,
                view_kwargs,
                'notification_id',
            )
            if notification.user_id is not None:
                view_kwargs['id'] = notification.user_id
            else:
                view_kwargs['id'] = None

        if view_kwargs.get('feedback_id') is not None:
            feedback = safe_query_kwargs(Feedback, view_kwargs, 'feedback_id')
            if feedback.user_id is not None:
                view_kwargs['id'] = feedback.user_id
            else:
                view_kwargs['id'] = None

        if view_kwargs.get('attendee_id') is not None:
            attendee = safe_query_kwargs(TicketHolder, view_kwargs, 'attendee_id')
            if attendee.user is not None:
                if not has_access(
                    'is_user_itself', user_id=attendee.user.id
                ) or not has_access('is_coorganizer', event_id=attendee.event_id):
                    raise ForbiddenError({'source': ''}, 'Access Forbidden')
                view_kwargs['id'] = attendee.user.id
            else:
                view_kwargs['id'] = None

        if view_kwargs.get('event_invoice_id') is not None:
            event_invoice = safe_query_kwargs(
                EventInvoice,
                view_kwargs,
                'event_invoice_id',
            )
            if event_invoice.user_id is not None:
                view_kwargs['id'] = event_invoice.user_id
            else:
                view_kwargs['id'] = None

        if view_kwargs.get('event_invoice_identifier') is not None:
            event_invoice = safe_query_kwargs(
                EventInvoice, view_kwargs, 'event_invoice_identifier', 'identifier'
            )
            if event_invoice.user_id is not None:
                view_kwargs['id'] = event_invoice.user_id
            else:
                view_kwargs['id'] = None

        if view_kwargs.get('users_events_role_id') is not None:
            users_events_role = safe_query_kwargs(
                UsersEventsRoles,
                view_kwargs,
                'users_events_role_id',
            )
            if users_events_role.user_id is not None:
                view_kwargs['id'] = users_events_role.user_id
            else:
                view_kwargs['id'] = None

        if view_kwargs.get('speaker_id') is not None:
            speaker = safe_query_kwargs(Speaker, view_kwargs, 'speaker_id')
            if speaker.user_id is not None:
                view_kwargs['id'] = speaker.user_id
            else:
                view_kwargs['id'] = None

        if view_kwargs.get('session_id') is not None:
            session = safe_query_kwargs(Session, view_kwargs, 'session_id')
            if session.creator_id is not None:
                view_kwargs['id'] = session.creator_id
            else:
                view_kwargs['id'] = None

        if view_kwargs.get('access_code_id') is not None:
            access_code = safe_query_kwargs(AccessCode, view_kwargs, 'access_code_id')
            if access_code.marketer_id is not None:
                view_kwargs['id'] = access_code.marketer_id
            else:
                view_kwargs['id'] = None

        if view_kwargs.get('event_id') is not None:
            event = safe_query_kwargs(Event, view_kwargs, 'event_id')
            if event.owner is not None:
                view_kwargs['id'] = event.owner.id
            else:
                view_kwargs['id'] = None

        if view_kwargs.get('group_id') is not None:
            group = safe_query_kwargs(Group, view_kwargs, 'group_id')
            if group.user_id is not None:
                view_kwargs['id'] = group.user_id
            else:
                view_kwargs['id'] = None

        if view_kwargs.get('discount_code_id') is not None:
            discount_code = safe_query_kwargs(
                DiscountCode,
                view_kwargs,
                'discount_code_id',
            )
            if discount_code.marketer_id is not None:
                view_kwargs['id'] = discount_code.marketer_id
            else:
                view_kwargs['id'] = None

        if view_kwargs.get('email_notification_id') is not None:
            email_notification = safe_query_kwargs(
                EmailNotification,
                view_kwargs,
                'email_notification_id',
            )
            if email_notification.user_id is not None:
                view_kwargs['id'] = email_notification.user_id
            else:
                view_kwargs['id'] = None

        if view_kwargs.get('video_stream_moderator_id') is not None:
            moderator = safe_query_kwargs(
                VideoStreamModerator,
                view_kwargs,
                'video_stream_moderator_id',
            )
            user = safe_query_by(User, moderator.email, param='email')
            if user is not None:
                view_kwargs['id'] = user.id
            else:
                view_kwargs['id'] = None

        if view_kwargs.get('user_follow_group_id') is not None:
            user_follow_group = safe_query_kwargs(
                UserFollowGroup, view_kwargs, 'user_follow_group_id'
            )
            if user_follow_group.id is not None:
                view_kwargs['id'] = user_follow_group.user_id
            else:
                view_kwargs['id'] = None

    def before_update_object(self, user, data, view_kwargs):
        # TODO: Make a celery task for this
        # if data.get('avatar_url') and data['original_image_url'] != user.original_image_url:
        #     try:
        #         uploaded_images = create_save_image_sizes(data['original_image_url'], 'speaker-image', user.id)
        #     except (urllib.error.HTTPError, urllib.error.URLError):
        #         raise UnprocessableEntityError(
        #             {'source': 'attributes/original-image-url'}, 'Invalid Image URL'
        #         )
        #     data['original_image_url'] = uploaded_images['original_image_url']
        #     data['small_image_url'] = uploaded_images['thumbnail_image_url']
        #     data['thumbnail_image_url'] = uploaded_images['thumbnail_image_url']
        #     data['icon_image_url'] = uploaded_images['icon_image_url']

        if data.get('deleted_at') != user.deleted_at:
            if has_access('is_user_itself', user_id=user.id) or has_access('is_admin'):
                if data.get('deleted_at'):
                    event_exists = db.session.query(
                        Event.query.filter_by(deleted_at=None)
                        .join(Event.users)
                        .filter(User.id == user.id)
                        .exists()
                    ).scalar()
                    if event_exists:
                        logging.error("Users associated with events cannot be deleted")
                        raise ForbiddenError(
                            {'source': ''},
                            "Users associated with events cannot be deleted",
                        )
                    # TODO(Areeb): Deduplicate the query. Present in video stream model as well
                    order_exists = db.session.query(
                        TicketHolder.query.filter_by(user=user)
                        .join(Order)
                        .join(Order.event)
                        .filter(Event.ends_at > datetime.now())
                        .filter(
                            or_(
                                Order.status == 'completed',
                                Order.status == 'placed',
                                Order.status == 'initializing',
                                Order.status == 'pending',
                            )
                        )
                        .exists()
                    ).scalar()
                    # If any pending or completed order exists, we cannot delete the user
                    if order_exists:
                        logger.warning(
                            'User %s has pending or completed orders, hence cannot be deleted',
                            user,
                        )
                        raise ForbiddenError(
                            {'source': ''},
                            "Users associated with orders cannot be deleted",
                        )
                    modify_email_for_user_to_be_deleted(user)
                else:
                    modify_email_for_user_to_be_restored(user)
                    data['email'] = user.email
                user.deleted_at = data.get('deleted_at')
            else:
                logging.info("You are not authorized to update this information.")
                raise ForbiddenError(
                    {'source': ''}, "You are not authorized to update this information."
                )

        if (
            not has_access('is_admin')
            and data.get('is_verified') is not None
            and data.get('is_verified') != user.is_verified
        ):
            logging.info("Admin access is required to update this information.")
            raise ForbiddenError(
                {'pointer': '/data/attributes/is-verified'},
                "Admin access is required to update this information.",
            )

        users_email = data.get('email', None)
        if users_email is not None:
            users_email = users_email.strip()

        if users_email is not None and users_email != user.email:
            try:
                db.session.query(User).filter_by(email=users_email).one()
            except NoResultFound:
                verify_fresh_jwt_in_request()
                view_kwargs['email_changed'] = user.email
            else:
                logging.error("Email already exists")
                raise ConflictError(
                    {'pointer': '/data/attributes/email'}, "Email already exists"
                )

        if (
            has_access('is_super_admin')
            and data.get('is_admin')
            and data.get('is_admin') != user.is_admin
        ):
            user.is_admin = not user.is_admin

        if (
            has_access('is_admin')
            and ('is_sales_admin' in data)
            and data.get('is_sales_admin') != user.is_sales_admin
        ):
            user.is_sales_admin = not user.is_sales_admin

        if (
            has_access('is_admin')
            and ('is_marketer' in data)
            and data.get('is_marketer') != user.is_marketer
        ):
            user.is_marketer = not user.is_marketer

        if data.get('avatar_url'):
            start_image_resizing_tasks(user, data['avatar_url'])

    def after_update_object(self, user, data, view_kwargs):
        """
        method to mail user about email change
        :param user:
        :param data:
        :param view_kwargs:
        :return:
        """
        if view_kwargs.get('email_changed'):
            send_email_change_user_email(user, view_kwargs.get('email_changed'))

    decorators = (
        api.has_permission(
            'is_user_itself',
            fetch="user_id,id",
            fetch_as="user_id",
            model=[
                Notification,
                Feedback,
                UsersEventsRoles,
                Session,
                EventInvoice,
                AccessCode,
                DiscountCode,
                EmailNotification,
                Speaker,
                User,
                UserFollowGroup,
                Group,
            ],
            fetch_key_url="notification_id, feedback_id, users_events_role_id, session_id, \
                  event_invoice_id, access_code_id, discount_code_id, email_notification_id, speaker_id, id, user_follow_group_id, group_id",
            leave_if=lambda a: a.get('attendee_id'),
        ),
    )
    schema = UserSchema
    data_layer = {
        'session': db.session,
        'model': User,
        'methods': {
            'before_get_object': before_get_object,
            'before_update_object': before_update_object,
            'after_update_object': after_update_object,
        },
    }


class UserRelationship(ResourceRelationship):
    """
    User Relationship
    """

    decorators = (is_user_itself,)
    schema = UserSchema
    data_layer = {'session': db.session, 'model': User}


@user_misc_routes.route('/users/check_email', methods=['POST'])
@user_misc_routes.route('/users/checkEmail', methods=['POST'])  # deprecated
def is_email_available():
    email = request.json.get('email', None)
    if email:
        if get_count(db.session.query(User).filter_by(deleted_at=None, email=email)):
            return jsonify(exists=True)
        return jsonify(exists=False)
    abort(make_response(jsonify(error="Email field missing"), 422))


def start_image_resizing_tasks(user, original_image_url):
    user_id = str(user.id)
    from .helpers.tasks import resize_user_images_task

    resize_user_images_task.delay(user_id, original_image_url)
