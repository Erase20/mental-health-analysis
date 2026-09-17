from app import db
from app.models.user_profile import UserProfile
from app.models.mental_health_data import MentalHealthData
from sqlalchemy import func
from app.services.visualization_service import VisualizationService
from app.ml.feature_engineering import FeatureEngineer
from app.ml.classification import ClassificationModel
import json
import os
import logging

logger = logging.getLogger(__name__)

class ProfileService:
    """用户画像服务类"""
    
    @staticmethod
    def _build_profile_from_data(record):
        """从 MentalHealthData 记录构建画像数据"""
        # 计算风险评分
        risk_score = 50
        if record.family_history == 'Yes':
            risk_score += 10
        if record.treatment == 'Yes':
            risk_score += 10
        if record.work_interfere in ['Often', 'Sometimes']:
            risk_score += 10
        risk_score = min(100, max(0, risk_score))
        
        # 确定风险等级
        if record.risk_level:
            risk_level = record.risk_level
        elif risk_score >= 70:
            risk_level = 'High Risk'
        elif risk_score >= 40:
            risk_level = 'Medium Risk'
        else:
            risk_level = 'Low Risk'
        
        # 生成标签
        tags = []
        if record.age:
            if record.age < 30:
                tags.append('青年员工')
            elif record.age < 45:
                tags.append('中年员工')
            else:
                tags.append('资深员工')
        if record.tech_company == 'Yes':
            tags.append('科技公司')
        if record.remote_work == 'Yes':
            tags.append('远程工作')
        if record.family_history == 'Yes':
            tags.append('家族病史')
        
        # 关键特征
        key_features = {
            '年龄': record.age,
            '性别': record.gender,
            '工作干扰': record.work_interfere,
            '家族病史': record.family_history
        }
        
        # 建议
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
        
        cluster_name = VisualizationService.get_cluster_name(record.cluster_id) if record.cluster_id is not None else None
        
        return {
            'id': record.id,
            'user_id': None,
            'data_id': record.id,
            'tags': tags,
            'risk_score': risk_score,
            'risk_level': risk_level,
            'cluster_id': record.cluster_id,
            'cluster_name': cluster_name,
            'feature_vector': {},
            'key_features': key_features,
            'recommendations': recommendations,
            'description': f'该用户风险评分为{risk_score}，属于{risk_level}群体。',
            'created_at': record.created_at.strftime('%Y-%m-%d %H:%M:%S') if record.created_at else None,
            'updated_at': record.updated_at.strftime('%Y-%m-%d %H:%M:%S') if record.updated_at else None
        }
    
    @staticmethod
    def get_profile_list(page=1, per_page=20, risk_level=None, cluster_id=None):
        """获取画像列表"""
        # 优先从 UserProfile 表查询
        has_profiles = UserProfile.query.first() is not None
        
        if has_profiles:
            query = UserProfile.query
            
            if risk_level:
                query = query.filter(UserProfile.risk_level == risk_level)
            
            if cluster_id is not None:
                query = query.filter(UserProfile.cluster_id == cluster_id)
            
            pagination = query.order_by(UserProfile.risk_score.desc()).paginate(
                page=page, per_page=per_page, error_out=False
            )
            
            return {
                'items': [item.to_dict() for item in pagination.items],
                'total': pagination.total,
                'pages': pagination.pages,
                'current_page': page
            }
        else:
            # UserProfile 表为空时，从 MentalHealthData 表生成画像数据
            query = MentalHealthData.query
            
            if risk_level:
                query = query.filter(MentalHealthData.risk_level == risk_level)
            
            if cluster_id is not None:
                query = query.filter(MentalHealthData.cluster_id == cluster_id)
            
            pagination = query.order_by(MentalHealthData.id.desc()).paginate(
                page=page, per_page=per_page, error_out=False
            )
            
            return {
                'items': [ProfileService._build_profile_from_data(item) for item in pagination.items],
                'total': pagination.total,
                'pages': pagination.pages,
                'current_page': page
            }
    
    @staticmethod
    def get_profile_by_id(profile_id):
        """根据ID获取画像"""
        profile = UserProfile.query.get(profile_id)
        if profile:
            return profile.to_dict()
        
        # UserProfile 中没有，尝试从 MentalHealthData 获取
        data = MentalHealthData.query.get(profile_id)
        if data:
            return ProfileService._build_profile_from_data(data)
        return None
    
    @staticmethod
    def get_profile_by_data_id(data_id):
        """根据数据ID获取画像"""
        profile = UserProfile.query.filter_by(data_id=data_id).first()
        if profile:
            return profile.to_dict()
        
        # UserProfile 中没有，尝试从 MentalHealthData 获取
        data = MentalHealthData.query.get(data_id)
        if data:
            return ProfileService._build_profile_from_data(data)
        return None
    
    @staticmethod
    def get_profile_statistics():
        """获取画像统计信息"""
        # 从 MentalHealthData 表获取统计数据（因为 UserProfile 表可能为空）
        total_profiles = MentalHealthData.query.count()

        # 风险等级分布
        risk_dist = db.session.query(
            MentalHealthData.risk_level,
            func.count(MentalHealthData.id)
        ).group_by(MentalHealthData.risk_level).all()

        # 聚类分布
        cluster_dist = db.session.query(
            MentalHealthData.cluster_id,
            func.count(MentalHealthData.id)
        ).group_by(MentalHealthData.cluster_id).all()

        # 风险评分分布（从 UserProfile 表获取，如果有的话）
        risk_scores = db.session.query(UserProfile.risk_score).all()
        risk_score_list = [r[0] for r in risk_scores if r[0] is not None]

        return {
            'total': total_profiles,
            'risk_distribution': {r[0]: r[1] for r in risk_dist if r[0]},
            'cluster_distribution': {VisualizationService.get_cluster_name(c[0]): c[1] for c in cluster_dist if c[0] is not None},
            'risk_score_stats': {
                'min': min(risk_score_list) if risk_score_list else 0,
                'max': max(risk_score_list) if risk_score_list else 100,
                'avg': sum(risk_score_list) / len(risk_score_list) if risk_score_list else 50
            }
        }
    
    @staticmethod
    def search_profiles(keyword, page=1, per_page=20):
        """搜索画像"""
        has_profiles = UserProfile.query.first() is not None
        
        if has_profiles:
            # 通过关联的数据进行搜索
            query = UserProfile.query.join(
                MentalHealthData, 
                UserProfile.data_id == MentalHealthData.id
            ).filter(
                db.or_(
                    MentalHealthData.country.contains(keyword),
                    MentalHealthData.state.contains(keyword),
                    MentalHealthData.gender.contains(keyword)
                )
            )
            
            pagination = query.paginate(page=page, per_page=per_page, error_out=False)
            
            return {
                'items': [item.to_dict() for item in pagination.items],
                'total': pagination.total,
                'pages': pagination.pages,
                'current_page': page
            }
        else:
            # UserProfile 为空时，直接从 MentalHealthData 搜索
            query = MentalHealthData.query.filter(
                db.or_(
                    MentalHealthData.country.contains(keyword),
                    MentalHealthData.state.contains(keyword),
                    MentalHealthData.gender.contains(keyword)
                )
            )
            
            pagination = query.paginate(page=page, per_page=per_page, error_out=False)
            
            return {
                'items': [ProfileService._build_profile_from_data(item) for item in pagination.items],
                'total': pagination.total,
                'pages': pagination.pages,
                'current_page': page
            }
    
    @staticmethod
    def get_similar_profiles(profile_id, limit=5):
        """获取相似画像"""
        has_profiles = UserProfile.query.first() is not None
        
        if has_profiles:
            profile = UserProfile.query.get(profile_id)
            if profile:
                # 基于同一聚类和风险等级查找相似画像
                similar = UserProfile.query.filter(
                    UserProfile.cluster_id == profile.cluster_id,
                    UserProfile.risk_level == profile.risk_level,
                    UserProfile.id != profile.id
                ).limit(limit).all()
                
                return [p.to_dict() for p in similar]
        
        # 从 MentalHealthData 查找相似画像
        data = MentalHealthData.query.get(profile_id)
        if not data:
            return []
        
        query = MentalHealthData.query.filter(MentalHealthData.id != data.id)
        if data.cluster_id is not None:
            query = query.filter(MentalHealthData.cluster_id == data.cluster_id)
        if data.risk_level:
            query = query.filter(MentalHealthData.risk_level == data.risk_level)
        
        similar = query.limit(limit).all()
        return [ProfileService._build_profile_from_data(item) for item in similar]
    
    @staticmethod
    def get_profile_tags():
        """获取所有标签"""
        has_profiles = UserProfile.query.first() is not None
        
        if has_profiles:
            profiles = UserProfile.query.all()
            all_tags = {}
            for profile in profiles:
                tags = profile.get_tags()
                for tag in tags:
                    all_tags[tag] = all_tags.get(tag, 0) + 1
            return all_tags
        
        # 从 MentalHealthData 生成标签
        records = MentalHealthData.query.all()
        all_tags = {}
        for record in records:
            profile_data = ProfileService._build_profile_from_data(record)
            for tag in profile_data['tags']:
                all_tags[tag] = all_tags.get(tag, 0) + 1
        return all_tags
    
    @staticmethod
    def generate_self_assessment(form_data, user_id=None):
        """根据用户填写的数据生成自评画像"""
        import pandas as pd
        from flask import current_app

        # 1. 构建单行 DataFrame 用于特征工程
        row = {
            'id': 0,
            'age': form_data.get('age'),
            'gender': form_data.get('gender'),
            'country': form_data.get('country', 'Unknown'),
            'state': form_data.get('state', ''),
            'self_employed': form_data.get('self_employed'),
            'family_history': form_data.get('family_history'),
            'treatment': form_data.get('treatment'),
            'work_interfere': form_data.get('work_interfere'),
            'no_employees': form_data.get('no_employees'),
            'remote_work': form_data.get('remote_work'),
            'tech_company': form_data.get('tech_company'),
            'benefits': form_data.get('benefits'),
            'care_options': form_data.get('care_options'),
            'wellness_program': form_data.get('wellness_program'),
            'seek_help': form_data.get('seek_help'),
            'anonymity': form_data.get('anonymity'),
            'leave': form_data.get('leave'),
            'mental_health_consequence': form_data.get('mental_health_consequence'),
            'phys_health_consequence': form_data.get('phys_health_consequence'),
            'coworkers': form_data.get('coworkers'),
            'supervisor': form_data.get('supervisor'),
            'mental_health_interview': form_data.get('mental_health_interview'),
            'phys_health_interview': form_data.get('phys_health_interview'),
            'mental_vs_physical': form_data.get('mental_vs_physical'),
            'obs_consequence': form_data.get('obs_consequence'),
        }
        df = pd.DataFrame([row])

        # 2. 特征工程
        feature_engineer = FeatureEngineer()
        df_features = feature_engineer.create_features(df)

        feature_cols = [
            'age', 'support_score', 'stress_index', 'company_size_encoded',
            'attitude_score', 'family_treatment_interaction',
            'remote_tech_interaction', 'has_observed_consequence'
        ]
        available_cols = [col for col in feature_cols if col in df_features.columns]

        # 3. 尝试用分类模型预测风险
        prediction = None
        probabilities = None
        try:
            model_path = os.path.join(current_app.config['MODEL_PATH'], 'classification_model.pkl')
            if os.path.exists(model_path):
                classifier = ClassificationModel()
                classifier.load(model_path)
                X = df_features[available_cols].fillna(0)
                pred = classifier.predict(X)[0]
                proba = classifier.predict_proba(X)[0]
                risk_labels = ['Low Risk', 'Medium Risk', 'High Risk']
                prediction = risk_labels[pred]
                probabilities = {risk_labels[i]: round(float(p), 4) for i, p in enumerate(proba)}
        except Exception as e:
            logger.warning(f"分类模型预测失败，使用规则评分: {e}")

        # 4. 计算风险评分（规则 + 模型结合）
        risk_score = 50
        if form_data.get('family_history') == 'Yes':
            risk_score += 10
        if form_data.get('treatment') == 'Yes':
            risk_score += 10
        if form_data.get('work_interfere') in ['Often', 'Sometimes']:
            risk_score += 10
        if form_data.get('obs_consequence') == 'Yes':
            risk_score += 10
        if form_data.get('mental_health_consequence') == 'Yes':
            risk_score += 5
        # 根据压力指数和支持度微调
        if 'stress_index' in df_features.columns:
            stress = float(df_features['stress_index'].iloc[0])
            risk_score += int(stress * 15)
        if 'support_score' in df_features.columns:
            support = float(df_features['support_score'].iloc[0])
            risk_score -= int(support * 10)
        risk_score = min(100, max(0, risk_score))

        # 确定风险等级：优先使用模型预测
        if prediction:
            risk_level = prediction
        elif risk_score >= 70:
            risk_level = 'High Risk'
        elif risk_score >= 40:
            risk_level = 'Medium Risk'
        else:
            risk_level = 'Low Risk'

        # 5. 生成标签
        tags = []
        age = form_data.get('age')
        if age:
            if age < 30:
                tags.append('青年员工')
            elif age < 45:
                tags.append('中年员工')
            else:
                tags.append('资深员工')
        if form_data.get('tech_company') == 'Yes':
            tags.append('科技公司')
        if form_data.get('remote_work') == 'Yes':
            tags.append('远程工作')
        if form_data.get('family_history') == 'Yes':
            tags.append('家族病史')
        if form_data.get('self_employed') == 'Yes':
            tags.append('自雇人士')
        if form_data.get('treatment') == 'Yes':
            tags.append('正在治疗')
        if form_data.get('benefits') == 'Yes':
            tags.append('公司有福利')

        # 6. 关键特征
        key_features = {
            '年龄': form_data.get('age'),
            '性别': form_data.get('gender'),
            '家族病史': form_data.get('family_history'),
            '是否治疗': form_data.get('treatment'),
            '工作干扰': form_data.get('work_interfere'),
            '远程工作': form_data.get('remote_work'),
        }
        if 'stress_index' in df_features.columns:
            key_features['压力指数'] = round(float(df_features['stress_index'].iloc[0]), 2)
        if 'support_score' in df_features.columns:
            key_features['支持度评分'] = round(float(df_features['support_score'].iloc[0]), 2)
        if 'attitude_score' in df_features.columns:
            key_features['态度评分'] = round(float(df_features['attitude_score'].iloc[0]), 2)

        # 7. 建议
        recommendations = []
        if risk_level == 'High Risk':
            recommendations.append('建议尽快寻求专业心理咨询')
            recommendations.append('建议与上级沟通工作压力问题')
            recommendations.append('考虑调整工作节奏，避免过度劳累')
        elif risk_level == 'Medium Risk':
            recommendations.append('建议关注心理健康状况')
            recommendations.append('建议参加公司健康项目')
            recommendations.append('保持良好的社交与支持网络')
        else:
            recommendations.append('保持良好的工作生活平衡')
            recommendations.append('定期进行心理健康自评')
            recommendations.append('继续保持积极的心态与生活习惯')

        if form_data.get('work_interfere') in ['Often', 'Sometimes']:
            recommendations.append('工作对心理健康有较大干扰，建议寻求职场支持')
        if form_data.get('benefits') != 'Yes':
            recommendations.append('了解公司是否提供心理健康福利与EAP服务')

        return_data = {
            'risk_score': risk_score,
            'risk_level': risk_level,
            'prediction': prediction,
            'probabilities': probabilities,
            'tags': tags,
            'key_features': key_features,
            'recommendations': recommendations,
            'description': f'您的风险评分为{risk_score}，属于{risk_level}群体。'
                           + ('模型预测结果与之一致。' if prediction == risk_level else f'模型预测为{prediction}。' if prediction else '基于规则评分。')
        }

        # 将自评结果存入 UserProfile
        # data_id=None 表示这是自评生成的画像（非系统分析）
        try:
            # 将原始表单数据和模型预测结果存入 feature_vector
            feature_data = dict(form_data)
            if prediction:
                feature_data['_prediction'] = prediction
            if probabilities:
                feature_data['_probabilities'] = probabilities

            profile = UserProfile(
                user_id=int(user_id) if user_id else None,
                data_id=None,
                risk_score=risk_score,
                risk_level=risk_level,
                tags=json.dumps(tags, ensure_ascii=False),
                key_features=json.dumps(key_features, ensure_ascii=False),
                feature_vector=json.dumps(feature_data, ensure_ascii=False),
                recommendations=json.dumps(recommendations, ensure_ascii=False),
                description=return_data['description']
            )
            db.session.add(profile)
            db.session.commit()
            return_data['assessment_id'] = profile.id
        except Exception as e:
            db.session.rollback()
            logger.warning(f"保存自评记录失败: {e}")

        return return_data

    @staticmethod
    def get_profiles_by_tag(tag, page=1, per_page=20):
        """根据标签获取画像"""
        has_profiles = UserProfile.query.first() is not None
        
        if has_profiles:
            # 由于标签存储在JSON中，需要在Python中过滤
            all_profiles = UserProfile.query.all()
            filtered = [p for p in all_profiles if tag in p.get_tags()]
            
            # 手动分页
            total = len(filtered)
            start = (page - 1) * per_page
            end = start + per_page
            items = filtered[start:end]
            
            return {
                'items': [item.to_dict() for item in items],
                'total': total,
                'pages': (total + per_page - 1) // per_page,
                'current_page': page
            }
        else:
            # 从 MentalHealthData 按标签过滤
            all_records = MentalHealthData.query.all()
            filtered = []
            for record in all_records:
                profile_data = ProfileService._build_profile_from_data(record)
                if tag in profile_data['tags']:
                    filtered.append(profile_data)
            
            total = len(filtered)
            start = (page - 1) * per_page
            end = start + per_page
            items = filtered[start:end]
            
            return {
                'items': items,
                'total': total,
                'pages': (total + per_page - 1) // per_page,
                'current_page': page
            }
