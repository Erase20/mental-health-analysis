"""Create database tables and optional bootstrap accounts/demo data."""
import argparse
import os
import sys

from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

from app import create_app, db
from app.models import User
from app.services.data_service import DataService


def create_user(username, email, password, role):
    user = User.query.filter_by(username=username).first()
    if user:
        print(f"账号已存在，跳过: {username}")
        return user

    user = User(username=username, email=email, role=role)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    print(f"已创建账号: {username} ({role})")
    return user


def seed_demo_data():
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(backend_dir)
    candidates = [
        os.path.join(project_dir, 'survey.csv'),
        os.path.join(project_dir, 'mental_health.csv')
    ]
    source = next((path for path in candidates if os.path.exists(path)), None)

    if not source:
        raise FileNotFoundError('未找到 survey.csv 或 mental_health.csv')

    print(f"正在导入演示数据: {source}")
    count = DataService.import_from_file(source)
    print(f"演示数据导入完成: {count} 条")


def main():
    parser = argparse.ArgumentParser(description='初始化项目数据库')
    parser.add_argument('--with-demo-data', action='store_true', help='导入示例 CSV 数据')
    parser.add_argument('--admin-password', default=os.environ.get('ADMIN_PASSWORD', 'Admin123!'))
    parser.add_argument('--skip-accounts', action='store_true', help='只建表，不创建默认账号')
    args = parser.parse_args()

    app = create_app(os.environ.get('FLASK_CONFIG', 'development'))
    with app.app_context():
        db.create_all()
        print('数据库表创建完成')

        backfilled = DataService.backfill_derived_fields()
        if backfilled:
            print(f'已回填派生字段: {backfilled} 条')

        if not args.skip_accounts:
            create_user(
                os.environ.get('ADMIN_USERNAME', 'admin'),
                os.environ.get('ADMIN_EMAIL', 'admin@example.com'),
                args.admin_password,
                'admin'
            )
            create_user(
                os.environ.get('ANALYST_USERNAME', 'analyst'),
                os.environ.get('ANALYST_EMAIL', 'analyst@example.com'),
                os.environ.get('ANALYST_PASSWORD', 'Analyst123!'),
                'analyst'
            )

        if args.with_demo_data:
            seed_demo_data()


if __name__ == '__main__':
    main()
