# =============================================================================
# data.py — 数据管理模块 API（上传 / 列表 / 详情 / 删除 / 统计 / 分布 / 导出）
# =============================================================================
# 职责：处理心理健康调查数据的导入、查询、统计和导出
# 路由前缀：/api/data/xxx
# 数据来源：CSV / Excel 文件上传，解析后存入数据库
# =============================================================================

# ---- Flask 核心 ----
from flask import Blueprint, request, jsonify, current_app  # current_app=当前应用实例（获取配置）
# ---- JWT 认证 ----
from flask_jwt_extended import jwt_required, get_jwt_identity  # 所有接口均需登录
# ---- 工具库 ----
from werkzeug.utils import secure_filename  # 安全文件名处理（过滤特殊字符，防止路径注入攻击）
import os                                    # 文件系统操作（路径拼接等）
import pandas as pd                          # 数据处理（时间戳、导出CSV等）
# ---- 业务层 ----
from app.services.data_service import DataService       # 数据服务（导入/查询/统计/导出）
from app.models.mental_health_data import MentalHealthData  # 心理健康数据模型
from app import db                                        # 数据库实例

# 允许上传的文件扩展名（只接受CSV和Excel格式）
ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}

# 创建数据管理蓝图，URL前缀 /api/data
data_bp = Blueprint('data', __name__)

def allowed_file(filename):
    """检查文件扩展名是否在允许列表中
    
    判断逻辑：文件名中包含'.'且后缀在 ALLOWED_EXTENSIONS 中
    例：data.csv ✓  |  data.exe ✗  |  data ✓
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ==========================================================================
# POST /api/data/upload — 上传数据文件（CSV/Excel）
# ==========================================================================
# 流程：检查文件 → 安全命名 → 保存到磁盘 → 调用 DataService 解析并入库
# 返回：导入的数据条数 + 文件名
# ==========================================================================
@data_bp.route('/upload', methods=['POST'])
@jwt_required()   # 需要登录
def upload_file():
    """上传数据文件
    
    前端以 multipart/form-data 格式上传文件，
    后端保存文件后调用 DataService.import_from_csv() 解析并批量入库
    """
    try:
        # ① 检查请求中是否包含文件字段
        if 'file' not in request.files:
            return jsonify({
                'code': 400,
                'message': '没有文件',
                'data': None
            }), 400
        
        # ② 获取文件对象
        file = request.files['file']
        
        # ③ 检查用户是否真的选择了文件（而不是提交空文件名）
        if file.filename == '':
            return jsonify({
                'code': 400,
                'message': '未选择文件',
                'data': None
            }), 400
        
        # ④ 检查文件扩展名是否合法
        if not allowed_file(file.filename):
            return jsonify({
                'code': 400,
                'message': '不支持的文件格式，请上传CSV或Excel文件',
                'data': None
            }), 400
        
        # ⑤ 保存文件到磁盘
        # secure_filename() 过滤特殊字符，防止文件名注入攻击（如 ../etc/passwd）
        filename = secure_filename(file.filename)
        # 添加时间戳前缀，防止同名文件覆盖（例：20260317_192804_data.csv）
        timestamp = pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{filename}"
        # 拼接完整路径（DATA_PATH 在 config.py 中配置）
        filepath = os.path.join(current_app.config['DATA_PATH'], filename)
        file.save(filepath)   # 写入磁盘
        
        # ⑥ 调用 DataService 解析 CSV 并批量入库，返回导入条数
        count = DataService.import_from_csv(filepath)
        
        return jsonify({
            'code': 200,
            'message': f'成功导入{count}条数据',
            'data': {
                'filename': filename,   # 保存后的文件名
                'count': count          # 导入的数据条数
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'导入失败: {str(e)}',
            'data': None
        }), 500

# ==========================================================================
# GET /api/data/list — 获取数据列表（分页 + 筛选）
# ==========================================================================
# 查询参数：page(页码), per_page(每页条数), risk_level, gender, age_group, country, cluster_id
# ==========================================================================
@data_bp.route('/list', methods=['GET'])
@jwt_required()   # 需要登录
def get_data_list():
    """获取数据列表
    
    支持分页和多维度筛选（风险等级、性别、年龄组、国家、聚类群体）
    """
    try:
        # ① 分页参数：默认第1页，每顢20条
        page = request.args.get('page', 1, type=int)         # 当前页码
        per_page = request.args.get('per_page', 20, type=int) # 每页显示条数
        
        # ② 筛选参数：从 URL 查询参数中提取过滤条件
        filters = {
            'risk_level': request.args.get('risk_level'),       # 风险等级筛选
            'gender': request.args.get('gender'),               # 性别筛选
            'age_group': request.args.get('age_group'),         # 年龄组筛选
            'country': request.args.get('country'),             # 国家筛选
            'cluster_id': request.args.get('cluster_id', type=int)  # 聚类群体ID筛选
        }
        
        # ③ 移除值为 None 的筛选条件（只保留用户实际传入的参数）
        filters = {k: v for k, v in filters.items() if v is not None}
        
        # ④ 调用 DataService 执行分页查询
        result = DataService.get_data_list(page, per_page, filters)
        
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
# GET /api/data/<id> — 获取单条数据详情
# ==========================================================================
@data_bp.route('/<int:data_id>', methods=['GET'])
@jwt_required()   # 需要登录
def get_data_detail(data_id):
    """获取数据详情
    
    参数：data_id — URL 路径参数，数据记录的 ID
    返回：该条记录的完整字段信息
    """
    try:
        # 调用 DataService 查询单条记录
        data = DataService.get_data_by_id(data_id)
        
        # 查询不到则返回404
        if not data:
            return jsonify({
                'code': 404,
                'message': '数据不存在',
                'data': None
            }), 404
        
        return jsonify({
            'code': 200,
            'message': '获取成功',
            'data': data.to_dict()  # 转字典返回（隐藏内部结构）
        }), 200
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取失败: {str(e)}',
            'data': None
        }), 500

# ==========================================================================
# DELETE /api/data/<id> — 删除单条数据
# ==========================================================================
@data_bp.route('/<int:data_id>', methods=['DELETE'])
@jwt_required()   # 需要登录
def delete_data(data_id):
    """删除数据
    
    参数：data_id — 要删除的数据记录 ID
    """
    try:
        # 调用 DataService 执行删除，返回是否成功
        success = DataService.delete_data(data_id)
        
        # 数据不存在
        if not success:
            return jsonify({
                'code': 404,
                'message': '数据不存在',
                'data': None
            }), 404
        
        return jsonify({
            'code': 200,
            'message': '删除成功',
            'data': None
        }), 200
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'删除失败: {str(e)}',
            'data': None
        }), 500

# ==========================================================================
# GET /api/data/statistics — 获取数据统计概览
# ==========================================================================
# 返回：总数、风险等级分布、性别分布、年龄分布等统计数据
# ==========================================================================
@data_bp.route('/statistics', methods=['GET'])
@jwt_required()   # 需要登录
def get_statistics():
    """获取数据统计
    
    返回数据的整体统计概览，用于仪表盘展示
    """
    try:
        # 调用 DataService 计算统计数据
        stats = DataService.get_statistics()
        
        return jsonify({
            'code': 200,
            'message': '获取成功',
            'data': stats
        }), 200
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取失败: {str(e)}',
            'data': None
        }), 500

# ==========================================================================
# GET /api/data/distribution/<feature> — 获取特征分布
# ==========================================================================
# 参数：feature_name — URL路径参数，特征名（如 gender, risk_level, age等）
# 返回：该特征各取值的数量分布（用于生成饼图/柱状图）
# ==========================================================================
@data_bp.route('/distribution/<feature_name>', methods=['GET'])
@jwt_required()   # 需要登录
def get_distribution(feature_name):
    """获取特征分布
    
    参数：feature_name — 特征名称（如 gender, risk_level, country 等）
    返回：该特征各取值的计数分布，用于前端可视化图表
    """
    try:
        # 调用 DataService 统计该特征的分布
        distribution = DataService.get_feature_distribution(feature_name)
        
        return jsonify({
            'code': 200,
            'message': '获取成功',
            'data': {
                'feature': feature_name,      # 特征名称
                'distribution': distribution   # 分布数据（字典格式）
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取失败: {str(e)}',
            'data': None
        }), 500

# ==========================================================================
# GET /api/data/export — 导出数据为 CSV
# ==========================================================================
# 流程：筛选数据 → 转DataFrame → 保存为CSV → 返回下载链接
# ==========================================================================
@data_bp.route('/export', methods=['GET'])
@jwt_required()   # 需要登录
def export_data():
    """导出数据
    
    根据筛选条件导出数据为 CSV 文件，返回下载链接
    """
    try:
        # ① 筛选参数（支持按风险等级和聚类群体筛选）
        filters = {
            'risk_level': request.args.get('risk_level'),       # 风险等级
            'cluster_id': request.args.get('cluster_id', type=int)  # 聚类群体
        }
        # 移除空值
        filters = {k: v for k, v in filters.items() if v is not None}
        
        # ② 获取筛选后的 DataFrame 数据
        df = DataService.get_dataframe(filters)
        
        # ③ 生成导出文件名（带时间戳）
        timestamp = pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')
        filename = f'export_{timestamp}.csv'
        filepath = os.path.join(current_app.config['DATA_PATH'], filename)
        
        # ④ 保存为 CSV（utf-8-sig 编码支持 Excel 正确显示中文）
        df.to_csv(filepath, index=False, encoding='utf-8-sig')
        
        return jsonify({
            'code': 200,
            'message': '导出成功',
            'data': {
                'filename': filename,                                # 导出的文件名
                'download_url': f'/api/data/download/{filename}'    # 下载链接
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'导出失败: {str(e)}',
            'data': None
        }), 500
