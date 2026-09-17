import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, GridSearchCV, cross_val_score
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix, classification_report
from sklearn.preprocessing import StandardScaler
import pickle
import os
import logging

logger = logging.getLogger(__name__)

class ClassificationModel:
    """分类模型类 - 随机森林"""
    
    def __init__(self, random_state=42):
        self.random_state = random_state
        self.model = None
        self.scaler = StandardScaler()
        self.feature_names = None
        self.target_names = None
        self.metrics = {}
        self.best_params = None
        
    def fit(self, X, y, test_size=0.3, optimize=True):
        """训练随机森林模型"""
        # 分割训练集和测试集
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=self.random_state, stratify=y
        )
        
        # 标准化数据
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        if optimize:
            # 网格搜索优化超参数
            self.best_params = self._grid_search(X_train_scaled, y_train)
            self.model = RandomForestClassifier(
                **self.best_params,
                random_state=self.random_state,
                n_jobs=-1
            )
        else:
            # 使用默认参数
            self.model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                min_samples_split=2,
                min_samples_leaf=1,
                random_state=self.random_state,
                n_jobs=-1
            )
        
        # 训练模型
        self.model.fit(X_train_scaled, y_train)
        
        # 预测
        y_pred = self.model.predict(X_test_scaled)
        
        # 计算评估指标
        self._calculate_metrics(y_test, y_pred)
        
        # 保存特征名称
        if isinstance(X, pd.DataFrame):
            self.feature_names = X.columns.tolist()
        
        self.target_names = np.unique(y).tolist()
        
        logger.info(f"随机森林模型训练完成: accuracy={self.metrics['accuracy']:.4f}, "
                   f"f1_score={self.metrics['f1_score']:.4f}")
        
        return self.metrics
    
    def _grid_search(self, X_train, y_train):
        """网格搜索最优超参数"""
        param_grid = {
            'n_estimators': [50, 100, 200],
            'max_depth': [5, 10, 15, None],
            'min_samples_split': [2, 5, 10],
            'min_samples_leaf': [1, 2, 4]
        }
        
        rf = RandomForestClassifier(random_state=self.random_state)
        
        grid_search = GridSearchCV(
            rf, param_grid, 
            cv=5, 
            scoring='f1_weighted',
            n_jobs=-1,
            verbose=0
        )
        
        grid_search.fit(X_train, y_train)
        
        logger.info(f"网格搜索最优参数: {grid_search.best_params_}")
        
        return grid_search.best_params_
    
    def _calculate_metrics(self, y_true, y_pred):
        """计算评估指标"""
        self.metrics = {
            'accuracy': float(accuracy_score(y_true, y_pred)),
            'precision': float(precision_score(y_true, y_pred, average='weighted', zero_division=0)),
            'recall': float(recall_score(y_true, y_pred, average='weighted', zero_division=0)),
            'f1_score': float(f1_score(y_true, y_pred, average='weighted', zero_division=0)),
            'confusion_matrix': confusion_matrix(y_true, y_pred).tolist(),
            'classification_report': classification_report(y_true, y_pred, output_dict=True)
        }
    
    def predict(self, X):
        """预测"""
        if self.model is None:
            raise ValueError("模型未训练")
        
        X_scaled = self.scaler.transform(X)
        return self.model.predict(X_scaled)
    
    def predict_proba(self, X):
        """预测概率"""
        if self.model is None:
            raise ValueError("模型未训练")
        
        X_scaled = self.scaler.transform(X)
        return self.model.predict_proba(X_scaled)
    
    def cross_validate(self, X, y, cv=5):
        """交叉验证"""
        X_scaled = self.scaler.fit_transform(X)
        
        scores = cross_val_score(
            self.model, X_scaled, y, 
            cv=cv, 
            scoring='f1_weighted',
            n_jobs=-1
        )
        
        return {
            'scores': scores.tolist(),
            'mean': float(scores.mean()),
            'std': float(scores.std())
        }
    
    def get_feature_importance(self):
        """获取特征重要性"""
        if self.model is None:
            raise ValueError("模型未训练")
        
        importance = self.model.feature_importances_
        
        if self.feature_names:
            importance_dict = dict(zip(self.feature_names, importance))
        else:
            importance_dict = {f'feature_{i}': imp for i, imp in enumerate(importance)}
        
        # 按重要性排序
        return dict(sorted(importance_dict.items(), key=lambda x: x[1], reverse=True))
    
    def get_model_summary(self):
        """获取模型摘要"""
        return {
            'model_type': 'RandomForestClassifier',
            'best_params': self.best_params,
            'metrics': self.metrics,
            'feature_importance': self.get_feature_importance(),
            'n_features': len(self.feature_names) if self.feature_names else None,
            'n_classes': len(self.target_names) if self.target_names else None,
            'target_names': self.target_names
        }
    
    def save(self, filepath):
        """保存模型"""
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'feature_names': self.feature_names,
            'target_names': self.target_names,
            'metrics': self.metrics,
            'best_params': self.best_params,
            'random_state': self.random_state
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)
        
        logger.info(f"分类模型已保存: {filepath}")
    
    def load(self, filepath):
        """加载模型"""
        with open(filepath, 'rb') as f:
            model_data = pickle.load(f)
        
        self.model = model_data['model']
        self.scaler = model_data['scaler']
        self.feature_names = model_data['feature_names']
        self.target_names = model_data['target_names']
        self.metrics = model_data['metrics']
        self.best_params = model_data['best_params']
        self.random_state = model_data['random_state']
        
        logger.info(f"分类模型已加载: {filepath}")
