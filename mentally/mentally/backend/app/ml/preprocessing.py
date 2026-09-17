import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, LabelEncoder, OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.decomposition import PCA
import pickle
import os
import logging

logger = logging.getLogger(__name__)

class DataPreprocessor:
    """数据预处理类"""
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.label_encoders = {}
        self.imputer = SimpleImputer(strategy='mean')
        self.pca = None
        self.feature_columns = []
        self.categorical_columns = []
        self.numerical_columns = []
        
    def fit_transform(self, df, target_col=None):
        """拟合并转换数据"""
        df_processed = df.copy()
        
        # 1. 处理缺失值
        df_processed = self._handle_missing_values(df_processed)
        
        # 2. 处理异常值
        df_processed = self._handle_outliers(df_processed)
        
        # 3. 编码类别特征
        df_processed = self._encode_categorical(df_processed)
        
        # 4. 标准化数值特征
        df_processed = self._scale_numerical(df_processed)
        
        # 5. PCA降维 (保留85%方差)
        if target_col and target_col in df_processed.columns:
            X = df_processed.drop(columns=[target_col])
            y = df_processed[target_col]
            X_pca = self._apply_pca(X, variance_ratio=0.85)
            df_processed = pd.concat([X_pca, y], axis=1)
        else:
            df_processed = self._apply_pca(df_processed, variance_ratio=0.85)
        
        return df_processed
    
    def transform(self, df):
        """转换数据"""
        df_processed = df.copy()
        
        # 使用已拟合的转换器
        df_processed = self._handle_missing_values(df_processed, fit=False)
        df_processed = self._encode_categorical(df_processed, fit=False)
        df_processed = self._scale_numerical(df_processed, fit=False)
        
        if self.pca is not None:
            df_processed = pd.DataFrame(
                self.pca.transform(df_processed),
                columns=[f'PC{i+1}' for i in range(self.pca.n_components_)],
                index=df_processed.index
            )
        
        return df_processed
    
    def _handle_missing_values(self, df, fit=True):
        """处理缺失值"""
        df = df.copy()
        
        # 数值型字段 - 均值填充
        numerical_cols = df.select_dtypes(include=[np.number]).columns
        if fit:
            df[numerical_cols] = self.imputer.fit_transform(df[numerical_cols])
        else:
            df[numerical_cols] = self.imputer.transform(df[numerical_cols])
        
        # 类别型字段 - 众数填充
        categorical_cols = df.select_dtypes(include=['object']).columns
        for col in categorical_cols:
            mode_val = df[col].mode()
            if not mode_val.empty:
                df[col].fillna(mode_val[0], inplace=True)
            else:
                df[col].fillna('Unknown', inplace=True)
        
        return df
    
    def _handle_outliers(self, df):
        """处理异常值 - 3σ原则"""
        df = df.copy()
        numerical_cols = df.select_dtypes(include=[np.number]).columns
        
        for col in numerical_cols:
            if col in ['id', 'cluster_id']:
                continue
            mean = df[col].mean()
            std = df[col].std()
            # 将超过3σ的值设为边界值
            upper_bound = mean + 3 * std
            lower_bound = mean - 3 * std
            df[col] = df[col].clip(lower=lower_bound, upper=upper_bound)
        
        return df
    
    def _encode_categorical(self, df, fit=True):
        """编码类别特征"""
        df = df.copy()
        categorical_cols = df.select_dtypes(include=['object']).columns
        
        for col in categorical_cols:
            if fit:
                le = LabelEncoder()
                df[col] = le.fit_transform(df[col].astype(str))
                self.label_encoders[col] = le
            else:
                if col in self.label_encoders:
                    le = self.label_encoders[col]
                    # 处理未见过的类别
                    df[col] = df[col].apply(
                        lambda x: le.transform([x])[0] if x in le.classes_ else -1
                    )
        
        return df
    
    def _scale_numerical(self, df, fit=True):
        """标准化数值特征"""
        df = df.copy()
        numerical_cols = df.select_dtypes(include=[np.number]).columns
        
        if fit:
            df[numerical_cols] = self.scaler.fit_transform(df[numerical_cols])
        else:
            df[numerical_cols] = self.scaler.transform(df[numerical_cols])
        
        return df
    
    def _apply_pca(self, df, variance_ratio=0.85):
        """应用PCA降维"""
        # 选择数值列
        numerical_df = df.select_dtypes(include=[np.number])
        
        if numerical_df.shape[1] < 2:
            return df
        
        # 拟合PCA
        if self.pca is None:
            self.pca = PCA(n_components=variance_ratio)
            pca_result = self.pca.fit_transform(numerical_df)
        else:
            pca_result = self.pca.transform(numerical_df)
        
        # 创建PCA结果DataFrame
        pca_df = pd.DataFrame(
            pca_result,
            columns=[f'PC{i+1}' for i in range(pca_result.shape[1])],
            index=df.index
        )
        
        logger.info(f"PCA降维: {numerical_df.shape[1]}维 -> {pca_result.shape[1]}维, 保留{self.pca.explained_variance_ratio_.sum()*100:.2f}%方差")
        
        return pca_df
    
    def save(self, filepath):
        """保存预处理器"""
        with open(filepath, 'wb') as f:
            pickle.dump({
                'scaler': self.scaler,
                'label_encoders': self.label_encoders,
                'imputer': self.imputer,
                'pca': self.pca,
                'feature_columns': self.feature_columns
            }, f)
    
    def load(self, filepath):
        """加载预处理器"""
        with open(filepath, 'rb') as f:
            data = pickle.load(f)
            self.scaler = data['scaler']
            self.label_encoders = data['label_encoders']
            self.imputer = data['imputer']
            self.pca = data['pca']
            self.feature_columns = data['feature_columns']
    
    def get_feature_names(self):
        """获取特征名称"""
        if self.pca is not None:
            return [f'PC{i+1}' for i in range(self.pca.n_components_)]
        return self.feature_columns
