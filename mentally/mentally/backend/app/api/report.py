# =============================================================================
# report.py — 报告模块 API（生成 / 下载 / 列表 / 预览）
# =============================================================================
# 职责：生成 PDF 分析报告、提供报告文件下载、列表查询和在线预览
# 路由前缀：/api/report/xxx
# PDF生成：使用 reportlab 库，支持中文字体（simhei/simsun/msyh）
# =============================================================================

# ---- Flask 核心 ----
from flask import Blueprint, request, jsonify, send_file, current_app, g
# ---- 业务层 ----
from app.services.report_service import ReportService             # 报告服务（PDF生成核心）
from app.services.visualization_service import VisualizationService  # 可视化服务（提供预览数据）
# ---- 工具库 ----
import os   # 文件系统操作（路径拼接、文件存在检查等）
from werkzeug.utils import secure_filename

from app import db
from app.models.report_record import ReportRecord
from app.utils.permissions import auth_required, roles_required

# 创建报告蓝图，URL前缀 /api/report
report_bp = Blueprint('report', __name__)

# ==========================================================================
# POST /api/report/generate — 生成 PDF 分析报告
# ==========================================================================
# 流程：收集分析数据 → 使用 reportlab 生成 PDF → 保存到磁盘 → 返回报告信息
# 报告结构：封面 → 数据概览 → 风险分析 → 聚类分析 → 模型评估 → 结论建议
# ==========================================================================
@report_bp.route('/generate', methods=['POST'])
@auth_required
def generate_report():
    """生成报告
    
    请求参数（可选）：
    - type: 报告类型（full=完整报告，默认）
    - title: 报告标题（默认：心理健康用户画像分析报告）
    """
    try:
        current_user = g.current_user
        # 解析请求体（如果没有JSON则默认为空字典）
        data = request.get_json() or {}
        
        requested_type = data.get('type', 'full')
        if current_user.role in ['admin', 'analyst']:
            # 管理员和分析师可以生成全局报告或自己的个人报告。
            allowed_types = {'full', 'risk', 'cluster', 'model', 'personal'}
            if requested_type not in allowed_types:
                return jsonify({
                    'code': 400,
                    'message': '不支持的报告类型',
                    'data': None
                }), 400
            report_type = requested_type
        else:
            # 普通用户即使伪造 type=full，也会被强制改成 personal，
            # 避免个人报告服务把全局统计数据混入个人 PDF。
            report_type = 'personal'

        # 报告标题：默认中文标题
        default_title = '个人心理健康评估报告' if report_type == 'personal' else '心理健康用户画像分析报告'
        title = data.get('title') or default_title
        
        # 调用 ReportService 生成 PDF 报告（内部使用 reportlab 绘制）
        result = ReportService.generate_report(
            user_id=current_user.id,    # 生成者ID
            report_type=report_type,     # 报告类型
            title=title                  # 报告标题
        )

        # 文件生成成功后写入所有权记录，后续列表和下载都以这条记录为准。
        record = ReportRecord(
            user_id=current_user.id,
            filename=result['filename'],
            report_type=report_type,
            title=title,
            is_personal=report_type == 'personal'
        )
        db.session.add(record)
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': '报告生成成功',
            'data': {
                **result,
                'report_type': report_type,
                'title': title
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
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
@auth_required
def download_report(filename):
    """下载报告
    
    参数：filename — 报告文件名（如 report_20260317_194010.pdf）
    返回：PDF 文件流（Content-Type: application/pdf）
    """
    try:
        # secure_filename 防止通过 ../ 等路径构造访问报告目录外的文件。
        safe_filename = secure_filename(filename)
        record = ReportRecord.query.filter_by(filename=safe_filename).first()

        if not record:
            return jsonify({
                'code': 404,
                'message': '报告记录不存在',
                'data': None
            }), 404

        # 角色校验之外再做对象级校验：普通用户只能下载自己的报告。
        if g.current_user.role not in ['admin', 'analyst'] and record.user_id != g.current_user.id:
            return jsonify({
                'code': 403,
                'message': '无权限下载该报告',
                'data': None
            }), 403
        
        # 拼接报告文件的完整路径
        filepath = os.path.join(current_app.config['REPORT_PATH'], safe_filename)
        
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
            download_name=safe_filename, # 下载时的文件名
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
@auth_required
def get_report_list():
    """获取报告列表
    
    扫描报告目录中的所有 PDF 文件，按创建时间倒序返回
    """
    try:
        # 列表也必须按所有者过滤，不能只依赖前端隐藏按钮。
        query = ReportRecord.query
        if g.current_user.role not in ['admin', 'analyst']:
            query = query.filter_by(user_id=g.current_user.id)

        reports = [
            record.to_dict()
            for record in query.order_by(ReportRecord.created_at.desc()).all()
        ]
        
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
@roles_required('admin', 'analyst')
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
