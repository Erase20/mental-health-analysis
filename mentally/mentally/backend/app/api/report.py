# =============================================================================
# report.py — 报告模块 API（生成 / 下载 / 列表 / 预览）
# =============================================================================
# 职责：生成 PDF 分析报告、提供报告文件下载、列表查询和在线预览
# 路由前缀：/api/report/xxx
# PDF生成：使用 reportlab 库，支持中文字体（simhei/simsun/msyh）
# =============================================================================

# ---- Flask 核心 ----
from flask import Blueprint, request, jsonify, send_file  # send_file=发送文件给客户端（用于下载）
# ---- JWT 认证 ----
from flask_jwt_extended import jwt_required, get_jwt_identity  # 所有接口需登录
# ---- 业务层 ----
from app.services.report_service import ReportService             # 报告服务（PDF生成核心）
from app.services.visualization_service import VisualizationService  # 可视化服务（提供预览数据）
# ---- 工具库 ----
import os   # 文件系统操作（路径拼接、文件存在检查等）

# 创建报告蓝图，URL前缀 /api/report
report_bp = Blueprint('report', __name__)

# ==========================================================================
# POST /api/report/generate — 生成 PDF 分析报告
# ==========================================================================
# 流程：收集分析数据 → 使用 reportlab 生成 PDF → 保存到磁盘 → 返回报告信息
# 报告结构：封面 → 数据概览 → 风险分析 → 聚类分析 → 模型评估 → 结论建议
# ==========================================================================
@report_bp.route('/generate', methods=['POST'])
@jwt_required()   # 需要登录
def generate_report():
    """生成报告
    
    请求参数（可选）：
    - type: 报告类型（full=完整报告，默认）
    - title: 报告标题（默认：心理健康用户画像分析报告）
    """
    try:
        # 获取当前登录用户ID（用于记录报告生成者）
        current_user_id = get_jwt_identity()
        # 解析请求体（如果没有JSON则默认为空字典）
        data = request.get_json() or {}
        
        # 报告类型：默认为完整报告
        report_type = data.get('type', 'full')
        # 报告标题：默认中文标题
        title = data.get('title', '心理健康用户画像分析报告')
        
        # 调用 ReportService 生成 PDF 报告（内部使用 reportlab 绘制）
        result = ReportService.generate_report(
            user_id=current_user_id,    # 生成者ID
            report_type=report_type,     # 报告类型
            title=title                  # 报告标题
        )
        
        return jsonify({
            'code': 200,
            'message': '报告生成成功',
            'data': result
        }), 200
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'报告生成失败: {str(e)}',
            'data': None
        }), 500

# ==========================================================================
# GET /api/report/download/<filename> — 下载 PDF 报告文件
# ==========================================================================
# 参数：filename — URL路径参数，报告文件名
# 返回：PDF 文件流，浏览器会触发下载行为
# ==========================================================================
@report_bp.route('/download/<filename>', methods=['GET'])
@jwt_required()   # 需要登录
def download_report(filename):
    """下载报告
    
    参数：filename — 报告文件名（如 report_20260317_194010.pdf）
    返回：PDF 文件流（Content-Type: application/pdf）
    """
    try:
        # 局部导入 current_app（获取配置中的报告存储路径）
        from flask import current_app
        
        # 拼接报告文件的完整路径
        filepath = os.path.join(current_app.config['REPORT_PATH'], filename)
        
        # 检查文件是否存在
        if not os.path.exists(filepath):
            return jsonify({
                'code': 404,
                'message': '报告文件不存在',
                'data': None
            }), 404
        
        # 发送 PDF 文件给客户端（触发浏览器下载）
        return send_file(
            filepath,                    # 文件路径
            as_attachment=True,          # 作为附件下载（而不是在浏览器中显示）
            download_name=filename,      # 下载时的文件名
            mimetype='application/pdf'   # MIME类型：PDF文件
        )
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'下载失败: {str(e)}',
            'data': None
        }), 500

# ==========================================================================
# GET /api/report/list — 获取报告文件列表
# ==========================================================================
# 返回：所有已生成的 PDF 报告文件列表（按时间倒序）
# ==========================================================================
@report_bp.route('/list', methods=['GET'])
@jwt_required()   # 需要登录
def get_report_list():
    """获取报告列表
    
    扫描报告目录中的所有 PDF 文件，按创建时间倒序返回
    """
    try:
        # 局部导入
        from flask import current_app
        import glob   # 文件通配符搜索
        
        # 获取报告存储目录路径
        report_path = current_app.config['REPORT_PATH']
        # 搜索目录中所有 PDF 文件
        report_files = glob.glob(os.path.join(report_path, '*.pdf'))
        
        # 构建报告列表
        reports = []
        # 按文件创建时间倒序排列（最新的在前）
        for filepath in sorted(report_files, key=os.path.getctime, reverse=True):
            filename = os.path.basename(filepath)     # 获取文件名
            stat = os.stat(filepath)                   # 获取文件状态信息
            reports.append({
                'filename': filename,                  # 文件名
                'size': stat.st_size,                  # 文件大小（字节）
                'created_at': stat.st_ctime,           # 创建时间（时间戳）
                'download_url': f'/api/report/download/{filename}'  # 下载链接
            })
        
        return jsonify({
            'code': 200,
            'message': '获取成功',
            'data': reports
        }), 200
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取失败: {str(e)}',
            'data': None
        }), 500

# ==========================================================================
# GET /api/report/preview — 报告数据预览（在线查看）
# ==========================================================================
# 返回：可视化数据（概览 + 风险 + 聚类 + 特征），用于前端在线预览报告内容
# 注意：这个接口不返回 PDF，而是返回前端渲染报告页面所需的 JSON 数据
# ==========================================================================
@report_bp.route('/preview', methods=['GET'])
@jwt_required()   # 需要登录
def preview_report_data():
    """预览报告数据
    
    收集报告所需的所有可视化数据并一次性返回，
    前端用这些数据在页面上渲染图表，实现在线预览报告的效果
    """
    try:
        # ① 概览数据（总人数、基本统计）
        overview = VisualizationService.get_overview_stats()
        
        # ② 风险分析数据（各风险等级分布）
        risk_analysis = VisualizationService.get_risk_analysis()
        
        # ③ 聚类分析数据（各群体规模和特征）
        cluster_analysis = VisualizationService.get_cluster_analysis()
        
        # ④ 特征分析数据（特征重要性排名）
        feature_analysis = VisualizationService.get_feature_analysis()
        
        return jsonify({
            'code': 200,
            'message': '获取成功',
            'data': {
                'overview': overview,                 # 概览统计
                'risk_analysis': risk_analysis,        # 风险分析
                'cluster_analysis': cluster_analysis,  # 聚类分析
                'feature_analysis': feature_analysis    # 特征分析
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取失败: {str(e)}',
            'data': None
        }), 500
