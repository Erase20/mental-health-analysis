import pandas as pd
import numpy as np
from datetime import datetime
from app import db
from app.models.mental_health_data import MentalHealthData
from sqlalchemy import func
import logging

logger = logging.getLogger(__name__)

class DataService:
    """数据服务类"""
    
    @staticmethod
    def import_from_csv(file_path):
        """从CSV文件导入数据"""
        try:
            df = pd.read_csv(file_path, encoding='utf-8')
            return DataService.import_from_dataframe(df)
        except Exception as e:
            logger.error(f"导入CSV失败: {str(e)}")
            raise
    
    @staticmethod
    def import_from_dataframe(df):
        """从DataFrame导入数据"""
        try:
            # 数据清洗
            df = DataService.clean_data(df)
            
            # 预先建立列名映射，提高性能
            column_mapping = {}
            for col in df.columns:
                column_mapping[col.lower()] = col
            
            def get_value(row, col_name):
                col_lower = col_name.lower()
                if col_lower in column_mapping:
                    actual_col = column_mapping[col_lower]
                    return row[actual_col]
                return None
            
            # 批量插入，使用更高效的方法
            batch_size = 1000
            total_imported = 0
            
            for i in range(0, len(df), batch_size):
                batch_df = df.iloc[i:i+batch_size]
                records = []
                
                for _, row in batch_df.iterrows():
                    record = MentalHealthData(
                        timestamp=pd.to_datetime(get_value(row, 'Timestamp')) if pd.notna(get_value(row, 'Timestamp')) else None,
                        age=int(get_value(row, 'Age')) if pd.notna(get_value(row, 'Age')) else None,
                        gender=get_value(row, 'Gender'),
                        country=get_value(row, 'Country'),
                        state=get_value(row, 'state'),
                        self_employed=get_value(row, 'self_employed'),
                        family_history=get_value(row, 'family_history'),
                        treatment=get_value(row, 'treatment'),
                        work_interfere=get_value(row, 'work_interfere'),
                        no_employees=get_value(row, 'no_employees'),
                        remote_work=get_value(row, 'remote_work'),
                        tech_company=get_value(row, 'tech_company'),
                        benefits=get_value(row, 'benefits'),
                        care_options=get_value(row, 'care_options'),
                        wellness_program=get_value(row, 'wellness_program'),
                        seek_help=get_value(row, 'seek_help'),
                        anonymity=get_value(row, 'anonymity'),
                        leave=get_value(row, 'leave'),
                        mental_health_consequence=get_value(row, 'mental_health_consequence'),
                        phys_health_consequence=get_value(row, 'phys_health_consequence'),
                        coworkers=get_value(row, 'coworkers'),
                        supervisor=get_value(row, 'supervisor'),
                        mental_health_interview=get_value(row, 'mental_health_interview'),
                        phys_health_interview=get_value(row, 'phys_health_interview'),
                        mental_vs_physical=get_value(row, 'mental_vs_physical'),
                        obs_consequence=get_value(row, 'obs_consequence'),
                        comments=get_value(row, 'comments'),
                        risk_level=get_value(row, 'Risk_Level'),
                        age_group=get_value(row, 'Age_Group'),
                        is_processed=True
                    )
                    records.append(record)
                
                # 批量保存
                db.session.bulk_save_objects(records)
                db.session.commit()
                total_imported += len(records)
                logger.info(f"已导入 {total_imported}/{len(df)} 条数据")
            
            return total_imported
        except Exception as e:
            db.session.rollback()
            logger.error(f"导入数据失败: {str(e)}")
            raise
    
    @staticmethod
    def clean_data(df):
        """数据清洗"""
        # 去除重复行
        df = df.drop_duplicates()
        
        # 处理缺失值
        # 数值型字段使用均值填充
        numeric_cols = ['Age']
        for col in numeric_cols:
            # 大小写不敏感匹配
            col_match = None
            for c in df.columns:
                if c.lower() == col.lower():
                    col_match = c
                    break
            if col_match:
                df[col_match] = pd.to_numeric(df[col_match], errors='coerce')
                df[col_match].fillna(df[col_match].mean(), inplace=True)
        
        # 类别型字段使用众数填充
        categorical_cols = ['Gender', 'Country', 'self_employed', 'family_history', 'treatment']
        for col in categorical_cols:
            # 大小写不敏感匹配
            col_match = None
            for c in df.columns:
                if c.lower() == col.lower():
                    col_match = c
                    break
            if col_match:
                df[col_match].fillna(df[col_match].mode()[0] if not df[col_match].mode().empty else 'Unknown', inplace=True)
        
        # 异常值处理 - 3σ原则
        age_col = None
        for c in df.columns:
            if c.lower() == 'age':
                age_col = c
                break
        if age_col:
            mean_age = df[age_col].mean()
            std_age = df[age_col].std()
            df = df[abs(df[age_col] - mean_age) <= 3 * std_age]
        
        # 标准化文本字段
        text_cols = ['Gender', 'Country', 'state']
        for col in text_cols:
            # 大小写不敏感匹配
            col_match = None
            for c in df.columns:
                if c.lower() == col.lower():
                    col_match = c
                    break
            if col_match:
                df[col_match] = df[col_match].astype(str).str.strip()
        
        return df
    
    @staticmethod
    def get_data_by_id(data_id):
        """根据ID获取数据"""
        return MentalHealthData.query.get(data_id)
    
    @staticmethod
    def get_data_list(page=1, per_page=20, filters=None):
        """获取数据列表"""
        query = MentalHealthData.query
        
        if filters:
            if 'risk_level' in filters and filters['risk_level']:
                query = query.filter(MentalHealthData.risk_level == filters['risk_level'])
            if 'gender' in filters and filters['gender']:
                query = query.filter(MentalHealthData.gender == filters['gender'])
            if 'age_group' in filters and filters['age_group']:
                query = query.filter(MentalHealthData.age_group == filters['age_group'])
            if 'country' in filters and filters['country']:
                query = query.filter(MentalHealthData.country == filters['country'])
            if 'cluster_id' in filters and filters['cluster_id'] is not None:
                query = query.filter(MentalHealthData.cluster_id == filters['cluster_id'])
        
        pagination = query.order_by(MentalHealthData.id.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return {
            'items': [item.to_dict() for item in pagination.items],
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page
        }
    
    @staticmethod
    def get_statistics():
        """获取数据统计信息"""
        return MentalHealthData.get_statistics()
    
    @staticmethod
    def get_dataframe(filters=None, limit=10000):
        """获取DataFrame格式的数据"""
        # 快速检查是否有数据
        total_count = MentalHealthData.query.count()
        if total_count == 0:
            return pd.DataFrame()
        
        query = MentalHealthData.query
        
        if filters:
            if 'risk_level' in filters and filters['risk_level']:
                query = query.filter(MentalHealthData.risk_level == filters['risk_level'])
            if 'cluster_id' in filters and filters['cluster_id'] is not None:
                query = query.filter(MentalHealthData.cluster_id == filters['cluster_id'])
        
        # 限制返回数据量以提高性能
        if limit:
            query = query.limit(limit)
        
        records = query.all()
        if not records:
            return pd.DataFrame()
        
        data = [r.to_dict() for r in records]
        return pd.DataFrame(data)
    
    @staticmethod
    def delete_data(data_id):
        """删除数据"""
        try:
            record = MentalHealthData.query.get(data_id)
            if record:
                db.session.delete(record)
                db.session.commit()
                return True
            return False
        except Exception as e:
            db.session.rollback()
            logger.error(f"删除数据失败: {str(e)}")
            raise
    
    @staticmethod
    def update_cluster_labels(cluster_labels):
        """更新聚类标签"""
        try:
            for data_id, cluster_id in cluster_labels.items():
                record = MentalHealthData.query.get(data_id)
                if record:
                    record.cluster_id = cluster_id
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            logger.error(f"更新聚类标签失败: {str(e)}")
            raise
    
    @staticmethod
    def get_feature_distribution(feature_name):
        """获取特征分布"""
        from sqlalchemy import func
        
        if feature_name == 'age':
            result = db.session.query(
                MentalHealthData.age_group,
                func.count(MentalHealthData.id)
            ).group_by(MentalHealthData.age_group).all()
        elif feature_name == 'risk_level':
            result = db.session.query(
                MentalHealthData.risk_level,
                func.count(MentalHealthData.id)
            ).group_by(MentalHealthData.risk_level).all()
        elif feature_name == 'gender':
            result = db.session.query(
                MentalHealthData.gender,
                func.count(MentalHealthData.id)
            ).group_by(MentalHealthData.gender).all()
        elif feature_name == 'country':
            result = db.session.query(
                MentalHealthData.country,
                func.count(MentalHealthData.id)
            ).group_by(MentalHealthData.country).all()
        else:
            return {}
        
        return {str(item[0]): item[1] for item in result if item[0]}
    
    @staticmethod
    def get_correlation_matrix():
        """获取特征相关性矩阵"""
        df = DataService.get_dataframe(limit=5000)
        
        # 选择数值型和相关类别特征
        features = ['age', 'risk_level', 'cluster_id']
        
        # 编码类别特征
        if 'risk_level' in df.columns:
            risk_mapping = {'Low Risk': 0, 'Medium Risk': 1, 'High Risk': 2}
            df['risk_level_encoded'] = df['risk_level'].map(risk_mapping)
        
        # 计算相关性
        numeric_df = df[['age', 'risk_level_encoded', 'cluster_id']].dropna()
        corr_matrix = numeric_df.corr()
        
        return corr_matrix.to_dict()
