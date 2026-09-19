from functools import wraps

from flask import g, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required

from app import db
from app.models.user import User


def permission_required(*allowed_roles):
    """统一的登录与角色校验装饰器。

    学习重点：
    1. 不直接相信 JWT 里的 role，而是用 JWT 中的 user_id 再查数据库。
       这样管理员修改角色或禁用账号后，旧 Token 不会继续保留权限。
    2. 不传 allowed_roles 表示“登录即可访问”；
       传入角色列表表示“必须属于其中一种角色”。
    """

    def decorator(view_func):
        @wraps(view_func)
        @jwt_required()
        def wrapper(*args, **kwargs):
            # JWT identity 统一保存为用户 ID。
            try:
                user_id = int(get_jwt_identity())
            except (TypeError, ValueError):
                return jsonify({
                    'code': 401,
                    'message': '无效的用户身份',
                    'data': None
                }), 401

            # 每次都读取当前数据库状态，避免依赖过期的 JWT 角色声明。
            user = db.session.get(User, user_id)
            if not user or not user.is_active:
                return jsonify({
                    'code': 401,
                    'message': '用户不存在或已被禁用',
                    'data': None
                }), 401

            # 403 表示“已经登录，但角色不允许访问”。
            if allowed_roles and user.role not in allowed_roles:
                return jsonify({
                    'code': 403,
                    'message': '无权限访问该资源',
                    'data': None
                }), 403

            # 把当前用户放入请求上下文，业务函数可通过 g.current_user 获取。
            g.current_user = user
            return view_func(*args, **kwargs)

        return wrapper

    return decorator


auth_required = permission_required()


def roles_required(*allowed_roles):
    """只允许指定角色访问。

    用法：
        @roles_required('admin', 'analyst')
    """
    return permission_required(*allowed_roles)
