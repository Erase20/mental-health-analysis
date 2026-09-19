# =============================================================================
# auth.py — 认证模块 API（注册 / 登录 / Token刷新 / 登出 / 修改密码）
# =============================================================================
# 职责：处理用户身份认证相关的所有请求
# 路由前缀：/api/auth/xxx
# 认证方式：JWT（JSON Web Token），分 access_token 和 refresh_token 两种
# =============================================================================

# ---- Flask 核心 ----
from flask import Blueprint, request, jsonify        # Blueprint=蓝图(路由分组), request=请求对象, jsonify=JSON响应
# ---- JWT 认证 ----
from flask_jwt_extended import (
    create_access_token,      # 创建访问令牌（有效期24h，用于API鉴权）
    create_refresh_token,     # 创建刷新令牌（有效期30天，用于续期）
    jwt_required,             # 装饰器：标记路由需要JWT认证才能访问
    get_jwt_identity          # 从当前请求的JWT中提取用户身份（user_id）
)
# ---- 数据模型 & 数据库 ----
from app.models.user import User   # 用户模型（包含密码加密、角色等字段）
from app import db                 # SQLAlchemy 数据库实例（用于增删改查操作）
from sqlalchemy import or_         # SQL OR 查询（登录时支持用户名或邮箱查找）
# ---- 工具库 ----
import re                          # 正则表达式（用于邮箱格式校验）
from datetime import datetime      # 时间处理

# 创建认证蓝图，URL前缀 /api/auth（在 __init__.py 中注册时指定）
auth_bp = Blueprint('auth', __name__)

def validate_email(email):
    """验证邮箱格式是否合法
    
    使用正则表达式匹配标准邮箱格式：用户名@域名.后缀
    例：test@example.com ✓  |  test@com ✗
    """
    # 正则规则：允许字母/数字/点/百分号/加减号 作为用户名，域名至少两级
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None  # 匹配成功返回True

def validate_password(password):
    """验证密码强度
    
    当前规则：密码长度 >= 6位
    返回：(是否通过, 错误提示)
    """
    if len(password) < 6:
        return False, '密码长度至少6位'  # 不通过 + 错误信息
    return True, ''  # 通过 + 空信息

# ==========================================================================
# POST /api/auth/register — 用户注册
# ==========================================================================
# 流程：接收JSON → 校验必填 → 校验邮箱格式 → 校验密码 → 查重 → 创建用户 → 存库
# 返回：新用户的 id, username, email
# ==========================================================================
@auth_bp.route('/register', methods=['POST'])
def register():
    """用户注册"""
    try:
        # ① 解析请求体中的 JSON 数据
        data = request.get_json()
        
        # ② 验证必填字段（用户名、邮箱、密码缺一不可）
        if not data.get('username') or not data.get('email') or not data.get('password'):
            return jsonify({
                'code': 400,
                'message': '用户名、邮箱和密码不能为空',
                'data': None
            }), 400
        
        # ③ 去除首尾空格，防止用户误输入空格
        username = data['username'].strip()
        email = data['email'].strip()
        password = data['password']  # 密码不去空格（空格也可能是密码的一部分）
        
        # ④ 验证邮箱格式是否合法
        if not validate_email(email):
            return jsonify({
                'code': 400,
                'message': '邮箱格式不正确',
                'data': None
            }), 400
        
        # ⑤ 验证密码强度（至少6位）
        is_valid, msg = validate_password(password)
        if not is_valid:
            return jsonify({
                'code': 400,
                'message': msg,
                'data': None
            }), 400
        
        # ⑥ 检查用户名是否已被注册（数据库唯一性校验）
        if User.query.filter_by(username=username).first():
            return jsonify({
                'code': 400,
                'message': '用户名已存在',
                'data': None
            }), 400
        
        # ⑦ 检查邮箱是否已被注册（数据库唯一性校验）
        if User.query.filter_by(email=email).first():
            return jsonify({
                'code': 400,
                'message': '邮箱已被注册',
                'data': None
            }), 400
        
        # ⑧ 创建新用户对象（设置属性，尚未存入数据库）
        user = User(
            username=username,
            email=email,
            role='user',                             # 公开注册固定为普通用户，防止角色提升
            phone=data.get('phone'),                 # 手机号（可选）
            department=data.get('department')         # 部门（可选）
        )
        # ⑨ 调用 User 模型的 set_password() 方法，使用 bcrypt 加密密码
        user.set_password(password)
        
        # ⑩ 写入数据库
        db.session.add(user)      # 加入会话（相当于 INSERT INTO）
        db.session.commit()       # 提交事务（真正写入数据库）
        
        return jsonify({
            'code': 201,
            'message': '注册成功',
            'data': {
                'id': user.id,
                'username': user.username,
                'email': user.email
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()  # 发生异常时回滚事务，避免脏数据
        return jsonify({
            'code': 500,
            'message': f'注册失败: {str(e)}',
            'data': None
        }), 500

# ==========================================================================
# POST /api/auth/login — 用户登录
# ==========================================================================
# 流程：接收JSON → 查找用户(支持用户名或邮箱) → 验证密码 → 检查是否禁用 → 生成JWT Token
# 返回：access_token(24h) + refresh_token(30d) + 用户信息
# ==========================================================================
@auth_bp.route('/login', methods=['POST'])
def login():
    """用户登录
    
    支持用户名或邮箱登录，验证通过后生成 JWT Token 对返回给前端
    """
    try:
        # ① 解析 JSON 请求体
        data = request.get_json()
        
        # ② 校验必填字段
        if not data.get('username') or not data.get('password'):
            return jsonify({
                'code': 400,
                'message': '用户名和密码不能为空',
                'data': None
            }), 400
        
        username = data['username'].strip()
        password = data['password']
        
        # ③ 查找用户：使用 OR 查询，支持用户名或邮箱登录
        user = User.query.filter(
            or_(
                User.username == username,   # 按用户名查找
                User.email == username       # 按邮箱查找
            )
        ).first()
        
        # ④ 用户不存在（用户名/邮箱都找不到匹配）
        if not user:
            return jsonify({
                'code': 401,
                'message': '用户不存在',
                'data': None
            }), 401
        
        # ⑤ 密码校验：调用 User 模型的 check_password()，内部使用 bcrypt 比对哈希
        if not user.check_password(password):
            return jsonify({
                'code': 401,
                'message': '密码错误',
                'data': None
            }), 401
        
        # ⑥ 检查账号是否被管理员禁用
        if not user.is_active:
            return jsonify({
                'code': 401,
                'message': '账号已被禁用',
                'data': None
            }), 401
        
        # ⑦ 更新最后登录时间（记录用户活跃情况）
        user.update_last_login()
        
        # ⑧ 生成 JWT Token 对
        # access_token: 访问令牌，有效期24小时，每次请求时携带
        # refresh_token: 刷新令牌，有效期30天，access_token过期后用它换新的
        access_token = create_access_token(
            identity=str(user.id),        # JWT中存储用户ID（identity是JWT的标识）
            additional_claims={            # 额外声明：存入用户名和角色（便于权限判断）
                'username': user.username,
                'role': user.role
            }
        )
        refresh_token = create_refresh_token(identity=str(user.id))  # 刷新令牌只存user_id
        
        return jsonify({
            'code': 200,
            'message': '登录成功',
            'data': {
                'access_token': access_token,   # 访问令牌（前端每次请求携带）
                'refresh_token': refresh_token,  # 刷新令牌（用于续期access_token）
                'token_type': 'Bearer',          # 令牌类型：Bearer（请求头格式：Authorization: Bearer xxx）
                'expires_in': 86400,             # 过期时间：24小时（单位：秒）
                'user': user.to_dict()           # 用户信息（调用to_dict()隐藏密码字段）
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'登录失败: {str(e)}',
            'data': None
        }), 500

# ==========================================================================
# POST /api/auth/refresh — 刷新 Token
# ==========================================================================
# 前置条件：请求头必须携带有效的 refresh_token
# @jwt_required(refresh=True) 表示只接受 refresh_token，不接受 access_token
# ==========================================================================
@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)   # 只接受 refresh_token 的请求
def refresh():
    """刷新Token
    
    当 access_token 过期时，前端用 refresh_token 调用此接口换取新的 access_token，
    这样用户无需重新登录就能继续使用系统
    """
    try:
        # ① 从 refresh_token 中提取用户 ID
        current_user_id = get_jwt_identity()
        # ② 查询用户是否还存在且未被禁用
        user = User.query.get(current_user_id)
        
        # ③ 安全检查：用户不存在或已被禁用，拒绝刷新
        if not user or not user.is_active:
            return jsonify({
                'code': 401,
                'message': '用户不存在或已被禁用',
                'data': None
            }), 401
        
        # ④ 生成新的 access_token（带有用户名和角色信息）
        new_token = create_access_token(
            identity=user.id,        # JWT身份标识 = 用户ID
            additional_claims={      # 额外信息：用户名和角色
                'username': user.username,
                'role': user.role
            }
        )
        
        return jsonify({
            'code': 200,
            'message': 'Token刷新成功',
            'data': {
                'access_token': new_token,   # 新的访问令牌
                'token_type': 'Bearer',       # 令牌类型
                'expires_in': 86400           # 有效期：24小时
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'刷新失败: {str(e)}',
            'data': None
        }), 500

# ==========================================================================
# POST /api/auth/logout — 用户登出
# ==========================================================================
# 注意：JWT 是无状态的，服务器不保存 token，所以这里只是返回成功消息
# 实际登出操作由前端完成：删除 localStorage/Cookie 中的 token
# ==========================================================================
@auth_bp.route('/logout', methods=['POST'])
@jwt_required()   # 需要携带有效的 access_token
def logout():
    """用户登出
    
    JWT是无状态的，服务器不维护会话，
    所以只需前端删除本地存储的token即可实现登出
    """
    # JWT无状态，客户端删除token即可
    return jsonify({
        'code': 200,
        'message': '登出成功',
        'data': None
    }), 200

# ==========================================================================
# GET /api/auth/profile — 获取当前登录用户的信息
# ==========================================================================
# 需要登录，从 JWT 中提取 user_id，然后查询数据库返回用户详情
# ==========================================================================
@auth_bp.route('/profile', methods=['GET'])
@jwt_required()   # 需要登录状态
def get_profile():
    """获取当前用户信息
    
    从 JWT Token 中解析出 user_id，然后查库返回用户完整信息
    """
    try:
        # ① 从 JWT Token 中提取当前登录用户的 ID
        current_user_id = get_jwt_identity()
        # ② 根据 ID 查询用户
        user = User.query.get(current_user_id)
        
        # ③ 用户不存在（可能已被管理员删除）
        if not user:
            return jsonify({
                'code': 404,
                'message': '用户不存在',
                'data': None
            }), 404
        
        # ④ 返回用户信息（to_dict() 会隐藏密码哈希等敏感字段）
        return jsonify({
            'code': 200,
            'message': '获取成功',
            'data': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取失败: {str(e)}',
            'data': None
        }), 500

@auth_bp.route('/password', methods=['PUT'])
@jwt_required()   # 需要登录状态
def change_password():
    """修改密码
    
    流程：验证旧密码 → 校验新密码强度 → bcrypt加密新密码 → 提交数据库
    """
    try:
        # ① 从 JWT 获取当前登录用户
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        # ② 用户不存在检查
        if not user:
            return jsonify({
                'code': 404,
                'message': '用户不存在',
                'data': None
            }), 404
        
        # ③ 解析请求体
        data = request.get_json()
        old_password = data.get('old_password')   # 原密码（用于验证身份）
        new_password = data.get('new_password')   # 新密码（将要设置）
        
        # ④ 必填校验
        if not old_password or not new_password:
            return jsonify({
                'code': 400,
                'message': '原密码和新密码不能为空',
                'data': None
            }), 400
        
        # ⑤ 验证旧密码是否正确（防止他人偷改密码）
        if not user.check_password(old_password):
            return jsonify({
                'code': 400,
                'message': '原密码错误',
                'data': None
            }), 400
        
        # ⑥ 校验新密码强度（至少6位）
        is_valid, msg = validate_password(new_password)
        if not is_valid:
            return jsonify({
                'code': 400,
                'message': msg,
                'data': None
            }), 400
        
        # ⑦ 使用 bcrypt 加密新密码并存入用户对象
        user.set_password(new_password)
        # ⑧ 提交到数据库
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': '密码修改成功',
            'data': None
        }), 200
        
    except Exception as e:
        db.session.rollback()  # 出错时回滚数据库事务
        return jsonify({
            'code': 500,
            'message': f'修改失败: {str(e)}',
            'data': None
        }), 500

# ==========================================================================
# GET /api/auth/info — 获取当前用户信息（与 /profile 功能相同，兼容不同前端调用）
# ==========================================================================
@auth_bp.route('/info', methods=['GET'])
@jwt_required()   # 需要登录状态
def get_info():
    """获取当前用户信息
    
    与 /profile 接口功能完全相同，是为了兼容不同前端页面调用而提供的冗余接口
    """
    try:
        # ① 从 JWT 中提取当前用户 ID
        current_user_id = get_jwt_identity()
        # ② 查询数据库
        user = User.query.get(current_user_id)
        
        # ③ 用户不存在
        if not user:
            return jsonify({
                'code': 404,
                'message': '用户不存在',
                'data': None
            }), 404
        
        # ④ 返回用户信息（to_dict() 会隐藏密码哈希等敏感字段）
        return jsonify({
            'code': 200,
            'message': '获取成功',
            'data': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取失败: {str(e)}',
            'data': None
        }), 500
