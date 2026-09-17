from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_restful import Api
from celery import Celery
import redis
import os
import sys
from datetime import timedelta
from config import config

# 设置控制台编码为UTF-8
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer)

# 加载.env文件
from dotenv import load_dotenv
load_dotenv()

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
celery = Celery(__name__)
redis_client = None

def create_app(config_name=None):
    """应用工厂函数"""
    print("开始创建应用...")
    if config_name is None:
        config_name = os.environ.get('FLASK_CONFIG', 'default')
    
    print(f"使用配置: {config_name}")
    
    try:
        app = Flask(__name__)
        print("✓ Flask应用创建成功")
        
        app.config.from_object(config[config_name])
        print("✓ 配置加载成功")
        
        # 初始化扩展
        print("初始化数据库...")
        db.init_app(app)
        print("✓ 数据库初始化成功")
        
        print("初始化迁移...")
        migrate.init_app(app, db)
        print("✓ 迁移初始化成功")
        
        print("初始化JWT...")
        jwt.init_app(app)
        print("✓ JWT初始化成功")
        
        print("配置CORS...")
        CORS(app, resources={
            r"/api/*": {
                "origins": ["http://localhost:3000", "http://localhost:3001", "http://localhost:3002", "http://localhost:3003", "http://localhost:5173", "http://localhost:8080"],
                "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                "allow_headers": ["Authorization", "Content-Type"],
                "supports_credentials": True
            }
        })
        print("✓ CORS配置成功")
        
        # 初始化Redis（可选）
        print("初始化Redis...")
        global redis_client
        redis_client = None
        print("⚠️ Redis未初始化，系统将在无Redis模式下运行")
        print("✓ Redis初始化完成")
        
        # 初始化Celery
        print("初始化Celery...")
        celery.conf.update(app.config)
        print("✓ Celery初始化成功")
        
        # 创建必要的目录
        print("创建目录...")
        os.makedirs(app.config['DATA_PATH'], exist_ok=True)
        os.makedirs(app.config['MODEL_PATH'], exist_ok=True)
        os.makedirs(app.config['REPORT_PATH'], exist_ok=True)
        print("✓ 目录创建成功")
        
        # 注册蓝图
        print("注册蓝图...")
        try:
            from app.api.auth import auth_bp
            print("✓ auth_bp导入成功")
            
            from app.api.data import data_bp
            print("✓ data_bp导入成功")
            
            from app.api.analysis import analysis_bp
            print("✓ analysis_bp导入成功")
            
            from app.api.visualization import viz_bp
            print("✓ viz_bp导入成功")
            
            from app.api.report import report_bp
            print("✓ report_bp导入成功")
            
            from app.api.user import user_bp
            print("✓ user_bp导入成功")
            
            app.register_blueprint(auth_bp, url_prefix='/api/auth')
            app.register_blueprint(data_bp, url_prefix='/api/data')
            app.register_blueprint(analysis_bp, url_prefix='/api/analysis')
            app.register_blueprint(viz_bp, url_prefix='/api/viz')
            app.register_blueprint(report_bp, url_prefix='/api/report')
            app.register_blueprint(user_bp, url_prefix='/api/user')
            print("✓ 蓝图注册成功")
        except Exception as e:
            print(f"✗ 蓝图注册失败: {e}")
            import traceback
            traceback.print_exc()
        
        # 注册错误处理
        print("注册错误处理...")
        register_error_handlers(app)
        print("✓ 错误处理注册成功")
        
        # JWT错误处理
        print("配置JWT错误处理...")
        @jwt.expired_token_loader
        def expired_token_callback(jwt_header, jwt_payload):
            return {'code': 401, 'message': 'Token已过期', 'data': None}, 401
        
        @jwt.invalid_token_loader
        def invalid_token_callback(error):
            return {'code': 401, 'message': '无效的Token', 'data': None}, 401
        
        @jwt.unauthorized_loader
        def missing_token_callback(error):
            return {'code': 401, 'message': '缺少Token', 'data': None}, 401
        print("✓ JWT错误处理配置成功")
        
        print("✓ 应用创建完成")
        return app
        
    except Exception as e:
        print(f"✗ 应用创建失败: {e}")
        import traceback
        traceback.print_exc()
        raise


def register_error_handlers(app):
    """注册错误处理器"""
    
    @app.errorhandler(400)
    def bad_request(error):
        return {'code': 400, 'message': '请求参数错误', 'data': None}, 400
    
    @app.errorhandler(404)
    def not_found(error):
        return {'code': 404, 'message': '资源不存在', 'data': None}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return {'code': 500, 'message': '服务器内部错误', 'data': None}, 500
    
    @app.errorhandler(Exception)
    def handle_exception(error):
        db.session.rollback()
        return {'code': 500, 'message': str(error), 'data': None}, 500

def make_celery(app):
    """创建Celery实例"""
    celery = Celery(
        app.import_name,
        backend=app.config['CELERY_RESULT_BACKEND'],
        broker=app.config['CELERY_BROKER_URL']
    )
    celery.conf.update(app.config)
    
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    
    celery.Task = ContextTask
    return celery
