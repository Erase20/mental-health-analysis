# =============================================================================
# analysis.py — 分析模块 API（完整分析 / 聚类 / 分类 / 预测 / 历史 / 最新）
# =============================================================================
# 职责：调用机器学习服务进行数据分析、模型训练和风险预测
# 路由前缀：/api/analysis/xxx
# 核心算法：KMeans++聚类 + RandomForest分类 + 特征工程
# =============================================================================

# ---- Flask 核心 ----
from flask import Blueprint, request, jsonify
# ---- JWT 认证 ----
from flask_jwt_extended import jwt_required, get_jwt_identity  # 所有接口需要登录
# ---- 业务层 ----
from app.services.analysis_service import AnalysisService  # 分析服务（核心算法编排）

# 创建分析蓝图，URL前缀 /api/analysis
analysis_bp = Blueprint('analysis', __name__)

# ==========================================================================
# POST /api/analysis/run — 运行完整分析
# ==========================================================================
# 流程：获取数据 → 特征工程 → 聚类分析 → 分类模型 → 生成用户画像
# 耗时较长，前端应显示加载状态
# ==========================================================================
@analysis_bp.route('/run', methods=['POST'])
@jwt_required()   # 需要登录
def run_analysis():
    """运行完整分析
    
    触发完整的分析流水线：数据获取 → 特征工程 → 聚类 → 分类 → 画像生成
    这是系统中最核心的接口，通常需要较长时间执行
    """
    try:
        # 获取当前登录用户的ID（用于记录谁触发的分析）
        current_user_id = get_jwt_identity()
        
        # 调用 AnalysisService 执行完整分析流程
        result = AnalysisService.run_full_analysis(user_id=current_user_id)
        
        return jsonify({
            'code': 200,
            'message': '分析完成',  
            'data': result
        }), 200
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'分析失败: {str(e)}',
            'data': None
        }), 500

# ==========================================================================
# POST /api/analysis/clustering — 单独运行聚类分析
# ==========================================================================
# 使用 KMeans++ 算法对用户群体进行聚类，自动寻找最优K值
# ==========================================================================
@analysis_bp.route('/clustering', methods=['POST'])
@jwt_required()   # 需要登录
def run_clustering():
    """运行聚类分析
    
    单独运行 KMeans++ 聚类：获取数据 → 特征工程 → 聚类 → 更新数据库
    用于只更新聚类结果而不重新训练分类模型的场景
    """
    try:
        # 局部导入：避免循环依赖，只在需要时加载
        from app.services.data_service import DataService          # 数据服务
        from app.ml.clustering import ClusteringModel              # KMeans 聚类模型
        from app.ml.feature_engineering import FeatureEngineer      # 特征工程
        import pandas as pd
        
        # 获取当前用户 ID
        current_user_id = get_jwt_identity()
        
        # ① 获取数据（限制2000条，避免数据量太大导致超时）
        df = DataService.get_dataframe(limit=2000)
        
        # ② 特征工程：生成衍生特征（support_score, stress_index等）
        feature_engineer = FeatureEngineer()
        df_features = feature_engineer.create_features(df)
        
        # ③ 选择用于聚类的特征列（8个核心特征）
        feature_cols = [
            'age',                             # 年龄
            'support_score',                   # 支持度评分
            'stress_index',                    # 压力指数
            'company_size_encoded',            # 公司规模编码
            'attitude_score',                  # 态度评分
            'family_treatment_interaction',    # 家庭治疗交互特征
            'remote_tech_interaction',         # 远程工作+科技公司交互特征
            'has_observed_consequence'         # 是否观察到后果
        ]
        # 只保留实际存在的列（防止数据中缺少某个字段时报错）
        available_cols = [col for col in feature_cols if col in df_features.columns]
        X = df_features[available_cols].fillna(0)  # 缺失值填充为0
        
        # ④ 调用 AnalysisService 执行聚类
        result = AnalysisService.run_clustering(X, df_features, current_user_id)
        
        return jsonify({
            'code': 200,
            'message': '聚类分析完成',
            'data': result
        }), 200
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'聚类分析失败: {str(e)}',
            'data': None
        }), 500

# ==========================================================================
# POST /api/analysis/classification — 单独运行分类模型
# ==========================================================================
# 使用 RandomForest 随机森林训练风险分类模型
# ==========================================================================
@analysis_bp.route('/classification', methods=['POST'])
@jwt_required()   # 需要登录
def run_classification():
    """运行分类分析
    
    单独运行 RandomForest 分类：获取数据 → 特征工程 → 分类模型训练 → 保存指标
    用于只更新分类模型而不重新聚类的场景
    """
    try:
        # 局部导入：避免循环依赖
        from app.services.data_service import DataService          # 数据服务
        from app.ml.feature_engineering import FeatureEngineer      # 特征工程
        
        # 获取当前用户 ID
        current_user_id = get_jwt_identity()
        
        # ① 获取数据（限制2000条，避免超时）
        df = DataService.get_dataframe(limit=2000)
        
        # ② 特征工程：生成衍生特征
        feature_engineer = FeatureEngineer()
        df_features = feature_engineer.create_features(df)
        
        # ③ 选择特征列（与聚类相同的8个核心特征）
        feature_cols = [
            'age',                             # 年龄
            'support_score',                   # 支持度评分
            'stress_index',                    # 压力指数
            'company_size_encoded',            # 公司规模编码
            'attitude_score',                  # 态度评分
            'family_treatment_interaction',    # 家庭治疗交互
            'remote_tech_interaction',         # 远程工作+科技公司
            'has_observed_consequence'         # 是否观察到后果
        ]
        # 只保留实际存在的列
        available_cols = [col for col in feature_cols if col in df_features.columns]
        X = df_features[available_cols].fillna(0)  # 缺失值填充0
        
        # ④ 调用 AnalysisService 执行分类训练
        result = AnalysisService.run_classification(X, df_features, current_user_id)
        
        return jsonify({
            'code': 200,
            'message': '分类分析完成',
            'data': result
        }), 200
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'分类分析失败: {str(e)}',
            'data': None
        }), 500

# ==========================================================================
# POST /api/analysis/predict — 单条风险预测
# ==========================================================================
# 前端传入用户特征值，后端加载已训练模型进行单条预测
# ==========================================================================
@analysis_bp.route('/predict', methods=['POST'])
@jwt_required()   # 需要登录
def predict():
    """预测风险等级
    
    前端传入特征值，后端加载已训练的 RandomForest 模型进行单条预测
    返回预测的风险等级 + 概率分布
    """
    try:
        # ① 解析前端传入的 JSON 特征数据
        data = request.get_json()
        
        # ② 准备特征向量（使用默认值填充缺失字段）
        features = {
            'age': data.get('age', 30),                              # 年龄（默认30岁）
            'support_score': data.get('support_score', 0.5),          # 支持度（默认0.5）
            'stress_index': data.get('stress_index', 0.5),            # 压力指数（默认0.5）
            'company_size_encoded': data.get('company_size_encoded', 2),  # 公司规模编码（默认2=中型）
            'attitude_score': data.get('attitude_score', 0.5),        # 态度评分（默认0.5）
            'family_treatment_interaction': data.get('family_treatment_interaction', 0),  # 家庭治疗交互
            'remote_tech_interaction': data.get('remote_tech_interaction', 0),          # 远程工作+科技
            'has_observed_consequence': data.get('has_observed_consequence', 0)         # 观察到后果
        }
        
        # ③ 调用 AnalysisService 执行单条预测（加载.pkl模型）
        result = AnalysisService.predict_risk(features)
        
        return jsonify({
            'code': 200,
            'message': '预测成功',
            'data': result
        }), 200
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'预测失败: {str(e)}',
            'data': None
        }), 500

# ==========================================================================
# GET /api/analysis/history — 获取分析历史记录
# ==========================================================================
# 查询参数：type(分析类型), limit(返回条数)
# ==========================================================================
@analysis_bp.route('/history', methods=['GET'])
@jwt_required()   # 需要登录
def get_history():
    """获取分析历史
    
    查询参数：
    - type: 分析类型（full/clustering/classification）
    - limit: 返回条数（默认10条）
    """
    try:
        # 解析查询参数
        analysis_type = request.args.get('type')       # 分析类型筛选
        limit = request.args.get('limit', 10, type=int) # 返回条数（默认10）
        
        # 调用 AnalysisService 查询历史
        history = AnalysisService.get_analysis_history(analysis_type, limit)
        
        return jsonify({
            'code': 200,
            'message': '获取成功',
            'data': history
        }), 200
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取失败: {str(e)}',
            'data': None
        }), 500

# ==========================================================================
# GET /api/analysis/latest/<type> — 获取最新的分析结果
# ==========================================================================
# 参数：analysis_type — URL路径参数（full/clustering/classification）
# ==========================================================================
@analysis_bp.route('/latest/<analysis_type>', methods=['GET'])
@jwt_required()   # 需要登录
def get_latest(analysis_type):
    """获取最新分析结果
    
    参数：analysis_type — 分析类型（full/clustering/classification）
    返回：该类型最新一次分析的完整结果
    """
    try:
        # 查询指定类型的最新分析结果
        result = AnalysisService.get_latest_analysis(analysis_type)
        
        # 还没有分析结果
        if not result:
            return jsonify({
                'code': 404,
                'message': '暂无分析结果',
                'data': None
            }), 404
        
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
