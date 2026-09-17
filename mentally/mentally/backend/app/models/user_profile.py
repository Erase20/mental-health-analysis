from app import db
from datetime import datetime
import json

class UserProfile(db.Model):
    """用户画像模型"""
    __tablename__ = 'user_profiles'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    data_id = db.Column(db.Integer, db.ForeignKey('mental_health_data.id'), nullable=True)
    
    # 画像标签 (JSON格式存储)
    tags = db.Column(db.Text, nullable=True)
    
    # 风险评分 (0-100)
    risk_score = db.Column(db.Float, nullable=True)
    
    # 风险等级
    risk_level = db.Column(db.String(20), nullable=True)
    
    # 所属群体
    cluster_id = db.Column(db.Integer, nullable=True)
    cluster_name = db.Column(db.String(50), nullable=True)
    
    # 特征向量 (JSON格式存储)
    feature_vector = db.Column(db.Text, nullable=True)
    
    # 关键特征 (JSON格式存储)
    key_features = db.Column(db.Text, nullable=True)
    
    # 建议 (JSON格式存储)
    recommendations = db.Column(db.Text, nullable=True)
    
    # 画像描述
    description = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联关系
    data = db.relationship('MentalHealthData', backref='profiles', lazy=True)
    
    def set_tags(self, data):
        """设置标签"""
        self.tags = json.dumps(data, ensure_ascii=False)
    
    def get_tags(self):
        """获取标签"""
        return json.loads(self.tags) if self.tags else []
    
    def set_feature_vector(self, data):
        """设置特征向量"""
        self.feature_vector = json.dumps(data, ensure_ascii=False)
    
    def get_feature_vector(self):
        """获取特征向量"""
        return json.loads(self.feature_vector) if self.feature_vector else {}
    
    def set_key_features(self, data):
        """设置关键特征"""
        self.key_features = json.dumps(data, ensure_ascii=False)
    
    def get_key_features(self):
        """获取关键特征"""
        return json.loads(self.key_features) if self.key_features else {}
    
    def set_recommendations(self, data):
        """设置建议"""
        self.recommendations = json.dumps(data, ensure_ascii=False)
    
    def get_recommendations(self):
        """获取建议"""
        return json.loads(self.recommendations) if self.recommendations else []
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'data_id': self.data_id,
            'tags': self.get_tags(),
            'risk_score': self.risk_score,
            'risk_level': self.risk_level,
            'cluster_id': self.cluster_id,
            'cluster_name': self.cluster_name,
            'feature_vector': self.get_feature_vector(),
            'key_features': self.get_key_features(),
            'recommendations': self.get_recommendations(),
            'description': self.description,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def __repr__(self):
        return f'<UserProfile {self.id}>'
