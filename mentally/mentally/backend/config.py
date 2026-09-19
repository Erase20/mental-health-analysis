import os
from datetime import timedelta

class Config:
    """基础配置类"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-only-secret-key-change-me-32chars'
    
    # MySQL数据库配置
    MYSQL_HOST = os.environ.get('MYSQL_HOST') or 'localhost'
    MYSQL_PORT = int(os.environ.get('MYSQL_PORT') or 3306)
    MYSQL_USER = os.environ.get('MYSQL_USER') or 'root'
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD') or 'root'
    MYSQL_DB = os.environ.get('MYSQL_DB') or 'mental_health_db'
    
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or (
        f'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_POOL_SIZE = 20
    SQLALCHEMY_POOL_TIMEOUT = 30
    SQLALCHEMY_POOL_RECYCLE = 3600
    
    # Redis配置
    REDIS_HOST = os.environ.get('REDIS_HOST') or 'localhost'
    REDIS_PORT = int(os.environ.get('REDIS_PORT') or 6379)
    REDIS_DB = int(os.environ.get('REDIS_DB') or 0)
    REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD') or None
    
    # JWT配置
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'dev-only-jwt-secret-key-change-me-32chars'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    
    # Celery配置
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL') or f'redis://{REDIS_HOST}:{REDIS_PORT}/1'
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND') or f'redis://{REDIS_HOST}:{REDIS_PORT}/2'
    
    # Hadoop配置
    HDFS_HOST = os.environ.get('HDFS_HOST') or 'localhost'
    HDFS_PORT = int(os.environ.get('HDFS_PORT') or 9000)
    HDFS_USER = os.environ.get('HDFS_USER') or 'hdfs'
    
    # Spark配置
    SPARK_MASTER = os.environ.get('SPARK_MASTER') or 'local[*]'
    SPARK_APP_NAME = os.environ.get('SPARK_APP_NAME') or 'MentalHealthAnalysis'
    SPARK_EXECUTOR_MEMORY = os.environ.get('SPARK_EXECUTOR_MEMORY') or '2g'
    SPARK_DRIVER_MEMORY = os.environ.get('SPARK_DRIVER_MEMORY') or '2g'
    
    # 数据文件路径
    DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
    MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app', 'ml', 'models')
    REPORT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'reports')
    
    # 分页配置
    PAGE_SIZE = 20
    MAX_PAGE_SIZE = 100
    
    # 文件上传配置
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}

class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    SQLALCHEMY_ECHO = True

class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    SQLALCHEMY_ECHO = False

class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
