import pandas as pd
import numpy as np
from sklearn.preprocessing import PolynomialFeatures
import logging

logger = logging.getLogger(__name__)

class FeatureEngineer:
    """特征工程类"""
    
    def __init__(self):
        self.feature_importance = {}
        
    def create_features(self, df):
        """创建新特征"""
        df = df.copy()
        
        # 保留id列
        if 'id' in df.columns:
            id_col = df['id'].copy()
        else:
            id_col = None
        
        # 数据清洗：确保数值列是数值类型
        if 'age' in df.columns:
            df['age'] = pd.to_numeric(df['age'], errors='coerce').fillna(30)
        
        # 1. 年龄分组特征
        if 'age' in df.columns:
            try:
                df['age_group_encoded'] = pd.cut(
                    df['age'], 
                    bins=[0, 25, 35, 45, 55, 100],
                    labels=[0, 1, 2, 3, 4]
                ).astype(int)
            except Exception as e:
                logger.warning(f"年龄分组失败: {e}")
                df['age_group_encoded'] = 2  # 默认值
        
        # 2. 工作支持度综合评分
        support_cols = ['benefits', 'care_options', 'wellness_program', 'seek_help', 'anonymity']
        if all(col in df.columns for col in support_cols):
            df['support_score'] = self._calculate_support_score(df, support_cols)
        
        # 3. 工作环境压力指数
        stress_cols = ['work_interfere', 'mental_health_consequence', 'leave']
        if all(col in df.columns for col in stress_cols):
            df['stress_index'] = self._calculate_stress_index(df, stress_cols)
        
        # 4. 公司规模编码
        if 'no_employees' in df.columns:
            df['company_size_encoded'] = df['no_employees'].apply(self._encode_company_size)
        
        # 5. 心理健康态度综合评分
        attitude_cols = ['coworkers', 'supervisor', 'mental_health_interview', 'mental_vs_physical']
        if all(col in df.columns for col in attitude_cols):
            df['attitude_score'] = self._calculate_attitude_score(df, attitude_cols)
        
        # 6. 家庭史与治疗交互特征
        if 'family_history' in df.columns and 'treatment' in df.columns:
            df['family_treatment_interaction'] = (
                (df['family_history'] == 'Yes').astype(int) * 
                (df['treatment'] == 'Yes').astype(int)
            )
        
        # 7. 远程工作与技术公司交互
        if 'remote_work' in df.columns and 'tech_company' in df.columns:
            df['remote_tech_interaction'] = (
                (df['remote_work'] == 'Yes').astype(int) * 
                (df['tech_company'] == 'Yes').astype(int)
            )
        
        # 8. 是否观察到负面后果
        if 'obs_consequence' in df.columns:
            df['has_observed_consequence'] = (df['obs_consequence'] == 'Yes').astype(int)
        
        # 恢复id列
        if id_col is not None:
            df['id'] = id_col
        
        # 确保所有特征列都是数值类型
        numeric_features = [
            'age_group_encoded', 'support_score', 'stress_index', 
            'company_size_encoded', 'attitude_score', 
            'family_treatment_interaction', 'remote_tech_interaction', 
            'has_observed_consequence'
        ]
        
        for feature in numeric_features:
            if feature in df.columns:
                df[feature] = pd.to_numeric(df[feature], errors='coerce').fillna(0)
        
        # 确保cluster_id是数值类型（如果存在）
        if 'cluster_id' in df.columns:
            df['cluster_id'] = pd.to_numeric(df['cluster_id'], errors='coerce')
        
        return df
    
    def _calculate_support_score(self, df, cols):
        """计算公司支持度评分"""
        score = pd.Series(0, index=df.index)
        
        positive_values = ['Yes', 'Very easy', 'Somewhat easy']
        
        for col in cols:
            if col in df.columns:
                score += df[col].isin(positive_values).astype(int)
        
        return score / len(cols)
    
    def _calculate_stress_index(self, df, cols):
        """计算工作压力指数"""
        score = pd.Series(0, index=df.index)
        
        # work_interfere: Often=3, Sometimes=2, Rarely=1, Never=0
        if 'work_interfere' in df.columns:
            interfere_map = {'Often': 3, 'Sometimes': 2, 'Rarely': 1, 'Never': 0, 'Not applicable': 0}
            score += df['work_interfere'].map(interfere_map).fillna(0)
        
        # mental_health_consequence: Yes=2, Maybe=1, No=0
        if 'mental_health_consequence' in df.columns:
            consequence_map = {'Yes': 2, 'Maybe': 1, 'No': 0}
            score += df['mental_health_consequence'].map(consequence_map).fillna(0)
        
        # leave: Very difficult=3, Somewhat difficult=2, Somewhat easy=1, Very easy=0
        if 'leave' in df.columns:
            leave_map = {'Very difficult': 3, 'Somewhat difficult': 2, 
                        'Somewhat easy': 1, 'Very easy': 0, "Don't know": 1}
            score += df['leave'].map(leave_map).fillna(1)
        
        return score / 6  # 归一化到0-1
    
    def _encode_company_size(self, size):
        """编码公司规模"""
        size_map = {
            '1-5': 0,
            '6-25': 1,
            '26-100': 2,
            '100-500': 3,
            '500-1000': 4,
            'More than 1000': 5
        }
        return size_map.get(size, 2)  # 默认中等规模
    
    def _calculate_attitude_score(self, df, cols):
        """计算态度评分"""
        score = pd.Series(0, index=df.index)
        
        # coworkers/supervisor: Yes=2, Some of them=1, No=0
        for col in ['coworkers', 'supervisor']:
            if col in df.columns:
                attitude_map = {'Yes': 2, 'Some of them': 1, 'No': 0}
                score += df[col].map(attitude_map).fillna(1)
        
        # mental_health_interview: Yes=2, Maybe=1, No=0
        if 'mental_health_interview' in df.columns:
            interview_map = {'Yes': 2, 'Maybe': 1, 'No': 0}
            score += df['mental_health_interview'].map(interview_map).fillna(1)
        
        # mental_vs_physical: Yes=2, Don't know=1, No=0
        if 'mental_vs_physical' in df.columns:
            physical_map = {'Yes': 2, "Don't know": 1, 'No': 0}
            score += df['mental_vs_physical'].map(physical_map).fillna(1)
        
        return score / 8  # 归一化到0-1
    
    def select_features(self, df, target_col, method='correlation', k=10):
        """特征选择"""
        from sklearn.feature_selection import SelectKBest, f_classif, mutual_info_classif
        
        X = df.drop(columns=[target_col])
        y = df[target_col]
        
        # 只选择数值型特征
        X_numeric = X.select_dtypes(include=[np.number])
        
        if method == 'correlation':
            # 基于相关性选择
            correlations = X_numeric.corrwith(y).abs().sort_values(ascending=False)
            selected_features = correlations.head(k).index.tolist()
        elif method == 'f_classif':
            # F检验
            selector = SelectKBest(score_func=f_classif, k=min(k, X_numeric.shape[1]))
            selector.fit(X_numeric, y)
            selected_features = X_numeric.columns[selector.get_support()].tolist()
        elif method == 'mutual_info':
            # 互信息
            selector = SelectKBest(score_func=mutual_info_classif, k=min(k, X_numeric.shape[1]))
            selector.fit(X_numeric, y)
            selected_features = X_numeric.columns[selector.get_support()].tolist()
        else:
            selected_features = X_numeric.columns.tolist()
        
        logger.info(f"特征选择: 从{X_numeric.shape[1]}个特征中选择{len(selected_features)}个")
        
        return selected_features
    
    def get_feature_importance(self, model, feature_names):
        """获取特征重要性"""
        if hasattr(model, 'feature_importances_'):
            importance = model.feature_importances_
        elif hasattr(model, 'coef_'):
            importance = np.abs(model.coef_[0])
        else:
            return {}
        
        importance_dict = dict(zip(feature_names, importance))
        return dict(sorted(importance_dict.items(), key=lambda x: x[1], reverse=True))
