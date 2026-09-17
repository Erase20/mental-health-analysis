"""
性能测试模块
使用Locust进行API性能测试
"""
import time
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
import json
from datetime import datetime

class PerformanceTester:
    """性能测试类"""
    
    def __init__(self, base_url='http://localhost:5000', token=None):
        self.base_url = base_url
        self.token = token
        self.headers = {
            'Content-Type': 'application/json'
        }
        if token:
            self.headers['Authorization'] = f'Bearer {token}'
        
        self.results = []
    
    def test_endpoint(self, method, endpoint, data=None, iterations=100):
        """测试单个接口性能"""
        url = f"{self.base_url}{endpoint}"
        response_times = []
        errors = []
        
        print(f"\n测试接口: {method} {endpoint}")
        print(f"迭代次数: {iterations}")
        
        for i in range(iterations):
            start_time = time.time()
            try:
                if method.upper() == 'GET':
                    response = requests.get(url, headers=self.headers, timeout=30)
                elif method.upper() == 'POST':
                    response = requests.post(url, json=data, headers=self.headers, timeout=30)
                elif method.upper() == 'PUT':
                    response = requests.put(url, json=data, headers=self.headers, timeout=30)
                elif method.upper() == 'DELETE':
                    response = requests.delete(url, headers=self.headers, timeout=30)
                else:
                    raise ValueError(f"不支持的HTTP方法: {method}")
                
                response_time = (time.time() - start_time) * 1000  # 转换为毫秒
                response_times.append(response_time)
                
                if response.status_code >= 400:
                    errors.append({
                        'iteration': i,
                        'status_code': response.status_code,
                        'response': response.text
                    })
                    
            except Exception as e:
                errors.append({
                    'iteration': i,
                    'error': str(e)
                })
        
        # 计算统计指标
        if response_times:
            result = {
                'endpoint': endpoint,
                'method': method,
                'iterations': iterations,
                'successful_requests': len(response_times),
                'failed_requests': len(errors),
                'avg_response_time': statistics.mean(response_times),
                'min_response_time': min(response_times),
                'max_response_time': max(response_times),
                'median_response_time': statistics.median(response_times),
                'p95_response_time': self._percentile(response_times, 95),
                'p99_response_time': self._percentile(response_times, 99),
                'requests_per_second': len(response_times) / sum(response_times) * 1000,
                'errors': errors[:5]  # 只保留前5个错误
            }
        else:
            result = {
                'endpoint': endpoint,
                'method': method,
                'iterations': iterations,
                'successful_requests': 0,
                'failed_requests': len(errors),
                'errors': errors
            }
        
        self.results.append(result)
        self._print_result(result)
        return result
    
    def test_concurrent(self, method, endpoint, data=None, concurrent_users=10, requests_per_user=10):
        """并发性能测试"""
        url = f"{self.base_url}{endpoint}"
        response_times = []
        errors = []
        
        print(f"\n并发测试接口: {method} {endpoint}")
        print(f"并发用户数: {concurrent_users}")
        print(f"每用户请求数: {requests_per_user}")
        
        def make_request(user_id, request_id):
            start_time = time.time()
            try:
                if method.upper() == 'GET':
                    response = requests.get(url, headers=self.headers, timeout=30)
                elif method.upper() == 'POST':
                    response = requests.post(url, json=data, headers=self.headers, timeout=30)
                else:
                    raise ValueError(f"不支持的HTTP方法: {method}")
                
                response_time = (time.time() - start_time) * 1000
                return {'success': True, 'time': response_time, 'status': response.status_code}
            except Exception as e:
                return {'success': False, 'error': str(e)}
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = []
            for user_id in range(concurrent_users):
                for request_id in range(requests_per_user):
                    future = executor.submit(make_request, user_id, request_id)
                    futures.append(future)
            
            for future in as_completed(futures):
                result = future.result()
                if result['success']:
                    response_times.append(result['time'])
                else:
                    errors.append(result)
        
        total_time = time.time() - start_time
        
        result = {
            'endpoint': endpoint,
            'method': method,
            'concurrent_users': concurrent_users,
            'requests_per_user': requests_per_user,
            'total_requests': concurrent_users * requests_per_user,
            'successful_requests': len(response_times),
            'failed_requests': len(errors),
            'total_time': total_time,
            'avg_response_time': statistics.mean(response_times) if response_times else 0,
            'min_response_time': min(response_times) if response_times else 0,
            'max_response_time': max(response_times) if response_times else 0,
            'median_response_time': statistics.median(response_times) if response_times else 0,
            'p95_response_time': self._percentile(response_times, 95) if response_times else 0,
            'requests_per_second': len(response_times) / total_time if total_time > 0 else 0,
            'errors': errors[:5]
        }
        
        self.results.append(result)
        self._print_concurrent_result(result)
        return result
    
    def _percentile(self, data, percentile):
        """计算百分位数"""
        size = len(data)
        sorted_data = sorted(data)
        index = int(size * percentile / 100)
        return sorted_data[min(index, size - 1)]
    
    def _print_result(self, result):
        """打印测试结果"""
        print(f"\n测试结果:")
        print(f"  成功请求: {result['successful_requests']}/{result['iterations']}")
        print(f"  失败请求: {result['failed_requests']}")
        if result['successful_requests'] > 0:
            print(f"  平均响应时间: {result['avg_response_time']:.2f} ms")
            print(f"  最小响应时间: {result['min_response_time']:.2f} ms")
            print(f"  最大响应时间: {result['max_response_time']:.2f} ms")
            print(f"  中位数响应时间: {result['median_response_time']:.2f} ms")
            print(f"  P95响应时间: {result['p95_response_time']:.2f} ms")
            print(f"  P99响应时间: {result['p99_response_time']:.2f} ms")
            print(f"  每秒请求数: {result['requests_per_second']:.2f}")
        if result.get('errors'):
            print(f"  错误示例: {result['errors'][:2]}")
    
    def _print_concurrent_result(self, result):
        """打印并发测试结果"""
        print(f"\n并发测试结果:")
        print(f"  总请求数: {result['total_requests']}")
        print(f"  成功请求: {result['successful_requests']}")
        print(f"  失败请求: {result['failed_requests']}")
        print(f"  总耗时: {result['total_time']:.2f} s")
        if result['successful_requests'] > 0:
            print(f"  平均响应时间: {result['avg_response_time']:.2f} ms")
            print(f"  P95响应时间: {result['p95_response_time']:.2f} ms")
            print(f"  每秒请求数: {result['requests_per_second']:.2f}")
    
    def generate_report(self, filename=None):
        """生成测试报告"""
        if not filename:
            filename = f"performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        report = {
            'test_time': datetime.now().isoformat(),
            'base_url': self.base_url,
            'total_tests': len(self.results),
            'results': self.results
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n测试报告已保存: {filename}")
        return filename


def run_api_tests():
    """运行API性能测试"""
    # 先登录获取token
    login_data = {
        'username': 'admin',
        'password': 'admin123'
    }
    
    try:
        response = requests.post(
            'http://localhost:5000/api/auth/login',
            json=login_data,
            headers={'Content-Type': 'application/json'}
        )
        token = response.json()['data']['access_token']
        print(f"登录成功，获取Token")
    except Exception as e:
        print(f"登录失败: {e}")
        token = None
    
    # 创建测试器
    tester = PerformanceTester(token=token)
    
    # 测试各个接口
    print("\n" + "="*60)
    print("开始API性能测试")
    print("="*60)
    
    # 1. 测试概览接口
    tester.test_endpoint('GET', '/api/viz/overview', iterations=100)
    
    # 2. 测试数据列表接口
    tester.test_endpoint('GET', '/api/data/list?page=1&per_page=20', iterations=50)
    
    # 3. 测试用户画像列表接口
    tester.test_endpoint('GET', '/api/user/profiles?page=1&per_page=20', iterations=50)
    
    # 4. 测试风险分析接口
    tester.test_endpoint('GET', '/api/viz/risk-analysis', iterations=50)
    
    # 5. 测试聚类分析接口
    tester.test_endpoint('GET', '/api/viz/cluster-analysis', iterations=50)
    
    # 6. 并发测试
    print("\n" + "="*60)
    print("开始并发性能测试")
    print("="*60)
    
    tester.test_concurrent('GET', '/api/viz/overview', concurrent_users=10, requests_per_user=10)
    tester.test_concurrent('GET', '/api/data/list?page=1&per_page=20', concurrent_users=5, requests_per_user=10)
    
    # 生成报告
    tester.generate_report()


if __name__ == '__main__':
    run_api_tests()
