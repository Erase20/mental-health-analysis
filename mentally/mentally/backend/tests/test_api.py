"""
API 单元测试：认证、权限、数据导入、分析与报告隔离。
"""
import io
import json
import os
import tempfile

import pytest
from openpyxl import Workbook

from app import create_app, db
from app.models import MentalHealthData, ReportRecord, User, UserProfile


CSV_HEADERS = [
    'Timestamp', 'Age', 'Gender', 'Country', 'state', 'self_employed',
    'family_history', 'treatment', 'work_interfere', 'no_employees',
    'remote_work', 'tech_company', 'benefits', 'care_options',
    'wellness_program', 'seek_help', 'anonymity', 'leave',
    'mental_health_consequence', 'phys_health_consequence', 'coworkers',
    'supervisor', 'mental_health_interview', 'phys_health_interview',
    'mental_vs_physical', 'obs_consequence', 'comments', 'Risk_Level',
    'Age_Group'
]

SAMPLE_ROW = [
    '2026-01-01 10:00:00', 30, 'Female', 'China', 'Beijing', 'No',
    'No', 'No', 'Sometimes', '26-100', 'No', 'Yes', 'Yes', 'Yes',
    'Yes', 'Yes', 'Yes', 'Somewhat easy', 'No', 'No', 'Some of them',
    'Yes', 'No', 'Maybe', 'Yes', 'No', 'test comment', 'Medium Risk',
    '30-35'
]


@pytest.fixture
def app():
    """创建使用独立临时目录的测试应用。"""
    app = create_app('testing')
    temp_root = tempfile.mkdtemp(prefix='mental_health_test_')
    app.config.update(
        DATA_PATH=os.path.join(temp_root, 'data'),
        MODEL_PATH=os.path.join(temp_root, 'models'),
        REPORT_PATH=os.path.join(temp_root, 'reports')
    )
    for path in (app.config['DATA_PATH'], app.config['MODEL_PATH'], app.config['REPORT_PATH']):
        os.makedirs(path, exist_ok=True)

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """创建测试客户端。"""
    return app.test_client()


def register_and_login(client, app, username, email=None, role='user'):
    """注册账号、设置测试角色并返回认证头。"""
    email = email or f'{username}@example.com'
    register_response = client.post('/api/auth/register', json={
        'username': username,
        'email': email,
        'password': 'testpass123',
        'role': role
    })
    assert register_response.status_code == 201

    if role != 'user':
        with app.app_context():
            user = User.query.filter_by(username=username).first()
            user.role = role
            db.session.commit()

    login_response = client.post('/api/auth/login', json={
        'username': username,
        'password': 'testpass123'
    })
    assert login_response.status_code == 200
    token = json.loads(login_response.data)['data']['access_token']
    return {'Authorization': f'Bearer {token}'}


@pytest.fixture
def user_headers(client, app):
    return register_and_login(client, app, 'normaluser')


@pytest.fixture
def analyst_headers(client, app):
    return register_and_login(client, app, 'analyst', role='analyst')


@pytest.fixture
def admin_headers(client, app):
    return register_and_login(client, app, 'adminuser', role='admin')


class TestAuthAPI:
    """认证与注册安全测试。"""

    def test_register_ignores_client_supplied_role(self, client, app):
        response = client.post('/api/auth/register', json={
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'newpass123',
            'role': 'admin'
        })

        assert response.status_code == 201
        with app.app_context():
            user = User.query.filter_by(username='newuser').first()
            assert user.role == 'user'

    def test_login_and_wrong_password(self, client, app):
        register_and_login(client, app, 'loginuser')

        response = client.post('/api/auth/login', json={
            'username': 'loginuser',
            'password': 'wrongpassword'
        })
        assert response.status_code == 401

    def test_disabled_user_token_is_rejected(self, client, app, user_headers):
        with app.app_context():
            user = User.query.filter_by(username='normaluser').first()
            user.is_active = False
            db.session.commit()

        response = client.get('/api/user/assessment-records', headers=user_headers)
        assert response.status_code == 401


class TestPermissionAPI:
    """服务端角色权限测试。"""

    STAFF_ONLY_GET_ENDPOINTS = [
        '/api/data/list',
        '/api/data/statistics',
        '/api/analysis/history',
        '/api/user/profiles',
        '/api/user/profiles/statistics',
        '/api/viz/overview',
        '/api/report/preview',
        '/api/user/accounts'
    ]

    @pytest.mark.parametrize('endpoint', STAFF_ONLY_GET_ENDPOINTS)
    def test_regular_user_cannot_access_staff_endpoints(self, client, user_headers, endpoint):
        response = client.get(endpoint, headers=user_headers)
        assert response.status_code == 403

    def test_regular_user_cannot_run_analysis(self, client, user_headers):
        response = client.post('/api/analysis/run', headers=user_headers)
        assert response.status_code == 403

    @pytest.mark.parametrize('endpoint', STAFF_ONLY_GET_ENDPOINTS)
    def test_analyst_can_access_staff_endpoints(self, client, analyst_headers, endpoint):
        response = client.get(endpoint, headers=analyst_headers)
        assert response.status_code == 200

    def test_only_admin_can_manage_accounts(self, client, app, analyst_headers):
        with app.app_context():
            target = User.query.filter_by(username='analyst').first()
            target_id = target.id

        response = client.delete(f'/api/user/accounts/{target_id}', headers=analyst_headers)
        assert response.status_code == 403


class TestDataUploadAPI:
    """CSV 与 Excel 上传测试。"""

    @staticmethod
    def _csv_file():
        content = ','.join(CSV_HEADERS) + '\n' + ','.join(map(str, SAMPLE_ROW))
        return io.BytesIO(content.encode('utf-8-sig'))

    @staticmethod
    def _xlsx_file():
        workbook = Workbook()
        sheet = workbook.active
        sheet.append(CSV_HEADERS)
        sheet.append(SAMPLE_ROW)
        output = io.BytesIO()
        workbook.save(output)
        output.seek(0)
        return output

    def test_upload_csv(self, client, app, analyst_headers):
        response = client.post(
            '/api/data/upload',
            headers=analyst_headers,
            data={'file': (self._csv_file(), 'survey.csv')},
            content_type='multipart/form-data'
        )

        assert response.status_code == 200
        assert json.loads(response.data)['data']['count'] == 1
        with app.app_context():
            assert MentalHealthData.query.count() == 1
            record = MentalHealthData.query.first()
            assert record.risk_level in {'Low Risk', 'Medium Risk', 'High Risk'}
            assert record.age_group == '26-35岁'

    def test_upload_xlsx(self, client, app, analyst_headers):
        response = client.post(
            '/api/data/upload',
            headers=analyst_headers,
            data={'file': (self._xlsx_file(), 'survey.xlsx')},
            content_type='multipart/form-data'
        )

        assert response.status_code == 200
        assert json.loads(response.data)['data']['count'] == 1
        with app.app_context():
            assert MentalHealthData.query.count() == 1
            record = MentalHealthData.query.first()
            assert record.risk_level in {'Low Risk', 'Medium Risk', 'High Risk'}
            assert record.age_group == '26-35岁'

    def test_regular_user_cannot_upload(self, client, user_headers):
        response = client.post(
            '/api/data/upload',
            headers=user_headers,
            data={'file': (self._csv_file(), 'survey.csv')},
            content_type='multipart/form-data'
        )
        assert response.status_code == 403


class TestAnalysisAPI:
    """分析接口权限与空数据行为测试。"""

    def test_analysis_history_requires_staff_role(self, client, user_headers, analyst_headers):
        denied = client.get('/api/analysis/history', headers=user_headers)
        allowed = client.get('/api/analysis/history', headers=analyst_headers)

        assert denied.status_code == 403
        assert allowed.status_code == 200
        assert json.loads(allowed.data)['data'] == []


class TestReportAPI:
    """报告列表、下载和预览权限测试。"""

    def test_user_only_sees_own_reports(self, client, app, user_headers, analyst_headers):
        with app.app_context():
            normal_user = User.query.filter_by(username='normaluser').first()
            analyst = User.query.filter_by(username='analyst').first()
            db.session.add_all([
                ReportRecord(
                    user_id=normal_user.id,
                    filename='normal_report.pdf',
                    report_type='personal',
                    title='个人报告',
                    is_personal=True
                ),
                ReportRecord(
                    user_id=analyst.id,
                    filename='analyst_report.pdf',
                    report_type='full',
                    title='全局报告',
                    is_personal=False
                )
            ])
            db.session.commit()

        user_response = client.get('/api/report/list', headers=user_headers)
        analyst_response = client.get('/api/report/list', headers=analyst_headers)

        user_reports = json.loads(user_response.data)['data']
        analyst_reports = json.loads(analyst_response.data)['data']
        assert [item['filename'] for item in user_reports] == ['normal_report.pdf']
        assert len(analyst_reports) == 2

    def test_user_cannot_download_another_users_report(self, client, app, user_headers):
        with app.app_context():
            analyst = User(
                username='reportowner',
                email='reportowner@example.com',
                role='analyst'
            )
            analyst.set_password('testpass123')
            db.session.add(analyst)
            db.session.flush()
            db.session.add(ReportRecord(
                user_id=analyst.id,
                filename='private_report.pdf',
                report_type='full',
                title='私有报告',
                is_personal=False
            ))
            db.session.commit()

        response = client.get(
            '/api/report/download/private_report.pdf',
            headers=user_headers
        )
        assert response.status_code == 403


class TestAssessmentOwnership:
    """普通用户只能查看自己的自评记录。"""

    def test_user_cannot_view_another_users_assessment(self, client, app, user_headers):
        with app.app_context():
            other = User(
                username='otheruser',
                email='other@example.com',
                role='user'
            )
            other.set_password('testpass123')
            db.session.add(other)
            db.session.flush()
            profile = UserProfile(
                user_id=other.id,
                data_id=None,
                risk_score=60,
                risk_level='Medium Risk',
                description='other assessment'
            )
            db.session.add(profile)
            db.session.commit()
            profile_id = profile.id

        response = client.get(
            f'/api/user/assessment-records/{profile_id}',
            headers=user_headers
        )
        assert response.status_code == 403
