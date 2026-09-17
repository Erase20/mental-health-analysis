# =============================================================================
# user.py — 用户画像 & 账号管理模块 API
# =============================================================================
# 职责：
#   1. 用户画像：列表/详情/搜索/相似/标签/统计
#   2. 自评功能：填写特征值查看画像和风险
#   3. 自评记录：列表/详情/统计
#   4. 账号管理：管理员查看/删除/启用禁用用户
# 路由前缀：/api/user/xxx
# =============================================================================

# ---- Flask 核心 ----
from flask import Blueprint, request, jsonify
# ---- JWT 认证 ----
from flask_jwt_extended import jwt_required, get_jwt_identity  # 所有接口需登录
# ---- 业务层 ----
from app.services.profile_service import ProfileService             # 画像服务（CRUD/自评/搜索）
from app.services.visualization_service import VisualizationService  # 可视化服务（画像详情数据）

# 创建用户画像蓝图，URL前缀 /api/user
user_bp = Blueprint('user', __name__)

# ==========================================================================
# GET /api/user/profiles — 获取用户画像列表（分页 + 筛选）
# ==========================================================================
@user_bp.route('/profiles', methods=['GET'])
@jwt_required()   # 需要登录
def get_profiles():
    """获取用户画像列表
    
    支持分页和筛选（风险等级、聚类群体ID）
    """
    try:
        # 分页参数
        page = request.args.get('page', 1, type=int)          # 当前页码
        per_page = request.args.get('per_page', 20, type=int)  # 每页条数
        # 筛选参数
        risk_level = request.args.get('risk_level')            # 风险等级筛选
        cluster_id = request.args.get('cluster_id', type=int)  # 聚类群体ID筛选
        
        # 调用 ProfileService 执行分页查询
        result = ProfileService.get_profile_list(page, per_page, risk_level, cluster_id)
        
        return jsonify({
            'code': 200,
            'message': '获取成功',
            'data': result
        }), 200
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取失败: {str(e)}',
            'data': None
        }), 500

# ==========================================================================
# GET /api/user/profiles/<id> — 获取单个画像详情
# ==========================================================================
@user_bp.route('/profiles/<int:profile_id>', methods=['GET'])
@jwt_required()   # 需要登录
def get_profile(profile_id):
    """获取用户画像详情
    
    参数：profile_id — 画像记录的 ID
    返回：该画像的完整信息（标签、特征向量、风险评分、建议等）
    """
    try:
        # 调用 VisualizationService 获取画像可视化数据
        data = VisualizationService.get_profile_data(profile_id=profile_id)
        
        # 画像不存在
        if not data:
            return jsonify({
                'code': 404,
                'message': '画像不存在',
                'data': None
            }), 404
        
        return jsonify({
            'code': 200,
            'message': '获取成功',
            'data': data
        }), 200
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取失败: {str(e)}',
            'data': None
        }), 500

# ==========================================================================
# GET /api/user/profiles/by-data/<id> — 根据原始数据ID获取画像
# ==========================================================================
@user_bp.route('/profiles/by-data/<int:data_id>', methods=['GET'])
@jwt_required()   # 需要登录
def get_profile_by_data(data_id):
    """根据数据ID获取画像
    
    参数：data_id — 原始心理健康数据的 ID
    返回：该数据对应的用户画像
    """
    try:
        # 调用 VisualizationService 通过原始数据ID查找画像
        data = VisualizationService.get_profile_data(data_id=data_id)
        
        # 画像不存在
        if not data:
            return jsonify({
                'code': 404,
                'message': '画像不存在',
                'data': None
            }), 404
        
        return jsonify({
            'code': 200,
            'message': '获取成功',
            'data': data
        }), 200
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取失败: {str(e)}',
            'data': None
        }), 500

# ==========================================================================
# GET /api/user/profiles/statistics — 画像统计概览
# ==========================================================================
@user_bp.route('/profiles/statistics', methods=['GET'])
@jwt_required()   # 需要登录
def get_profile_statistics():
    """获取画像统计
    
    返回画像的整体统计数据（总数、风险分布、标签统计等）
    """
    try:
        # 调用 ProfileService 计算画像统计
        data = ProfileService.get_profile_statistics()
        
        return jsonify({
            'code': 200,
            'message': '获取成功',
            'data': data
        }), 200
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取失败: {str(e)}',
            'data': None
        }), 500

# ==========================================================================
# GET /api/user/profiles/search — 搜索画像
# ==========================================================================
@user_bp.route('/profiles/search', methods=['GET'])
@jwt_required()   # 需要登录
def search_profiles():
    """搜索画像
    
    根据关键词搜索画像（匹配标签、特征等字段）
    查询参数：keyword(搜索词), page(页码), per_page(每页条数)
    """
    try:
        # 解析查询参数
        keyword = request.args.get('keyword', '')     # 搜索关键词
        page = request.args.get('page', 1, type=int)  # 当前页码
        per_page = request.args.get('per_page', 20, type=int)  # 每页条数
        
        # 关键词不能为空
        if not keyword:
            return jsonify({
                'code': 400,
                'message': '搜索关键词不能为空',
                'data': None
            }), 400
        
        # 调用 ProfileService 执行搜索
        result = ProfileService.search_profiles(keyword, page, per_page)
        
        return jsonify({
            'code': 200,
            'message': '搜索成功',
            'data': result
        }), 200
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'搜索失败: {str(e)}',
            'data': None
        }), 500

# ==========================================================================
# GET /api/user/profiles/<id>/similar — 获取相似画像
# ==========================================================================
@user_bp.route('/profiles/<int:profile_id>/similar', methods=['GET'])
@jwt_required()   # 需要登录
def get_similar_profiles(profile_id):
    """获取相似画像
    
    基于特征向量相似度，找到与指定画像最相似的其他画像
    查询参数：limit(返回条数，默认5条)
    """
    try:
        # 解析返回条数（默认5条）
        limit = request.args.get('limit', 5, type=int)
        
        # 调用 ProfileService 计算特征向量相似度
        data = ProfileService.get_similar_profiles(profile_id, limit)
        
        return jsonify({
            'code': 200,
            'message': '获取成功',
            'data': data
        }), 200
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取失败: {str(e)}',
            'data': None
        }), 500

# ==========================================================================
# GET /api/user/profiles/tags — 获取所有标签列表
# ==========================================================================
@user_bp.route('/profiles/tags', methods=['GET'])
@jwt_required()   # 需要登录
def get_profile_tags():
    """获取所有标签
    
    返回系统中所有画像使用过的标签列表（用于标签筛选下拉框）
    """
    try:
        # 调用 ProfileService 获取所有标签
        data = ProfileService.get_profile_tags()
        
        return jsonify({
            'code': 200,
            'message': '获取成功',
            'data': data
        }), 200
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取失败: {str(e)}',
            'data': None
        }), 500

# ==========================================================================
# GET /api/user/profiles/by-tag/<tag> — 按标签筛选画像
# ==========================================================================
@user_bp.route('/profiles/by-tag/<tag>', methods=['GET'])
@jwt_required()   # 需要登录
def get_profiles_by_tag(tag):
    """根据标签获取画像
    
    参数：tag — URL路径参数，标签名称
    返回：包含该标签的画像列表（分页）
    """
    try:
        # 分页参数
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # 调用 ProfileService 按标签筛选
        result = ProfileService.get_profiles_by_tag(tag, page, per_page)
        
        return jsonify({
            'code': 200,
            'message': '获取成功',
            'data': result
        }), 200
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取失败: {str(e)}',
            'data': None
        }), 500

# ==========================================================================
# POST /api/user/self-assessment — 用户自评（填写特征值查看风险画像）
# ==========================================================================
# 前端传入用户填写的特征值，后端预测风险并生成画像记录
# ==========================================================================
@user_bp.route('/self-assessment', methods=['POST'])
@jwt_required()   # 需要登录
def self_assessment():
    """用户自评 - 填写特征值查看画像和风险
    
    前端传入用户填写的调查数据，后端调用模型预测风险等级，
    并生成一条自评画像记录存入数据库
    """
    try:
        # 获取当前登录用户ID（用于关联自评记录）
        current_user_id = get_jwt_identity()
        # 解析前端传入的调查数据
        data = request.get_json()
        
        # 数据不能为空
        if not data:
            return jsonify({
                'code': 400,
                'message': '请填写评估数据',
                'data': None
            }), 400
        
        # 调用 ProfileService 生成自评画像（特征工程 + 模型预测 + 规则评分）
        result = ProfileService.generate_self_assessment(data, user_id=current_user_id)
        
        return jsonify({
            'code': 200,
            'message': '评估完成',
            'data': result
        }), 200
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'评估失败: {str(e)}',
            'data': None
        }), 500


# ==========================================================================
# GET /api/user/assessment-records — 获取自评记录列表
# ==========================================================================
# 权限控制：
#   - 管理员/分析师：查看所有用户的自评记录
#   - 普通用户：只能查看自己的自评记录
# 自评记录特征：data_id 为 NULL 且 user_id 不为 NULL
# ==========================================================================
@user_bp.route('/assessment-records', methods=['GET'])
@jwt_required()   # 需要登录
def get_assessment_records():
    """获取自评记录列表（管理员查看所有，普通用户查看自己的）
    
    权限控制：admin/analyst 查看所有，普通用户只看自己的
    自评记录区别于数据画像：data_id=NULL 且 user_id!=NULL
    """
    try:
        # 局部导入（避免循环依赖）
        from flask_jwt_extended import get_jwt              # 获取JWT完整声明
        from app.models.user_profile import UserProfile     # 用户画像模型
        from app.models.user import User                    # 用户模型
        
        # ① 获取当前用户信息
        current_user_id = get_jwt_identity()    # 当前用户ID
        claims = get_jwt()                       # JWT中的完整声明
        role = claims.get('role', 'user')        # 用户角色
        
        # ② 分页和筛选参数
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        risk_level = request.args.get('risk_level')    # 风险等级筛选
        username = request.args.get('username')        # 用户名筛选（管理员专用）
        
        # ③ 基础查询：筛选自评记录（data_id=NULL 表示非数据画像，user_id!=NULL 表示用户自评）
        query = UserProfile.query.filter(
            UserProfile.data_id.is_(None),         # data_id 为空 = 自评记录
            UserProfile.user_id.isnot(None)        # user_id 不为空 = 有用户关联
        )
        
        # ④ 权限控制：普通用户只能看自己的记录
        if role not in ['admin', 'analyst']:
            query = query.filter_by(user_id=int(current_user_id))
        
        # ⑤ 筛选条件：风险等级
        if risk_level:
            query = query.filter_by(risk_level=risk_level)
        # ⑥ 筛选条件：用户名（仅管理员/分析师可用）
        if username and role in ['admin', 'analyst']:
            user = User.query.filter(User.username.like(f'%{username}%')).first()
            if user:
                query = query.filter_by(user_id=user.id)   # 找到用户则按user_id筛选
            else:
                query = query.filter_by(user_id=-1)        # 找不到则返回空结果
        
        # ⑦ 按创建时间倒序排列（最新的在前）
        query = query.order_by(UserProfile.created_at.desc())
        
        # ⑧ 执行分页查询
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # ⑨ 构建返回数据，附带用户名和自评原始数据
        items = []
        for item in pagination.items:
            d = item.to_dict()                    # 转为字典
            # ⑨-a 附带用户名
            if item.user_id:
                u = User.query.get(item.user_id)
                d['username'] = u.username if u else None
            else:
                d['username'] = None
            # ⑨-b 从 feature_vector JSON 字段解析原始自评数据
            fv = item.get_feature_vector()            # 获取特征向量字典
            d['age'] = fv.get('age')                  # 年龄
            d['gender'] = fv.get('gender')             # 性别
            d['family_history'] = fv.get('family_history')  # 家族病史
            d['treatment'] = fv.get('treatment')        # 是否接受治疗
            d['work_interfere'] = fv.get('work_interfere')  # 工作干扰程度
            d['remote_work'] = fv.get('remote_work')    # 是否远程工作
            d['tech_company'] = fv.get('tech_company')    # 是否科技公司
            d['benefits'] = fv.get('benefits')          # 公司福利
            d['probabilities'] = fv.get('_probabilities')  # 模型预测概率分布
            d['prediction'] = fv.get('_prediction')     # 模型预测结果
            items.append(d)
        
        return jsonify({
            'code': 200,
            'message': '获取成功',
            'data': {
                'items': items,                    # 自评记录列表
                'total': pagination.total,          # 总记录数
                'pages': pagination.pages,          # 总页数
                'current_page': page               # 当前页码
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取失败: {str(e)}',
            'data': None
        }), 500


# ==========================================================================
# GET /api/user/assessment-records/<id> — 获取单条自评记录详情
# ==========================================================================
@user_bp.route('/assessment-records/<int:record_id>', methods=['GET'])
@jwt_required()   # 需要登录
def get_assessment_detail(record_id):
    """获取单条自评记录详情
    
    参数：record_id — 自评记录的 ID
    返回：完整的自评信息（含原始填写数据 + 预测结果 + 概率分布）
    """
    try:
        # 局部导入
        from app.models.user_profile import UserProfile
        from app.models.user import User
        
        # ① 查询记录
        record = UserProfile.query.get(record_id)
        if not record:
            return jsonify({
                'code': 404,
                'message': '记录不存在',
                'data': None
            }), 404
        
        # ② 构建返回数据
        d = record.to_dict()
        # 附带用户名
        if record.user_id:
            u = User.query.get(record.user_id)
            d['username'] = u.username if u else None   # 查询用户名
        else:
            d['username'] = None
        # ③ 从 feature_vector 解析原始自评数据
        fv = record.get_feature_vector()
        d['age'] = fv.get('age')                  # 年龄
        d['gender'] = fv.get('gender')             # 性别
        d['family_history'] = fv.get('family_history')  # 家族病史
        d['treatment'] = fv.get('treatment')        # 治疗情况
        d['work_interfere'] = fv.get('work_interfere')  # 工作干扰
        d['remote_work'] = fv.get('remote_work')    # 远程工作
        d['tech_company'] = fv.get('tech_company')    # 科技公司
        d['benefits'] = fv.get('benefits')          # 公司福利
        d['probabilities'] = fv.get('_probabilities')  # 预测概率
        d['prediction'] = fv.get('_prediction')     # 预测结果
        
        return jsonify({
            'code': 200,
            'message': '获取成功',
            'data': d
        }), 200
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取失败: {str(e)}',
            'data': None
        }), 500


# ==========================================================================
# GET /api/user/assessment-records/stats — 自评统计数据（管理员）
# ==========================================================================
@user_bp.route('/assessment-records/stats', methods=['GET'])
@jwt_required()   # 需要登录
def get_assessment_stats():
    """获取自评统计数据（管理员）
    
    返回自评记录的总数和各风险等级分布
    """
    try:
        # 局部导入
        from app.models.user_profile import UserProfile
        
        # 基础查询：只统计自评记录（data_id=NULL 且 user_id!=NULL）
        base_query = UserProfile.query.filter(
            UserProfile.data_id.is_(None),         # 自评记录标识
            UserProfile.user_id.isnot(None)        # 有用户关联
        )
        # 统计总数和各风险等级数量
        total = base_query.count()                                          # 总记录数
        high_risk = base_query.filter_by(risk_level='High Risk').count()     # 高风险人数
        medium_risk = base_query.filter_by(risk_level='Medium Risk').count() # 中风险人数
        low_risk = base_query.filter_by(risk_level='Low Risk').count()       # 低风险人数
        
        return jsonify({
            'code': 200,
            'message': '获取成功',
            'data': {
                'total': total,              # 自评总记录数
                'high_risk': high_risk,       # 高风险数量
                'medium_risk': medium_risk,   # 中风险数量
                'low_risk': low_risk          # 低风险数量
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取失败: {str(e)}',
            'data': None
        }), 500


# ======================================================================
# ===== 用户账号管理（仅管理员/分析师可操作） =====
# ======================================================================

# ==========================================================================
# GET /api/user/accounts — 获取用户账号列表（管理员/分析师）
# ==========================================================================
@user_bp.route('/accounts', methods=['GET'])
@jwt_required()   # 需要登录
def get_user_accounts():
    """获取用户账号列表（管理员）
    
    权限：仅 admin/analyst 可访问
    支持关键词搜索（用户名/邮箱）和角色筛选
    """
    try:
        # 局部导入
        from flask_jwt_extended import get_jwt       # 获取JWT声明
        from app.models.user import User              # 用户模型
        from app import db                             # 数据库实例
        
        # ① 权限检查：只有管理员和分析师可以查看
        claims = get_jwt()
        role = claims.get('role', 'user')
        if role not in ['admin', 'analyst']:
            return jsonify({'code': 403, 'message': '无权限', 'data': None}), 403
        
        # ② 分页和筛选参数
        page = request.args.get('page', 1, type=int)           # 页码
        per_page = request.args.get('per_page', 20, type=int)  # 每页条数
        keyword = request.args.get('keyword', '')               # 搜索关键词
        role_filter = request.args.get('role')                   # 角色筛选
        
        # ③ 构建查询
        query = User.query
        # 关键词搜索：匹配用户名或邮箱
        if keyword:
            query = query.filter(
                db.or_(
                    User.username.like(f'%{keyword}%'),   # 用户名模糊匹配
                    User.email.like(f'%{keyword}%')       # 邮箱模糊匹配
                )
            )
        # 角色筛选
        if role_filter:
            query = query.filter_by(role=role_filter)
        
        # ④ 按创建时间倒序 + 分页
        query = query.order_by(User.created_at.desc())
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'code': 200,
            'message': '获取成功',
            'data': {
                'items': [u.to_dict() for u in pagination.items],  # 用户列表
                'total': pagination.total,      # 总数
                'pages': pagination.pages,       # 总页数
                'current_page': page            # 当前页码
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取失败: {str(e)}',
            'data': None
        }), 500


# ==========================================================================
# DELETE /api/user/accounts/<id> — 删除用户账号（仅管理员）
# ==========================================================================
# 权限：仅 admin 可操作（analyst 也不行）
# ==========================================================================
@user_bp.route('/accounts/<int:user_id>', methods=['DELETE'])
@jwt_required()   # 需要登录
def delete_user_account(user_id):
    """删除用户账号（管理员）
    
    权限：仅 admin 可操作
    流程：权限检查 → 禁止自删 → 删除关联画像 → 删除用户
    """
    try:
        # 局部导入
        from flask_jwt_extended import get_jwt
        from app.models.user import User
        from app.models.user_profile import UserProfile  # 需要删除关联画像
        from app import db
        
        # ① 权限检查：只有管理员(admin)可以删除用户
        claims = get_jwt()
        role = claims.get('role', 'user')
        if role != 'admin':
            return jsonify({'code': 403, 'message': '只有管理员可以删除用户', 'data': None}), 403
        
        # ② 禁止删除自己的账号（防止管理员误操作）
        current_user_id = get_jwt_identity()
        if int(current_user_id) == user_id:
            return jsonify({'code': 400, 'message': '不能删除自己的账号', 'data': None}), 400
        
        # ③ 查找目标用户
        user = User.query.get(user_id)
        if not user:
            return jsonify({'code': 404, 'message': '用户不存在', 'data': None}), 404
        
        # ④ 删除用户关联的画像记录（级联清理）
        UserProfile.query.filter_by(user_id=user_id).delete()
        # ⑤ 删除用户本身
        db.session.delete(user)
        # ⑥ 提交事务
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': '用户删除成功',
            'data': None
        }), 200
        
    except Exception as e:
        db.session.rollback()  # 出错时回滚事务
        return jsonify({
            'code': 500,
            'message': f'删除失败: {str(e)}',
            'data': None
        }), 500


# ==========================================================================
# PUT /api/user/accounts/<id>/toggle-status — 启用/禁用用户（仅管理员）
# ==========================================================================
@user_bp.route('/accounts/<int:user_id>/toggle-status', methods=['PUT'])
@jwt_required()   # 需要登录
def toggle_user_status(user_id):
    """启用/禁用用户账号（管理员）
    
    权限：仅 admin 可操作
    切换用户的 is_active 状态（True↔False）
    禁用后用户无法登录，但数据不会被删除
    """
    try:
        # 局部导入
        from flask_jwt_extended import get_jwt
        from app.models.user import User
        from app import db
        
        # ① 权限检查：只有管理员可以操作
        claims = get_jwt()
        role = claims.get('role', 'user')
        if role != 'admin':
            return jsonify({'code': 403, 'message': '只有管理员可以操作', 'data': None}), 403
        
        # ② 查找目标用户
        user = User.query.get(user_id)
        if not user:
            return jsonify({'code': 404, 'message': '用户不存在', 'data': None}), 404
        
        # ③ 切换状态：True↔False
        user.is_active = not user.is_active
        # ④ 提交到数据库
        db.session.commit()
        
        # ⑤ 根据新状态返回对应消息
        status = '启用' if user.is_active else '禁用'
        return jsonify({
            'code': 200,
            'message': f'用户已{status}',
            'data': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()  # 出错时回滚事务
        return jsonify({
            'code': 500,
            'message': f'操作失败: {str(e)}',
            'data': None
        }), 500
