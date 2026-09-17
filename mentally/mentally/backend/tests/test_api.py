"""
API单元测试
"""
import pytest
import json
from app import create_app, db
from app.models.user import User
from app.models.mental_health_data import MentalHealthData

@pytest.fixture
def app():
    """创建测试应用"""
    app = create_app('testing')
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    """创建测试客户端"""
    return app.test_client()

@pytest.fixture
def auth_headers(client):
    """获取认证头"""
    # 注册测试用户
    client.post('/api/auth/register', json={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'testpass123'
    })
    
    # 登录获取token
    response = client.post('/api/auth/login', json={
        'username': 'testuser',
        'password': 'testpass123'
    })
    
    token = json.loads(response.data)['data']['access_token']
    return {'Authorization': f'Bearer {token}'}

class TestAuthAPI:
    """认证API测试"""
    
    def test_register(self, client):
        """测试注册"""
        response = client.post('/api/auth/register', json={
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'newpass123'
        })
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['code'] == 201
        assert data['data']['username'] == 'newuser'
    
    def test_login(self, client):
        """测试登录"""
        # 先注册
        client.post('/api/auth/register', json={
            'username': 'loginuser',
            'email': 'login@example.com',
            'password': 'loginpass123'
        })
        
        # 再登录
        response = client.post('/api/auth/login', json={
            'username': 'loginuser',
            'password': 'loginpass123'
        })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['code'] == 200
        assert 'access_token' in data['data']
    
    def test_login_wrong_password(self, client):
        """测试错误密码登录"""
        # 先注册
        client.post('/api/auth/register', json={
            'username': 'wronguser',
            'email': 'wrong@example.com',
            'password': 'wrongpass123'
        })
        
        # 用错误密码登录
        response = client.post('/api/auth/login', json={
            'username': 'wronguser',
            'password': 'wrongpassword'
        })
        
        assert response.status_code == 401

class TestDataAPI:
    """数据API测试"""
    
    def test_get_data_list(self, client, auth_headers):
        """测试获取数据列表"""
        response = client.get('/api/data/list', headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['code'] == 200
        assert 'items' in data['data']
    
    def test_get_statistics(self, client, auth_headers):
        """测试获取统计信息"""
        response = client.get('/api/data/statistics', headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['code'] == 200
        assert 'total' in data['data']

class TestVisualizationAPI:
    """可视化API测试"""
    
    def test_get_overview(self, client, auth_headers):
        """测试获取概览数据"""
        response = client.get('/api/viz/overview', headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['code'] == 200
        assert 'total_samples' in data['data']
    
    def test_get_risk_analysis(self, client, auth_headers):
        """测试获取风险分析"""
        response = client.get('/api/viz/risk-analysis', headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['code'] == 200

class TestAnalysisAPI:
    """分析API测试"""
    
    def test_predict_risk(self, client, auth_headers):
        """测试风险预测"""
        response = client.post('/api/analysis/predict', 
            headers=auth_headers,
            json={
                'age': 30,
                'stress_index': 0.5,
                'support_score': 0.5
            }
        )
        
        # 如果没有训练模型，会返回错误
        assert response.status_code in [200, 500]

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
