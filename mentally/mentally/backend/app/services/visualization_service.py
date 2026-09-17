import pandas as pd
import numpy as np
import json
from app.services.data_service import DataService
from app.models.mental_health_data import MentalHealthData
from app.models.user_profile import UserProfile
from sqlalchemy import func
from app import db

class VisualizationService:
    """可视化服务类"""

    CLUSTER_NAMES = {
        0: '高风险群体',
        1: '中高风险群体',
        2: '中风险群体',
        3: '低风险群体',
        4: '超低风险群体'
    }

    @staticmethod
    def get_cluster_name(cluster_id):
        """获取群体名称"""
        return VisualizationService.CLUSTER_NAMES.get(cluster_id, f'群体_{cluster_id}')

    @staticmethod
    def get_overview_stats():
        """获取概览统计数据"""
        # 快速检查是否有数据
        total = MentalHealthData.query.count()
        
        if total == 0:
            return {
                'total_samples': 0,
                'risk_distribution': {},
                'gender_distribution': {},
                'age_distribution': {},
                'cluster_distribution': {},
                'country_distribution': {}
            }
        
        # 风险等级分布
        risk_dist = db.session.query(
            MentalHealthData.risk_level,
            func.count(MentalHealthData.id)
        ).group_by(MentalHealthData.risk_level).all()
        
        # 性别分布
        gender_dist = db.session.query(
            MentalHealthData.gender,
            func.count(MentalHealthData.id)
        ).group_by(MentalHealthData.gender).all()
        
        # 年龄分布
        age_dist = db.session.query(
            MentalHealthData.age_group,
            func.count(MentalHealthData.id)
        ).group_by(MentalHealthData.age_group).all()
        
        # 聚类分布
        cluster_dist = db.session.query(
            MentalHealthData.cluster_id,
            func.count(MentalHealthData.id)
        ).group_by(MentalHealthData.cluster_id).all()
        
        # 国家分布 (Top 10)
        country_dist = db.session.query(
            MentalHealthData.country,
            func.count(MentalHealthData.id)
        ).group_by(MentalHealthData.country).order_by(func.count(MentalHealthData.id).desc()).limit(10).all()
        
        return {
            'total_samples': total,
            'risk_distribution': {r[0]: r[1] for r in risk_dist if r[0]},
            'gender_distribution': {g[0]: g[1] for g in gender_dist if g[0]},
            'age_distribution': {a[0]: a[1] for a in age_dist if a[0]},
            'cluster_distribution': {VisualizationService.get_cluster_name(c[0]): c[1] for c in cluster_dist if c[0] is not None},
            'country_distribution': {c[0]: c[1] for c in country_dist if c[0]}
        }
    
    @staticmethod
    def get_risk_analysis():
        """获取风险分析数据"""
        df = DataService.get_dataframe(limit=5000)
        
        if df.empty:
            return {
                'risk_by_age': {'categories': [], 'series': []},
                'risk_by_gender': {'categories': [], 'series': []},
                'risk_by_company_size': {'categories': [], 'series': []},
                'risk_by_remote_work': {'categories': [], 'series': []}
            }
        
        # 风险与年龄关系
        risk_age = df.groupby(['age_group', 'risk_level']).size().unstack(fill_value=0)
        
        # 风险与性别关系
        risk_gender = df.groupby(['gender', 'risk_level']).size().unstack(fill_value=0)
        
        # 风险与公司规模关系
        risk_company = df.groupby(['no_employees', 'risk_level']).size().unstack(fill_value=0)
        
        # 风险与远程工作关系
        risk_remote = df.groupby(['remote_work', 'risk_level']).size().unstack(fill_value=0)
        
        return {
            'risk_by_age': {
                'categories': risk_age.index.tolist(),
                'series': [
                    {'name': col, 'data': risk_age[col].tolist()}
                    for col in risk_age.columns
                ]
            },
            'risk_by_gender': {
                'categories': risk_gender.index.tolist(),
                'series': [
                    {'name': col, 'data': risk_gender[col].tolist()}
                    for col in risk_gender.columns
                ]
            },
            'risk_by_company_size': {
                'categories': risk_company.index.tolist(),
                'series': [
                    {'name': col, 'data': risk_company[col].tolist()}
                    for col in risk_company.columns
                ]
            },
            'risk_by_remote_work': {
                'categories': risk_remote.index.tolist(),
                'series': [
                    {'name': col, 'data': risk_remote[col].tolist()}
                    for col in risk_remote.columns
                ]
            }
        }
    
    @staticmethod
    def get_cluster_analysis():
        """获取聚类分析数据"""
        df = DataService.get_dataframe(limit=5000)
        
        if df.empty or 'cluster_id' not in df.columns or df['cluster_id'].isna().all():
            return {
                'cluster_stats': [],
                'cluster_features': {}
            }
        
        # 聚类基本统计
        cluster_stats = df.groupby('cluster_id').agg({
            'age': 'mean',
            'risk_level': lambda x: x.mode()[0] if not x.mode().empty else 'Unknown'
        }).reset_index()
        
        # 聚类特征分布
        cluster_features = {}
        for cluster_id in df['cluster_id'].dropna().unique():
            cluster_data = df[df['cluster_id'] == cluster_id]
            cluster_features[int(cluster_id)] = {
                'size': len(cluster_data),
                'avg_age': round(cluster_data['age'].mean(), 1) if 'age' in cluster_data.columns else 0,
                'gender_dist': cluster_data['gender'].value_counts().to_dict() if 'gender' in cluster_data.columns else {},
                'risk_dist': cluster_data['risk_level'].value_counts().to_dict() if 'risk_level' in cluster_data.columns else {},
                'top_country': cluster_data['country'].mode()[0] if not cluster_data['country'].mode().empty and 'country' in cluster_data.columns else 'Unknown',
                'treatment_rate': round((cluster_data['treatment'] == 'Yes').mean() * 100, 1) if 'treatment' in cluster_data.columns else 0,
                'remote_work_rate': round((cluster_data['remote_work'] == 'Yes').mean() * 100, 1) if 'remote_work' in cluster_data.columns else 0,
                'tech_company_rate': round((cluster_data['tech_company'] == 'Yes').mean() * 100, 1) if 'tech_company' in cluster_data.columns else 0
            }

        return {
            'cluster_stats': cluster_stats.to_dict('records'),
            'cluster_features': cluster_features
        }
    
    @staticmethod
    def get_feature_analysis():
        """获取特征分析数据"""
        df = DataService.get_dataframe(limit=5000)
        
        if df.empty:
            return {
                'treatment_distribution': {},
                'family_history_distribution': {},
                'work_interfere_distribution': {},
                'benefits_distribution': {},
                'remote_work_distribution': {},
                'tech_company_distribution': {}
            }
        
        # 治疗情况分布
        treatment_dist = df['treatment'].value_counts().to_dict() if 'treatment' in df.columns else {}
        
        # 家族病史分布
        family_dist = df['family_history'].value_counts().to_dict() if 'family_history' in df.columns else {}
        
        # 工作干扰分布
        work_interfere_dist = df['work_interfere'].value_counts().to_dict() if 'work_interfere' in df.columns else {}
        
        # 公司福利分布
        benefits_dist = df['benefits'].value_counts().to_dict() if 'benefits' in df.columns else {}
        
        # 远程工作分布
        remote_dist = df['remote_work'].value_counts().to_dict() if 'remote_work' in df.columns else {}
        
        # 技术公司分布
        tech_dist = df['tech_company'].value_counts().to_dict() if 'tech_company' in df.columns else {}
        
        return {
            'treatment_distribution': treatment_dist,
            'family_history_distribution': family_dist,
            'work_interfere_distribution': work_interfere_dist,
            'benefits_distribution': benefits_dist,
            'remote_work_distribution': remote_dist,
            'tech_company_distribution': tech_dist
        }
    
    @staticmethod
    def get_correlation_data():
        """获取相关性数据"""
        df = DataService.get_dataframe(limit=5000)
        
        if df.empty:
            return {'categories': [], 'data': []}
        
        # 选择数值型和相关类别特征
        features = []
        
        # 年龄特征
        if 'age' in df.columns:
            features.append('age')
        
        # 聚类ID特征
        if 'cluster_id' in df.columns:
            features.append('cluster_id')
        
        # 编码风险等级
        if 'risk_level' in df.columns:
            risk_mapping = {'Low Risk': 0, 'Medium Risk': 1, 'High Risk': 2}
            df['risk_level_encoded'] = df['risk_level'].map(risk_mapping)
            features.append('risk_level_encoded')
        
        # 编码性别
        if 'gender' in df.columns:
            gender_mapping = {'Male': 0, 'Female': 1, 'Non-binary': 2, 'Prefer not to say': 3}
            df['gender_encoded'] = df['gender'].map(gender_mapping)
            features.append('gender_encoded')
        
        # 编码治疗情况
        if 'treatment' in df.columns:
            treatment_mapping = {'Yes': 1, 'No': 0}
            df['treatment_encoded'] = df['treatment'].map(treatment_mapping)
            features.append('treatment_encoded')
        
        # 计算相关性
        if not features or len(features) < 2:
            return {'categories': [], 'data': []}
        
        numeric_df = df[features].dropna()
        
        if numeric_df.empty or numeric_df.shape[1] < 2:
            return {'categories': [], 'data': []}
        
        corr_matrix = numeric_df.corr()
        
        # 转换为ECharts热力图格式
        categories = corr_matrix.columns.tolist()
        data = []
        for i, row in enumerate(corr_matrix.values):
            for j, val in enumerate(row):
                data.append([i, j, round(val, 2)])
        
        return {
            'categories': categories,
            'data': data
        }
    
    @staticmethod
    def get_geo_distribution():
        """获取地理分布数据"""
        country_dist = db.session.query(
            MentalHealthData.country,
            func.count(MentalHealthData.id)
        ).group_by(MentalHealthData.country).all()
        
        # 转换为地图数据格式
        geo_data = []
        for country, count in country_dist:
            if country:
                geo_data.append({
                    'name': country,
                    'value': count
                })
        
        return geo_data
    
    @staticmethod
    def get_trend_data():
        """获取趋势数据"""
        # 按时间统计
        trend = db.session.query(
            func.date_format(MentalHealthData.timestamp, '%Y-%m'),
            MentalHealthData.risk_level,
            func.count(MentalHealthData.id)
        ).filter(MentalHealthData.timestamp.isnot(None)).group_by(
            func.date_format(MentalHealthData.timestamp, '%Y-%m'),
            MentalHealthData.risk_level
        ).order_by(func.date_format(MentalHealthData.timestamp, '%Y-%m')).all()
        
        # 整理数据
        months = sorted(set([t[0] for t in trend]))
        risk_levels = ['Low Risk', 'Medium Risk', 'High Risk']
        
        series_data = {rl: [] for rl in risk_levels}
        
        for month in months:
            month_data = {t[1]: t[2] for t in trend if t[0] == month}
            for rl in risk_levels:
                series_data[rl].append(month_data.get(rl, 0))
        
        return {
            'months': months,
            'series': [
                {'name': rl, 'data': series_data[rl]}
                for rl in risk_levels
            ]
        }
    
    @staticmethod
    def get_radar_data(cluster_id=None):
        """获取雷达图数据"""
        df = DataService.get_dataframe(limit=5000)
        
        if df.empty:
            return {
                'dimensions': [
                    {'name': '工作支持度', 'max': 100},
                    {'name': '心理健康意识', 'max': 100},
                    {'name': '治疗意愿', 'max': 100},
                    {'name': '工作灵活性', 'max': 100},
                    {'name': '社会支持', 'max': 100}
                ],
                'values': [0, 0, 0, 0, 0]
            }
        
        if cluster_id is not None:
            df = df[df['cluster_id'] == cluster_id]
            if df.empty:
                return {
                    'dimensions': [
                        {'name': '工作支持度', 'max': 100},
                        {'name': '心理健康意识', 'max': 100},
                        {'name': '治疗意愿', 'max': 100},
                        {'name': '工作灵活性', 'max': 100},
                        {'name': '社会支持', 'max': 100}
                    ],
                    'values': [0, 0, 0, 0, 0]
                }
        
        # 计算各维度得分
        dimensions = [
            {'name': '工作支持度', 'max': 100},
            {'name': '心理健康意识', 'max': 100},
            {'name': '治疗意愿', 'max': 100},
            {'name': '工作灵活性', 'max': 100},
            {'name': '社会支持', 'max': 100}
        ]
        
        # 工作支持度
        support_score = 0
        if 'benefits' in df.columns:
            support_score += (df['benefits'] == 'Yes').mean() * 25
        if 'wellness_program' in df.columns:
            support_score += (df['wellness_program'] == 'Yes').mean() * 25
        if 'seek_help' in df.columns:
            support_score += (df['seek_help'] == 'Yes').mean() * 25
        if 'anonymity' in df.columns:
            support_score += (df['anonymity'] == 'Yes').mean() * 25
        
        # 心理健康意识
        awareness_score = 0
        if 'mental_health_consequence' in df.columns:
            awareness_score += (df['mental_health_consequence'] == 'No').mean() * 50
        if 'mental_vs_physical' in df.columns:
            awareness_score += (df['mental_vs_physical'] == 'Yes').mean() * 50
        
        # 治疗意愿
        treatment_score = (df['treatment'] == 'Yes').mean() * 100 if 'treatment' in df.columns else 0
        
        # 工作灵活性
        flexibility_score = (df['remote_work'] == 'Yes').mean() * 100 if 'remote_work' in df.columns else 0
        
        # 社会支持
        social_score = 0
        if 'coworkers' in df.columns:
            social_score += (df['coworkers'].isin(['Yes', 'Some of them'])).mean() * 50
        if 'supervisor' in df.columns:
            social_score += (df['supervisor'].isin(['Yes', 'Some of them'])).mean() * 50
        
        values = [
            round(support_score, 1),
            round(awareness_score, 1),
            round(treatment_score, 1),
            round(flexibility_score, 1),
            round(social_score, 1)
        ]
        
        return {
            'dimensions': dimensions,
            'values': values
        }
    
    @staticmethod
    def get_profile_data(profile_id=None, data_id=None):
        """获取用户画像数据"""
        from app.services.profile_service import ProfileService
        
        profile = None
        if profile_id:
            profile = UserProfile.query.get(profile_id)
            # 如果 UserProfile 中没有，尝试用 profile_id 作为 data_id 从 MentalHealthData 获取
            if not profile:
                data = MentalHealthData.query.get(profile_id)
                if data:
                    return {
                        'profile': ProfileService._build_profile_from_data(data),
                        'raw_data': data.to_dict()
                    }
        elif data_id:
            profile = UserProfile.query.filter_by(data_id=data_id).first()
            if not profile:
                data = MentalHealthData.query.get(data_id)
                if data:
                    return {
                        'profile': ProfileService._build_profile_from_data(data),
                        'raw_data': data.to_dict()
                    }
        else:
            return None
        
        if not profile:
            return None
        
        # 获取原始数据
        data = MentalHealthData.query.get(profile.data_id)
        
        return {
            'profile': profile.to_dict(),
            'raw_data': data.to_dict() if data else None
        }
    
    @staticmethod
    def get_comparison_data(cluster_ids):
        """获取群体对比数据"""
        df = DataService.get_dataframe(limit=5000)
        
        if df.empty:
            return {}
        
        comparison = {}
        for cluster_id in cluster_ids:
            cluster_data = df[df['cluster_id'] == cluster_id]
            
            if cluster_data.empty:
                continue
            
            comparison[VisualizationService.get_cluster_name(cluster_id)] = {
                'size': len(cluster_data),
                'avg_age': round(cluster_data['age'].mean(), 1) if 'age' in cluster_data.columns else 0,
                'risk_distribution': cluster_data['risk_level'].value_counts().to_dict() if 'risk_level' in cluster_data.columns else {},
                'gender_distribution': cluster_data['gender'].value_counts().to_dict() if 'gender' in cluster_data.columns else {},
                'treatment_rate': round((cluster_data['treatment'] == 'Yes').mean() * 100, 1) if 'treatment' in cluster_data.columns else 0,
                'remote_work_rate': round((cluster_data['remote_work'] == 'Yes').mean() * 100, 1) if 'remote_work' in cluster_data.columns else 0,
                'tech_company_rate': round((cluster_data['tech_company'] == 'Yes').mean() * 100, 1) if 'tech_company' in cluster_data.columns else 0
            }
        
        return comparison
