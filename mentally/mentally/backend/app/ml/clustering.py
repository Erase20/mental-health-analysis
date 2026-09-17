import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score, silhouette_samples
from sklearn.preprocessing import StandardScaler
import pickle
import os
import logging

logger = logging.getLogger(__name__)

class ClusteringModel:
    """聚类模型类 - K-Means++"""
    
    def __init__(self, n_clusters=3, random_state=42):
        self.n_clusters = n_clusters
        self.random_state = random_state
        self.model = None
        self.scaler = StandardScaler()
        self.labels = None
        self.cluster_centers = None
        self.silhouette_avg = None
        self.silhouette_samples = None
        self.inertia = None
        
    def fit(self, X):
        """训练K-Means++模型（优化版本）"""
        # 标准化数据
        X_scaled = self.scaler.fit_transform(X)
        
        # 使用K-Means++初始化（优化参数）
        self.model = KMeans(
            n_clusters=self.n_clusters,
            init='k-means++',  # K-Means++初始化
            n_init=3,  # 进一步减少初始化次数
            max_iter=50,  # 进一步减少最大迭代次数
            random_state=self.random_state
        )
        
        # 训练模型
        self.model.fit(X_scaled)
        
        # 获取结果
        self.labels = self.model.labels_
        self.cluster_centers = self.model.cluster_centers_
        self.inertia = self.model.inertia_
        
        # 计算轮廓系数
        self.silhouette_avg = silhouette_score(X_scaled, self.labels)
        self.silhouette_samples = silhouette_samples(X_scaled, self.labels)
        
        logger.info(f"K-Means++聚类完成: n_clusters={self.n_clusters}, "
                   f"silhouette_score={self.silhouette_avg:.4f}, inertia={self.inertia:.4f}")
        
        return self.labels
    
    def predict(self, X):
        """预测新数据的聚类标签"""
        if self.model is None:
            raise ValueError("模型未训练")
        
        X_scaled = self.scaler.transform(X)
        return self.model.predict(X_scaled)
    
    def find_optimal_k(self, X, k_range=range(2, 5)):
        """使用轮廓系数法寻找最优K值（优化版本，减少K值范围）"""
        X_scaled = self.scaler.fit_transform(X)
        
        silhouette_scores = []
        inertia_scores = []
        
        for k in k_range:
            kmeans = KMeans(
                n_clusters=k,
                init='k-means++',
                n_init=3,  # 进一步减少初始化次数
                max_iter=50,  # 进一步减少最大迭代次数
                random_state=self.random_state
            )
            kmeans.fit(X_scaled)
            
            silhouette_avg = silhouette_score(X_scaled, kmeans.labels_)
            silhouette_scores.append(silhouette_avg)
            inertia_scores.append(kmeans.inertia_)
            
            logger.info(f"K={k}: silhouette_score={silhouette_avg:.4f}, inertia={kmeans.inertia_:.4f}")
        
        # 选择轮廓系数最高的K值
        optimal_k = list(k_range)[np.argmax(silhouette_scores)]
        
        return {
            'optimal_k': optimal_k,
            'silhouette_scores': dict(zip(k_range, silhouette_scores)),
            'inertia_scores': dict(zip(k_range, inertia_scores))
        }
    
    def get_cluster_statistics(self, X, original_df=None):
        """获取聚类统计信息"""
        if self.labels is None:
            raise ValueError("模型未训练")
        
        stats = {
            'n_clusters': self.n_clusters,
            'silhouette_score': float(self.silhouette_avg),
            'inertia': float(self.inertia),
            'cluster_distribution': {},
            'cluster_centers': self.cluster_centers.tolist(),
            'cluster_details': []
        }
        
        # 聚类分布
        unique, counts = np.unique(self.labels, return_counts=True)
        for cluster_id, count in zip(unique, counts):
            stats['cluster_distribution'][f'cluster_{cluster_id}'] = int(count)
        
        # 每个聚类的详细信息
        for cluster_id in range(self.n_clusters):
            cluster_mask = self.labels == cluster_id
            cluster_size = np.sum(cluster_mask)
            cluster_silhouette = np.mean(self.silhouette_samples[cluster_mask])
            
            cluster_info = {
                'cluster_id': int(cluster_id),
                'size': int(cluster_size),
                'silhouette_score': float(cluster_silhouette),
                'percentage': float(cluster_size / len(self.labels) * 100)
            }
            
            # 如果有原始数据，计算每个聚类的特征均值（只计算数值列）
            if original_df is not None:
                cluster_data = original_df[cluster_mask]
                # 只选择数值列
                numeric_cols = cluster_data.select_dtypes(include=[np.number]).columns
                numeric_data = cluster_data[numeric_cols]
                cluster_info['feature_means'] = numeric_data.mean().to_dict()
            
            stats['cluster_details'].append(cluster_info)
        
        return stats
    
    def assign_cluster_names(self, cluster_stats, risk_col=None):
        """根据聚类特征分配风险等级名称"""
        cluster_names = {}
        
        if risk_col and 'cluster_details' in cluster_stats:
            # 根据风险等级分布分配名称
            for detail in cluster_stats['cluster_details']:
                cluster_id = detail['cluster_id']
                # 这里可以根据实际数据特征来命名
                # 简化处理：按聚类大小排序分配
                cluster_names[cluster_id] = f'群体_{cluster_id}'
        else:
            # 默认命名
            for i in range(self.n_clusters):
                cluster_names[i] = f'群体_{i}'
        
        return cluster_names
    
    def save(self, filepath):
        """保存模型"""
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'n_clusters': self.n_clusters,
            'labels': self.labels,
            'cluster_centers': self.cluster_centers,
            'silhouette_avg': self.silhouette_avg,
            'silhouette_samples': self.silhouette_samples,
            'inertia': self.inertia,
            'random_state': self.random_state
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)
        
        logger.info(f"聚类模型已保存: {filepath}")
    
    def load(self, filepath):
        """加载模型"""
        with open(filepath, 'rb') as f:
            model_data = pickle.load(f)
        
        self.model = model_data['model']
        self.scaler = model_data['scaler']
        self.n_clusters = model_data['n_clusters']
        self.labels = model_data['labels']
        self.cluster_centers = model_data['cluster_centers']
        self.silhouette_avg = model_data['silhouette_avg']
        self.silhouette_samples = model_data['silhouette_samples']
        self.inertia = model_data['inertia']
        self.random_state = model_data['random_state']
        
        logger.info(f"聚类模型已加载: {filepath}")
    
    def get_cluster_risk_mapping(self, original_df, risk_col='risk_level'):
        """获取聚类与风险等级的映射关系"""
        if self.labels is None or risk_col not in original_df.columns:
            return {}
        
        mapping = {}
        for cluster_id in range(self.n_clusters):
            cluster_mask = self.labels == cluster_id
            cluster_risks = original_df.loc[cluster_mask, risk_col]
            
            # 统计每个聚类中的风险等级分布
            risk_counts = cluster_risks.value_counts()
            dominant_risk = risk_counts.index[0]
            
            mapping[cluster_id] = {
                'dominant_risk': dominant_risk,
                'risk_distribution': risk_counts.to_dict()
            }
        
        return mapping
