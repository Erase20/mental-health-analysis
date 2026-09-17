from app import db
from datetime import datetime
import json

class AnalysisResult(db.Model):
    """分析结果模型"""
    __tablename__ = 'analysis_results'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    analysis_type = db.Column(db.String(50), nullable=False)  # clustering, classification, prediction
    model_name = db.Column(db.String(100), nullable=False)
    
    # 模型性能指标
    accuracy = db.Column(db.Float, nullable=True)
    precision = db.Column(db.Float, nullable=True)
    recall = db.Column(db.Float, nullable=True)
    f1_score = db.Column(db.Float, nullable=True)
    silhouette_score = db.Column(db.Float, nullable=True)
    
    # 特征重要性 (JSON格式存储)
    feature_importance = db.Column(db.Text, nullable=True)
    
    # 混淆矩阵 (JSON格式存储)
    confusion_matrix = db.Column(db.Text, nullable=True)
    
    # 聚类中心点 (JSON格式存储)
    cluster_centers = db.Column(db.Text, nullable=True)
    
    # 超参数 (JSON格式存储)
    hyperparameters = db.Column(db.Text, nullable=True)
    
    # 训练数据信息
    training_samples = db.Column(db.Integer, nullable=True)
    testing_samples = db.Column(db.Integer, nullable=True)
    features_count = db.Column(db.Integer, nullable=True)
    
    # 模型文件路径
    model_path = db.Column(db.String(500), nullable=True)
    
    # 备注
    notes = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_feature_importance(self, data):
        """设置特征重要性"""
        self.feature_importance = json.dumps(data, ensure_ascii=False)
    
    def get_feature_importance(self):
        """获取特征重要性"""
        return json.loads(self.feature_importance) if self.feature_importance else {}
    
    def set_confusion_matrix(self, data):
        """设置混淆矩阵"""
        self.confusion_matrix = json.dumps(data, ensure_ascii=False)
    
    def get_confusion_matrix(self):
        """获取混淆矩阵"""
        return json.loads(self.confusion_matrix) if self.confusion_matrix else []
    
    def set_cluster_centers(self, data):
        """设置聚类中心"""
        self.cluster_centers = json.dumps(data, ensure_ascii=False)
    
    def get_cluster_centers(self):
        """获取聚类中心"""
        return json.loads(self.cluster_centers) if self.cluster_centers else []
    
    def set_hyperparameters(self, data):
        """设置超参数"""
        self.hyperparameters = json.dumps(data, ensure_ascii=False)
    
    def get_hyperparameters(self):
        """获取超参数"""
        return json.loads(self.hyperparameters) if self.hyperparameters else {}
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'analysis_type': self.analysis_type,
            'model_name': self.model_name,
            'accuracy': self.accuracy,
            'precision': self.precision,
            'recall': self.recall,
            'f1_score': self.f1_score,
            'silhouette_score': self.silhouette_score,
            'feature_importance': self.get_feature_importance(),
            'confusion_matrix': self.get_confusion_matrix(),
            'cluster_centers': self.get_cluster_centers(),
            'hyperparameters': self.get_hyperparameters(),
            'training_samples': self.training_samples,
            'testing_samples': self.testing_samples,
            'features_count': self.features_count,
            'model_path': self.model_path,
            'notes': self.notes,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def __repr__(self):
        return f'<AnalysisResult {self.id}>'
