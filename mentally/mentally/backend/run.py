"""
应用入口文件
"""
import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 加载.env文件
from dotenv import load_dotenv
load_dotenv()

# 从app模块导入create_app函数
from app import create_app

# 创建应用实例
app = create_app(os.environ.get('FLASK_CONFIG', 'development'))

# 确保数据库表存在
with app.app_context():
    from app import db
    db.create_all()

# 启动服务器
print("启动后端服务器...")
print(f"数据库配置: {app.config['SQLALCHEMY_DATABASE_URI']}")
print(f"JWT配置: {app.config['JWT_SECRET_KEY'][:10]}...")
print("服务器运行在: http://localhost:5000")
app.run(host='0.0.0.0', port=5000, debug=False)



