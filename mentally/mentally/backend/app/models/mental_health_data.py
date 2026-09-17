from app import db
from datetime import datetime

class MentalHealthData(db.Model):
    """心理健康数据模型"""
    __tablename__ = 'mental_health_data'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # 基本信息
    timestamp = db.Column(db.DateTime, nullable=True)
    age = db.Column(db.Integer, nullable=True)
    gender = db.Column(db.String(20), nullable=True)
    country = db.Column(db.String(100), nullable=True)
    state = db.Column(db.String(100), nullable=True)
    
    # 工作情况
    self_employed = db.Column(db.String(10), nullable=True)
    family_history = db.Column(db.String(10), nullable=True)
    treatment = db.Column(db.String(10), nullable=True)
    work_interfere = db.Column(db.String(50), nullable=True)
    no_employees = db.Column(db.String(50), nullable=True)
    remote_work = db.Column(db.String(10), nullable=True)
    tech_company = db.Column(db.String(10), nullable=True)
    
    # 公司福利与支持
    benefits = db.Column(db.String(50), nullable=True)
    care_options = db.Column(db.String(50), nullable=True)
    wellness_program = db.Column(db.String(50), nullable=True)
    seek_help = db.Column(db.String(50), nullable=True)
    anonymity = db.Column(db.String(50), nullable=True)
    leave = db.Column(db.String(50), nullable=True)
    
    # 心理健康态度
    mental_health_consequence = db.Column(db.String(50), nullable=True)
    phys_health_consequence = db.Column(db.String(50), nullable=True)
    coworkers = db.Column(db.String(50), nullable=True)
    supervisor = db.Column(db.String(50), nullable=True)
    mental_health_interview = db.Column(db.String(50), nullable=True)
    phys_health_interview = db.Column(db.String(50), nullable=True)
    mental_vs_physical = db.Column(db.String(50), nullable=True)
    obs_consequence = db.Column(db.String(10), nullable=True)
    comments = db.Column(db.Text, nullable=True)
    
    # 分析结果
    risk_level = db.Column(db.String(20), nullable=True)  # High Risk, Medium Risk, Low Risk
    age_group = db.Column(db.String(20), nullable=True)
    cluster_id = db.Column(db.Integer, nullable=True)
    
    # 元数据
    is_processed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S') if self.timestamp else None,
            'age': self.age,
            'gender': self.gender,
            'country': self.country,
            'state': self.state,
            'self_employed': self.self_employed,
            'family_history': self.family_history,
            'treatment': self.treatment,
            'work_interfere': self.work_interfere,
            'no_employees': self.no_employees,
            'remote_work': self.remote_work,
            'tech_company': self.tech_company,
            'benefits': self.benefits,
            'care_options': self.care_options,
            'wellness_program': self.wellness_program,
            'seek_help': self.seek_help,
            'anonymity': self.anonymity,
            'leave': self.leave,
            'mental_health_consequence': self.mental_health_consequence,
            'phys_health_consequence': self.phys_health_consequence,
            'coworkers': self.coworkers,
            'supervisor': self.supervisor,
            'mental_health_interview': self.mental_health_interview,
            'phys_health_interview': self.phys_health_interview,
            'mental_vs_physical': self.mental_vs_physical,
            'obs_consequence': self.obs_consequence,
            'comments': self.comments,
            'risk_level': self.risk_level,
            'age_group': self.age_group,
            'cluster_id': self.cluster_id,
            'is_processed': self.is_processed,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
    
    @staticmethod
    def get_statistics():
        """获取数据统计信息"""
        from sqlalchemy import func
        
        total = MentalHealthData.query.count()
        risk_stats = db.session.query(
            MentalHealthData.risk_level,
            func.count(MentalHealthData.id)
        ).group_by(MentalHealthData.risk_level).all()
        
        gender_stats = db.session.query(
            MentalHealthData.gender,
            func.count(MentalHealthData.id)
        ).group_by(MentalHealthData.gender).all()
        
        age_stats = db.session.query(
            MentalHealthData.age_group,
            func.count(MentalHealthData.id)
        ).group_by(MentalHealthData.age_group).all()
        
        return {
            'total': total,
            'risk_distribution': {r[0]: r[1] for r in risk_stats if r[0]},
            'gender_distribution': {g[0]: g[1] for g in gender_stats if g[0]},
            'age_distribution': {a[0]: a[1] for a in age_stats if a[0]}
        }
    
    def __repr__(self):
        return f'<MentalHealthData {self.id}>'
