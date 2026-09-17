# ==================== 标准库 ====================
import pandas as pd       # 数据处理：读取、清洗、转换表格数据
import numpy as np         # 数值计算：数组运算、数学函数
from datetime import datetime  # 时间处理
import os                  # 文件系统操作（拼接路径等）
import logging             # 日志记录（方便调试和排查问题）

# ==================== 项目内部模块 ====================
from app import db         # SQLAlchemy 数据库实例（用于增删改查）
from app.models.mental_health_data import MentalHealthData  # 心理健康原始数据模型
from app.models.analysis_result import AnalysisResult        # 分析结果模型（存模型指标）
from app.models.user_profile import UserProfile              # 用户画像模型（存标签/评分）

# Service 层：其他业务服务
from app.services.data_service import DataService            # 数据服务（获取DataFrame、更新聚类标签）
from app.services.visualization_service import VisualizationService  # 可视化服务（获取群体名称）

# ML 层：机器学习模块
from app.ml.preprocessing import DataPreprocessor        # 数据预处理（缺失值/异常值/编码/标准化/PCA）
from app.ml.feature_engineering import FeatureEngineer   # 特征工程（从原始数据衍生新特征）
from app.ml.clustering import ClusteringModel            # 聚类算法（KMeans++）
from app.ml.classification import ClassificationModel    # 分类算法（RandomForest）

from flask import current_app  # 获取当前Flask应用实例（读取配置如MODEL_PATH）

# 创建本模块的日志记录器
logger = logging.getLogger(__name__)

class AnalysisService:
    """
    分析服务类 —— 后端的"大脑"
    
    职责：编排整个分析流程，串联 ML 模块和数据库操作
    包含 6 个核心方法：
      - run_full_analysis()   : 一键运行完整分析（聚类+分类+画像）
      - run_clustering()      : 单独运行 KMeans 聚类
      - run_classification()  : 单独运行 RandomForest 分类
      - generate_user_profiles(): 根据分析结果为每个人生成画像
      - predict_risk()        : 用已训练模型预测单条数据的风险
      - get_analysis_history() / get_latest_analysis() : 查询历史分析结果
    """
    
    @staticmethod
    def run_full_analysis(user_id=None):
        """
        运行完整分析流程（核心入口）
        
        整个流程分 6 步：
          获取数据 → 特征工程 → 选择特征 → 聚类分析 → 分类分析 → 生成画像
        
        参数：
            user_id: 触发分析的用户ID（可选，用于记录是谁触发的）
        返回：
            dict: 包含聚类结果和分类结果的字典
        """
        try:
            # ===== 第1步：获取数据 =====
            # 从数据库读取心理健康数据，限制2000条防止计算超时
            logger.info("开始获取数据...")
            df = DataService.get_dataframe(limit=2000)
            
            if df.empty:
                raise ValueError("没有可用数据")
            
            # ===== 第2步：特征工程 =====
            # 从原始的30+个字段中，衍生出8个更有价值的"新特征"
            # 例如：support_score（公司支持度评分）、stress_index（压力指数）
            # 这些新特征比原始字段更适合机器学习
            logger.info("开始特征工程...")
            feature_engineer = FeatureEngineer()
            df_features = feature_engineer.create_features(df)
            
            # ===== 第3步：选择用于建模的特征列 =====
            # 只选取经过特征工程处理后的数值型特征（不直接用原始文本字段）
            # feature_cols 中每个特征的含义：
            #   age                          → 年龄（直接使用）
            #   support_score                → 公司支持度评分(0~1)，由5项福利指标综合计算
            #   stress_index                 → 工作压力指数(0~1)，由工作干扰+后果+请假难度计算
            #   company_size_encoded         → 公司规模编码(0~5)，如 '1-5'→0, 'More than 1000'→5
            #   attitude_score               → 心理健康态度评分(0~1)，由同事/上司态度等计算
            #   family_treatment_interaction → 家族病史×是否治疗 的交互项（两者都有=1，否则=0）
            #   remote_tech_interaction      → 远程工作×科技公司 的交互项
            #   has_observed_consequence     → 是否观察到心理健康的负面后果(0/1)
            logger.info("开始数据预处理...")
            preprocessor = DataPreprocessor()
            
            feature_cols = [
                'age', 'support_score', 'stress_index', 'company_size_encoded',
                'attitude_score', 'family_treatment_interaction', 
                'remote_tech_interaction', 'has_observed_consequence'
            ]
            
            # 过滤：只保留 DataFrame 中实际存在的列（防御性编程）
            available_cols = [col for col in feature_cols if col in df_features.columns]
            # X 就是最终喂给模型的输入矩阵，缺失值填0
            X = df_features[available_cols].fillna(0)
            
            # ===== 第4步：聚类分析（无监督学习）=====
            # 目的：不知道谁高风险谁低风险，让 KMeans 自动把人分成几类
            logger.info("开始聚类分析...")
            clustering_result = AnalysisService.run_clustering(X, df_features, user_id)
            
            # ===== 第5步：分类分析（有监督学习）=====
            # 目的：已知 risk_level 标签，训练 RandomForest 模型来预测新人的风险
            logger.info("开始分类分析...")
            classification_result = AnalysisService.run_classification(X, df_features, user_id)
            
            # ===== 第6步：生成用户画像 =====
            # 根据聚类结果（cluster_labels），为每个人生成标签、评分、建议
            logger.info("生成用户画像...")
            AnalysisService.generate_user_profiles(df_features, clustering_result['labels'], user_id)
            
            # 返回完整分析结果
            return {
                'clustering': clustering_result,
                'classification': classification_result,
                'status': 'success'
            }
            
        except Exception as e:
            logger.error(f"分析失败: {str(e)}")
            raise
    
    @staticmethod
    def run_clustering(X, original_df, user_id=None):
        """
        运行 KMeans++ 聚类分析
        
        聚类是一种"无监督学习"：
        - 不需要标签（不知道谁高风险谁低风险）
        - 算法根据数据之间的"距离"自动分组
        - KMeans++ 是 KMeans 的改进版，优化了初始中心点的选择
        
        流程：
        1. 先尝试 K=2~7，用轮廓系数评估哪个K最好
        2. 用最优K重新训练
        3. 保存模型(.pkl) + 保存结果到数据库
        4. 把 cluster_id 写回每条数据
        
        参数：
            X: 特征矩阵（每行一个人，每列一个特征）
            original_df: 原始DataFrame（用于统计和获取data_id）
            user_id: 触发分析的用户ID
        返回：
            dict: 聚类结果（最优K、标签、统计信息等）
        """
        try:
            # ---------- 第1步：寻找最优K值 ----------
            # 尝试把数据分成 2、3、4、5、6、7 组
            # 用"轮廓系数"评估（越接近1说明分组越清晰）
            clustering = ClusteringModel()
            optimal_k_result = clustering.find_optimal_k(X, k_range=range(2, 8))
            optimal_k = optimal_k_result['optimal_k']  # 选出分数最高的K
            
            # ---------- 第2步：用最优K值重新训练 ----------
            # 例如 optimal_k=3，就把所有人分成3个群体
            clustering = ClusteringModel(n_clusters=optimal_k)
            labels = clustering.fit(X)  # labels 是数组，如 [0,2,1,0,2,...]，每条数据的群体编号
            
            # ---------- 第3步：获取聚类统计信息 ----------
            # 包括：每个群体的大小、轮廓系数、聚类中心点坐标等
            cluster_stats = clustering.get_cluster_statistics(X, original_df)
            
            # ---------- 第4步：保存模型文件 ----------
            # 用 pickle 序列化，保存为 .pkl 文件
            # 下次可以直接加载，不用重新训练
            model_path = os.path.join(current_app.config['MODEL_PATH'], 'clustering_model.pkl')
            clustering.save(model_path)
            
            # ---------- 第5步：保存分析结果到 analysis_results 表 ----------
            # 记录这次分析的"成绩单"：用了什么算法、轮廓系数多少、训练了多少样本
            result = AnalysisResult(
                user_id=user_id,
                analysis_type='clustering',          # 分析类型：聚类
                model_name='K-Means++',              # 算法名称
                silhouette_score=float(cluster_stats['silhouette_score']),  # 轮廓系数(0~1)
                training_samples=len(X),             # 训练样本数
                features_count=X.shape[1],           # 特征数量
                model_path=model_path                # 模型文件路径
            )
            result.set_cluster_centers(cluster_stats['cluster_centers'])  # 聚类中心坐标(JSON)
            result.set_hyperparameters({              # 超参数(JSON)
                'n_clusters': optimal_k,
                'init': 'k-means++',
                'random_state': 42
            })
            
            db.session.add(result)    # 添加到数据库会话
            db.session.commit()       # 提交事务（写入数据库）
            
            # ---------- 第6步：把聚类标签写回 mental_health_data 表 ----------
            # 这样每条数据就有了 cluster_id 字段
            # 例如：data_id=1 的人属于群体0，data_id=2 的人属于群体2
            data_ids = original_df['id'].tolist()
            cluster_labels = dict(zip(data_ids, labels.tolist()))  # {data_id: cluster_id}
            DataService.update_cluster_labels(cluster_labels)
            
            # 返回聚类分析结果
            return {
                'result_id': result.id,
                'optimal_k': optimal_k,
                'labels': labels.tolist(),
                'cluster_stats': cluster_stats,
                'silhouette_scores': optimal_k_result['silhouette_scores'],
                'model_path': model_path
            }
            
        except Exception as e:
            db.session.rollback()  # 出错时回滚数据库（防止写入脏数据）
            logger.error(f"聚类分析失败: {str(e)}")
            raise
    
    @staticmethod
    def run_classification(X, original_df, user_id=None):
        """
        运行 RandomForest 分类分析
        
        分类是一种"有监督学习"：
        - 需要标签（risk_level: Low/Medium/High Risk）
        - 模型学习"什么特征对应什么风险等级"
        - 训练好的模型可以预测新人的风险
        
        RandomForest（随机森林）的原理：
        - 同时训练100棵"决策树"，每棵树从不同角度看数据
        - 最终结果由所有树"投票"决定
        - 还通过 GridSearchCV 自动寻找最优参数
        
        参数：
            X: 特征矩阵
            original_df: 原始DataFrame（包含risk_level标签列）
            user_id: 触发分析的用户ID
        返回：
            dict: 分类结果（准确率、F1分数、特征重要性等）
        """
        try:
            # ---------- 第1步：准备目标变量（标签）----------
            # risk_level 是我们要预测的目标：Low Risk / Medium Risk / High Risk
            if 'risk_level' not in original_df.columns:
                raise ValueError("数据中缺少risk_level字段")
            
            # 把文字标签编码成数字（机器学习只能处理数字）
            # Low Risk → 0, Medium Risk → 1, High Risk → 2
            risk_mapping = {'Low Risk': 0, 'Medium Risk': 1, 'High Risk': 2}
            y = original_df['risk_level'].map(risk_mapping)
            
            # 移除 risk_level 为空的行（NaN 无法参与训练）
            valid_mask = y.notna()
            X_valid = X[valid_mask]          # 过滤后的特征矩阵
            y_valid = y[valid_mask].astype(int)  # 过滤后的标签
            
            if len(y_valid) == 0:
                raise ValueError("没有足够的有效标签数据")
            
            # ---------- 第2步：训练分类模型 ----------
            # 自动做以下事情：
            #   a. 70%数据训练，30%数据测试
            #   b. StandardScaler 标准化
            #   c. GridSearchCV 网格搜索最优参数
            #   d. 用最优参数重新训练
            #   e. 在测试集上评估，计算 accuracy/precision/recall/f1
            classifier = ClassificationModel()
            metrics = classifier.fit(X_valid, y_valid, test_size=0.3, optimize=True)
            
            # ---------- 第3步：保存模型文件 ----------
            model_path = os.path.join(current_app.config['MODEL_PATH'], 'classification_model.pkl')
            classifier.save(model_path)
            
            # ---------- 第4步：保存分析结果到 analysis_results 表 ----------
            result = AnalysisResult(
                user_id=user_id,
                analysis_type='classification',
                model_name='RandomForest',
                # 四大评估指标（衡量模型好坏）
                accuracy=metrics['accuracy'],      # 准确率：预测对了的比例
                precision=metrics['precision'],    # 精确率：预测为高风险的人中真正高风险的比例
                recall=metrics['recall'],          # 召回率：真正高风险的人中被找出来的比例
                f1_score=metrics['f1_score'],      # F1分数：精确率和召回率的调和平均
                training_samples=int(len(X_valid) * 0.7),   # 训练集大小
                testing_samples=int(len(X_valid) * 0.3),    # 测试集大小
                features_count=X_valid.shape[1],            # 特征数量
                model_path=model_path
            )
            # 保存额外的JSON数据
            result.set_feature_importance(classifier.get_feature_importance())  # 哪些特征最重要
            result.set_confusion_matrix(metrics['confusion_matrix'])            # 混淆矩阵（谁被误判了）
            result.set_hyperparameters(classifier.best_params)                  # 最优超参数
            
            db.session.add(result)
            db.session.commit()
            
            return {
                'result_id': result.id,
                'metrics': metrics,
                'feature_importance': classifier.get_feature_importance(),
                'model_path': model_path
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"分类分析失败: {str(e)}")
            raise
    
    @staticmethod
    def generate_user_profiles(df, cluster_labels, user_id=None):
        """
        生成用户画像
        
        根据每条数据的特征，为每个人计算：
        - risk_score: 风险评分 (0~100)
        - risk_level: 风险等级 (High/Medium/Low Risk)
        - tags: 标签列表（如 ["青年员工", "科技公司", "家族病史"]）
        - key_features: 关键特征摘要
        - recommendations: 个性化建议
        
        参数：
            df: 经过特征工程的DataFrame
            cluster_labels: 聚类结果的标签数组
            user_id: 触发分析的用户ID
        """
        try:
            # 每次重新分析时清空旧画像（避免重复）
            UserProfile.query.delete()
            
            risk_mapping = {'Low Risk': 0, 'Medium Risk': 1, 'High Risk': 2}
            
            # 遍历每一条数据，为每个人生成画像
            for i, (idx, row) in enumerate(df.iterrows()):
                data_id = row.get('id')
                if not data_id:
                    continue
                
                # ===== 计算风险评分 (0~100) =====
                # 基础分50分，根据各项特征加减分
                risk_score = 50
                
                # 加分项（有这些特征 → 风险更高）
                if row.get('stress_index', 0) > 0.5:      # 压力指数高
                    risk_score += 15
                if row.get('family_history') == 'Yes':     # 有家族病史
                    risk_score += 10
                if row.get('treatment') == 'Yes':          # 正在接受治疗（说明已有问题）
                    risk_score += 10
                if row.get('work_interfere') in ['Often', 'Sometimes']:  # 工作经常干扰心理健康
                    risk_score += 10
                if row.get('support_score', 0) < 0.3:     # 公司支持度低
                    risk_score += 10
                
                # 限制在 0~100 范围内
                risk_score = min(100, max(0, risk_score))
                
                # ===== 确定风险等级 =====
                if risk_score >= 70:
                    risk_level = 'High Risk'     # 高风险：建议立即关注
                elif risk_score >= 40:
                    risk_level = 'Medium Risk'   # 中风险：建议持续关注
                else:
                    risk_level = 'Low Risk'      # 低风险：保持良好状态
                
                # ===== 生成标签（给人"贴标签"方便分类查看）=====
                tags = []
                if row.get('age'):
                    if row['age'] < 30:
                        tags.append('青年员工')     # 30岁以下
                    elif row['age'] < 45:
                        tags.append('中年员工')     # 30~45岁
                    else:
                        tags.append('资深员工')     # 45岁以上
                
                if row.get('tech_company') == 'Yes':
                    tags.append('科技公司')          # 在科技公司工作
                
                if row.get('remote_work') == 'Yes':
                    tags.append('远程工作')          # 远程办公
                
                if row.get('family_history') == 'Yes':
                    tags.append('家族病史')          # 有心理健康家族病史
                
                # ===== 提取关键特征（简要描述这个人的核心信息）=====
                key_features = {
                    '年龄': row.get('age'),
                    '压力指数': round(row.get('stress_index', 0), 2),
                    '支持度评分': round(row.get('support_score', 0), 2),
                    '工作干扰': row.get('work_interfere')
                }
                
                # ===== 根据风险等级给出个性化建议 =====
                recommendations = []
                if risk_score >= 70:
                    recommendations.append('建议尽快寻求专业心理咨询')
                    recommendations.append('建议与上级沟通工作压力问题')
                elif risk_score >= 40:
                    recommendations.append('建议关注心理健康状况')
                    recommendations.append('建议参加公司健康项目')
                else:
                    recommendations.append('保持良好的工作生活平衡')
                    recommendations.append('定期进行心理健康自评')
                
                # ===== 创建画像记录并存入 user_profiles 表 =====
                # 注意：用行位置 i（不是DataFrame索引 idx）来对应 cluster_labels
                cluster_label = int(cluster_labels[i]) if i < len(cluster_labels) else None
                profile = UserProfile(
                    user_id=user_id,
                    data_id=data_id,                    # 关联原始数据
                    risk_score=risk_score,              # 风险评分
                    risk_level=risk_level,              # 风险等级
                    cluster_id=cluster_label,           # 所属聚类群体
                    cluster_name=VisualizationService.get_cluster_name(cluster_label) if cluster_label is not None else None,
                    description=f'该用户风险评分为{risk_score}，属于{risk_level}群体。'
                )
                # 将列表/字典序列化为JSON字符串存入数据库
                profile.set_tags(tags)
                profile.set_key_features(key_features)
                profile.set_recommendations(recommendations)
                
                db.session.add(profile)
            
            # 一次性提交所有画像
            db.session.commit()
            logger.info(f"生成了{len(df)}个用户画像")
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"生成用户画像失败: {str(e)}")
            raise
    
    @staticmethod
    def predict_risk(features):
        """
        用已训练的分类模型预测单条数据的风险等级
        
        使用场景：
        - 前端"心理自评"页面：用户填写问卷后，预测其风险
        - 不需要重新训练，直接加载上次保存的 .pkl 模型
        
        参数：
            features: dict，包含8个特征值的字典
        返回：
            dict: 预测结果（风险等级 + 各等级概率）
        """
        try:
            # 加载上次训练保存的模型文件
            model_path = os.path.join(current_app.config['MODEL_PATH'], 'classification_model.pkl')
            
            if not os.path.exists(model_path):
                raise ValueError("模型文件不存在，请先训练模型")
            
            # 反序列化加载模型（包含 RandomForest + StandardScaler）
            classifier = ClassificationModel()
            classifier.load(model_path)
            
            # 把字典转成 DataFrame（模型要求输入是二维数组）
            X = pd.DataFrame([features])
            
            # 预测：predict 返回类别编号(0/1/2)，predict_proba 返回各类型的概率
            prediction = classifier.predict(X)[0]           # 如：1（表示 Medium Risk）
            probabilities = classifier.predict_proba(X)[0]  # 如：[0.1, 0.7, 0.2]（70%概率中风险）
            
            # 把数字编号转回文字标签
            risk_labels = ['Low Risk', 'Medium Risk', 'High Risk']
            
            return {
                'prediction': risk_labels[prediction],     # 预测的风险等级
                'probabilities': {                          # 各等级的概率
                    risk_labels[i]: float(prob) 
                    for i, prob in enumerate(probabilities)
                }
            }
            
        except Exception as e:
            logger.error(f"预测失败: {str(e)}")
            raise
    
    @staticmethod
    def get_analysis_history(analysis_type=None, limit=10):
        """
        获取分析历史记录
        
        查询 analysis_results 表，按时间倒序返回
        可按类型过滤（只看聚类/只看分类）
        
        参数：
            analysis_type: 可选，'clustering' 或 'classification'
            limit: 最多返回多少条（默认10）
        """
        query = AnalysisResult.query
        
        # 如果指定了类型，只查该类型
        if analysis_type:
            query = query.filter(AnalysisResult.analysis_type == analysis_type)
        
        # 按创建时间倒序，取前 limit 条
        results = query.order_by(AnalysisResult.created_at.desc()).limit(limit).all()
        
        # 转为字典列表
        return [r.to_dict() for r in results]
    
    @staticmethod
    def get_latest_analysis(analysis_type):
        """
        获取某类型的最新一次分析结果
        
        使用场景：
        - 报告生成时获取最新的分类模型指标
        - 前端展示最新的聚类结果
        
        参数：
            analysis_type: 'clustering' 或 'classification'
        返回：
            dict 或 None
        """
        result = AnalysisResult.query.filter_by(
            analysis_type=analysis_type
        ).order_by(AnalysisResult.created_at.desc()).first()  # 取最新的一条
        
        if not result:
            return None
        
        try:
            return result.to_dict()
        except Exception as e:
            logger.error(f"转换分析结果失败: {str(e)}")
            return None
