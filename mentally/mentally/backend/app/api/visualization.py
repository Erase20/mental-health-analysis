# =============================================================================
# visualization.py — 可视化模块 API（9种图表接口）
# =============================================================================
# 职责：为前端 ECharts 图表提供数据，包括概览/风险/聚类/特征/相关性/地理/趋势/雷达/对比
# 路由前缀：/api/viz/xxx
# 数据格式：返回前端可直接用于图表渲染的 JSON 数据
# =============================================================================

# ---- Flask 核心 ----
from flask import Blueprint, request, jsonify
# ---- 业务层 ----
from app.services.visualization_service import VisualizationService  # 可视化服务（计算图表数据）
from app.utils.permissions import roles_required

# 创建可视化蓝图，URL前缀 /api/viz
viz_bp = Blueprint('viz', __name__)

# ==========================================================================
# GET /api/viz/overview — 数据概览统计（用于仪表盘）
# ==========================================================================
# 返回：总人数、风险分布、性别比例等概览数据
# ==========================================================================
@viz_bp.route('/overview', methods=['GET'])
@roles_required('admin', 'analyst')
def get_overview():
    """获取概览数据
    
    返回仪表盘所需的总览统计：总人数、风险等级分布、性别比例、年龄分布等
    """
    try:
        # 调用 VisualizationService 计算概览统计
        data = VisualizationService.get_overview_stats()
        
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
# GET /api/viz/risk-analysis — 风险分析数据（饼图/柱状图）
# ==========================================================================
# 返回：各风险等级的人数分布，用于生成饼图或柱状图
# ==========================================================================
@viz_bp.route('/risk-analysis', methods=['GET'])
@roles_required('admin', 'analyst')
def get_risk_analysis():
    """获取风险分析数据
    
    返回各风险等级（High/Medium/Low Risk）的人数分布
    前端用于生成饼图或柱状图展示
    """
    try:
        # 调用 VisualizationService 计算风险分布
        data = VisualizationService.get_risk_analysis()
        
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
# GET /api/viz/cluster-analysis — 聚类分析可视化数据
# ==========================================================================
# 返回：各聚类群体的规模、特征均值、名称映射
# ==========================================================================
@viz_bp.route('/cluster-analysis', methods=['GET'])
@roles_required('admin', 'analyst')
def get_cluster_analysis():
    """获取聚类分析数据
    
    返回 KMeans 聚类结果：各群体的规模、特征均值、名称映射
    前端用于生成聚类分布图（散点图/堆叠柱状图等）
    """
    try:
        # 调用 VisualizationService 计算聚类图表数据
        data = VisualizationService.get_cluster_analysis()
        
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
# GET /api/viz/feature-analysis — 特征重要性分析（柱状图）
# ==========================================================================
# 返回：各特征对风险预测的重要性排名
# ==========================================================================
@viz_bp.route('/feature-analysis', methods=['GET'])
@roles_required('admin', 'analyst')
def get_feature_analysis():
    """获取特征分析数据
    
    返回 RandomForest 模型的特征重要性排名
    前端用于生成水平柱状图，展示哪些特征对风险预测影响最大
    """
    try:
        # 调用 VisualizationService 计算特征重要性数据
        data = VisualizationService.get_feature_analysis()
        
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
# GET /api/viz/correlation — 特征相关性矩阵（热力图）
# ==========================================================================
# 返回：特征之间的相关系数矩阵，用于生成热力图
# ==========================================================================
@viz_bp.route('/correlation', methods=['GET'])
@roles_required('admin', 'analyst')
def get_correlation():
    """获取相关性数据
    
    返回特征之间的皮尔逊相关系数矩阵
    前端用于生成热力图，展示特征之间的相关性关系
    """
    try:
        # 调用 VisualizationService 计算相关性矩阵
        data = VisualizationService.get_correlation_data()
        
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
# GET /api/viz/geo-distribution — 地理分布数据（地图）
# ==========================================================================
# 返回：各国家/地区的心理健康数据分布，用于生成地图
# ==========================================================================
@viz_bp.route('/geo-distribution', methods=['GET'])
@roles_required('admin', 'analyst')
def get_geo_distribution():
    """获取地理分布数据
    
    返回各国家的调查数据量和风险分布
    前端用于生成世界地图可视化
    """
    try:
        # 调用 VisualizationService 计算地理分布
        data = VisualizationService.get_geo_distribution()
        
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
# GET /api/viz/trend — 趋势数据（折线图）
# ==========================================================================
# 返回：数据量随时间的变化趋势
# ==========================================================================
@viz_bp.route('/trend', methods=['GET'])
@roles_required('admin', 'analyst')
def get_trend():
    """获取趋势数据
    
    返回数据导入量随时间的变化趋势
    前端用于生成折线图展示
    """
    try:
        # 调用 VisualizationService 计算趋势数据
        data = VisualizationService.get_trend_data()
        
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
# GET /api/viz/radar — 雷达图数据
# ==========================================================================
# 参数：cluster_id — 指定聚类群体ID（可选，不传则返回所有群体）
# 返回：5维度雷达数据（工作支持度/心理意识/治疗意愿/工作灵活性/社会支持）
# ==========================================================================
@viz_bp.route('/radar', methods=['GET'])
@roles_required('admin', 'analyst')
def get_radar():
    """获取雷达图数据
    
    查询参数：cluster_id — 指定群体ID（可选）
    返回5维度雷达数据：工作支持度、心理健康意识、治疗意愿、工作灵活性、社会支持
    """
    try:
        # 解析可选的聚类群体ID（不传则返回所有群体的雷达数据）
        cluster_id = request.args.get('cluster_id', type=int)
        # 调用 VisualizationService 计算雷达数据
        data = VisualizationService.get_radar_data(cluster_id)
        
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
# GET /api/viz/comparison — 群体对比数据
# ==========================================================================
# 参数：cluster_id — 多个聚类群体ID（如 ?cluster_id=0&cluster_id=1）
# 返回：多个群体在各维度上的对比数据，用于生成对比图
# ==========================================================================
@viz_bp.route('/comparison', methods=['GET'])
@roles_required('admin', 'analyst')
def get_comparison():
    """获取群体对比数据
    
    查询参数：cluster_id — 要对比的群体ID列表（支持多个）
    返回多个群体在各特征维度上的对比数据
    """
    try:
        # 解析多个聚类群体ID（URL格式：?cluster_id=0&cluster_id=1）
        cluster_ids = request.args.getlist('cluster_id', type=int)
        
        # 必须指定至少一个群体
        if not cluster_ids:
            return jsonify({
                'code': 400,
                'message': '请指定要对比的群体',
                'data': None
            }), 400
        
        # 调用 VisualizationService 计算对比数据
        data = VisualizationService.get_comparison_data(cluster_ids)
        
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
