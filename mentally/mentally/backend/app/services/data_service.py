import pandas as pd
import numpy as np
from datetime import datetime
from app import db
from app.models.mental_health_data import MentalHealthData
from sqlalchemy import func, or_
import logging

logger = logging.getLogger(__name__)

class DataService:
    """数据服务类"""

    @staticmethod
    def _as_text(value):
        """将缺失值安全转换为文本。"""
        if value is None or pd.isna(value):
            return ''
        return str(value).strip()

    @staticmethod
    def normalize_gender(value):
        """把自由文本性别归并成稳定分组。

        原始调查中可能出现 M、male、f、Female、Trans woman、queer 等几十种写法。
        如果直接 value_counts，图表会产生大量只有一个样本的分类。
        """
        text = DataService._as_text(value).lower()
        if not text:
            return '未知'

        if (
            'female' in text
            or text in {'f', 'woman', 'femme', 'femail', 'femake', 'trans woman'}
            or 'cis-female' in text
        ):
            return '女'
        if (
            'male' in text
            or text in {'m', 'man', 'mail', 'mal', 'malr', 'maile', 'msle', 'make'}
        ):
            return '男'
        if any(keyword in text for keyword in [
            'non-binary', 'nonbinary', 'genderqueer', 'agender', 'androgyne',
            'fluid', 'enby', 'queer', 'neuter'
        ]):
            return '非二元/流性'
        return '其他/不愿透露'

    @staticmethod
    def derive_age_group(age):
        """根据年龄生成统一年龄段，保证筛选和图表使用同一套分组。"""
        if age is None or pd.isna(age):
            return '未知'
        age = int(age)
        if age < 26:
            return '25岁及以下'
        if age < 36:
            return '26-35岁'
        if age < 46:
            return '36-45岁'
        if age < 56:
            return '46-55岁'
        return '56岁以上'

    @staticmethod
    def derive_risk_level(row, get_value):
        """当原始数据没有 Risk_Level 时，用可解释规则生成风险分层。

        学习重点：
        这是规则评分，不是临床诊断。它的作用是让演示数据可以完成分析和可视化；
        真实项目中应优先使用独立量表分数或医生确认标签。
        """
        score = 0

        if get_value(row, 'family_history') == 'Yes':
            score += 25
        if get_value(row, 'treatment') == 'Yes':
            score += 20

        work_interfere = get_value(row, 'work_interfere')
        if work_interfere == 'Often':
            score += 25
        elif work_interfere == 'Sometimes':
            score += 15
        elif work_interfere == 'Rarely':
            score += 5

        support_columns = [
            'benefits', 'care_options', 'wellness_program', 'seek_help', 'anonymity'
        ]
        support_count = sum(get_value(row, col) == 'Yes' for col in support_columns)
        if support_count <= 1:
            score += 10
        elif support_count <= 2:
            score += 5

        if get_value(row, 'obs_consequence') == 'Yes':
            score += 10
        if get_value(row, 'leave') in {'Very difficult', 'Somewhat difficult'}:
            score += 10

        if score >= 70:
            return 'High Risk'
        if score >= 40:
            return 'Medium Risk'
        return 'Low Risk'

    @staticmethod
    def enrich_derived_fields(df):
        """给 DataFrame 补齐风险等级和年龄段。

        这个方法既用于导入新数据，也用于读取历史数据，
        因此旧数据库中缺失 Risk_Level/Age_Group 的记录也能正常显示。
        """
        if df.empty:
            return df

        df = df.copy()
        # 原始 CSV 的列名可能是 Age、age，因此先做大小写不敏感查找。
        age_col = next((col for col in df.columns if str(col).lower() == 'age'), None)
        if age_col:
            age_values = pd.to_numeric(df[age_col], errors='coerce')
            df['age_group'] = age_values.apply(DataService.derive_age_group)

        # 只有原始数据完全没有风险标签时才执行规则派生。
        if 'risk_level' not in df.columns or df['risk_level'].isna().all():
            column_mapping = {str(col).lower(): col for col in df.columns}

            def get_value(row, col_name):
                actual_col = column_mapping.get(col_name.lower())
                return row[actual_col] if actual_col else None

            df['risk_level'] = df.apply(
                lambda row: DataService.derive_risk_level(row, get_value),
                axis=1
            )

        return df

    @staticmethod
    def backfill_derived_fields():
        """把派生字段回填到历史数据库记录中。

        不回填也能通过 enrich_derived_fields 临时计算；
        回填后，数据管理页的风险筛选可以直接使用 SQL 过滤。
        """
        records = MentalHealthData.query.filter(
            or_(
                MentalHealthData.risk_level.is_(None),
                MentalHealthData.age_group.is_(None)
            )
        ).all()
        if not records:
            return 0

        original_rows = [record.to_dict() for record in records]
        enriched = DataService.enrich_derived_fields(pd.DataFrame(original_rows))
        for record, (_, row) in zip(records, enriched.iterrows()):
            record.risk_level = row.get('risk_level') or record.risk_level
            record.age_group = row.get('age_group') or record.age_group

        db.session.commit()
        return len(records)

    @staticmethod
    def import_from_file(file_path):
        """按扩展名选择正确的读取器。

        这是修复 Excel 上传 bug 的关键：
        CSV 使用 read_csv，xlsx/xls 使用 read_excel。
        """
        extension = file_path.rsplit('.', 1)[-1].lower()

        if extension == 'csv':
            return DataService.import_from_csv(file_path)
        if extension in {'xlsx', 'xls'}:
            return DataService.import_from_excel(file_path)

        raise ValueError('不支持的文件格式，请上传CSV或Excel文件')

    @staticmethod
    def import_from_csv(file_path):
        """从CSV文件导入数据"""
        try:
            df = pd.read_csv(file_path, encoding='utf-8-sig')
            return DataService.import_from_dataframe(df)
        except Exception as e:
            logger.error(f"导入CSV失败: {str(e)}")
            raise

    @staticmethod
    def import_from_excel(file_path):
        """从Excel文件导入数据。"""
        try:
            df = pd.read_excel(file_path)
            return DataService.import_from_dataframe(df)
        except Exception as e:
            logger.error(f"导入Excel失败: {str(e)}")
            raise
    
    @staticmethod
    def import_from_dataframe(df):
        """把清洗后的 DataFrame 批量写入数据库。"""
        try:
            # 第一步：清洗原始值，避免空值和异常值直接进入数据库。
            df = DataService.clean_data(df)
            # 第二步：生成图表和筛选需要的风险分层、年龄段。
            df = DataService.enrich_derived_fields(df)
            
            # 建立小写列名映射，兼容 Age/age、Gender/gender 等不同格式。
            column_mapping = {}
            for col in df.columns:
                column_mapping[col.lower()] = col
            
            def get_value(row, col_name):
                col_lower = col_name.lower()
                if col_lower in column_mapping:
                    actual_col = column_mapping[col_lower]
                    return row[actual_col]
                return None
            
            # 每 1000 条批量提交一次，避免一次插入过多导致内存和事务压力。
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
                        risk_level=get_value(row, 'Risk_Level') or get_value(row, 'risk_level'),
                        age_group=get_value(row, 'age_group') or get_value(row, 'Age_Group'),
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
        """数据清洗基础流程：去重、缺失值、异常值和文本空格。"""
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
            # 单行数据或常数列的标准差为 NaN/0。
            # 如果继续执行 3σ，所有样本都会被过滤掉，这是小数据集测试发现的边界问题。
            if pd.notna(std_age) and std_age > 0:
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
        
        # 数据库只保存原始字段时，响应前再补一次派生字段，保证旧数据也能显示。
        items = DataService.enrich_derived_fields(
            pd.DataFrame([item.to_dict() for item in pagination.items])
        ).to_dict('records')

        return {
            'items': items,
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
        return DataService.enrich_derived_fields(pd.DataFrame(data))
    
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
