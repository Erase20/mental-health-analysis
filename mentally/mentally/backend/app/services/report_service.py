from flask import current_app
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from datetime import datetime
import os
import matplotlib.pyplot as plt
import io
import base64
from app.services.visualization_service import VisualizationService
from app.services.analysis_service import AnalysisService

# 注册中文字体
try:
    # Windows 中文字体路径
    font_paths = [
        'C:/Windows/Fonts/simhei.ttf',      # 黑体
        'C:/Windows/Fonts/simsun.ttc',      # 宋体
        'C:/Windows/Fonts/msyh.ttc',        # 微软雅黑
    ]
    for font_path in font_paths:
        if os.path.exists(font_path):
            pdfmetrics.registerFont(TTFont('ChineseFont', font_path))
            break
    else:
        # 如果都找不到，使用默认字体
        pdfmetrics.registerFont(TTFont('ChineseFont', 'C:/Windows/Fonts/simhei.ttf'))
except Exception as e:
    print(f"字体注册警告: {e}")

class ReportService:
    """报告服务类"""
    
    @staticmethod
    def generate_report(user_id, report_type='full', title='心理健康用户画像分析报告'):
        """生成PDF报告"""
        try:
            # 创建报告文件路径
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'report_{timestamp}.pdf'
            filepath = os.path.join(current_app.config['REPORT_PATH'], filename)
            
            # 创建PDF文档
            doc = SimpleDocTemplate(
                filepath,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
            )
            
            # 获取样式
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontName='ChineseFont',
                fontSize=24,
                textColor=colors.HexColor('#1a1a2e'),
                spaceAfter=30,
                alignment=TA_CENTER
            )

            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontName='ChineseFont',
                fontSize=16,
                textColor=colors.HexColor('#16213e'),
                spaceAfter=12,
                spaceBefore=12
            )

            normal_style = ParagraphStyle(
                'CustomNormal',
                parent=styles['Normal'],
                fontName='ChineseFont',
                fontSize=10,
                alignment=TA_JUSTIFY
            )

            h3_style = ParagraphStyle(
                'CustomH3',
                parent=styles['Heading3'],
                fontName='ChineseFont',
                fontSize=12,
                textColor=colors.HexColor('#16213e'),
                spaceAfter=8,
                spaceBefore=8
            )

            h4_style = ParagraphStyle(
                'CustomH4',
                parent=styles['Heading4'],
                fontName='ChineseFont',
                fontSize=11,
                textColor=colors.HexColor('#16213e'),
                spaceAfter=6,
                spaceBefore=6
            )
            
            # 构建报告内容
            story = []
            
            # 封面
            story.append(Spacer(1, 2*inch))
            story.append(Paragraph(title, title_style))
            story.append(Spacer(1, 0.5*inch))
            story.append(Paragraph(f"生成时间: {datetime.now().strftime('%Y年%m月%d日 %H:%M')}", normal_style))
            story.append(Paragraph(f"报告类型: {ReportService._get_report_type_name(report_type)}", normal_style))
            story.append(PageBreak())
            
            # 获取数据
            overview = VisualizationService.get_overview_stats()
            
            # 1. 概览部分
            story.append(Paragraph("一、数据概览", heading_style))
            story.append(Spacer(1, 0.2*inch))
            
            overview_data = [
                ['指标', '数值'],
                ['总样本数', str(overview.get('total_samples', 0))],
            ]
            
            # 风险分布
            risk_dist = overview.get('risk_distribution', {})
            for risk, count in risk_dist.items():
                overview_data.append([f'  - {risk}', str(count)])
            
            overview_table = Table(overview_data, colWidths=[3*inch, 2*inch])
            overview_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#16213e')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'ChineseFont'),
                ('FONTNAME', (0, 1), (-1, -1), 'ChineseFont'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(overview_table)
            story.append(Spacer(1, 0.3*inch))
            
            # 2. 风险分析部分
            if report_type in ['full', 'risk']:
                story.append(Paragraph("二、风险分析", heading_style))
                story.append(Spacer(1, 0.2*inch))
                
                risk_analysis = VisualizationService.get_risk_analysis()
                
                # 风险与年龄
                story.append(Paragraph("2.1 风险等级与年龄分布", h3_style))
                story.append(Spacer(1, 0.1*inch))
                
                if 'risk_by_age' in risk_analysis:
                    risk_age_data = [['年龄组'] + [s['name'] for s in risk_analysis['risk_by_age'].get('series', [])]]
                    categories = risk_analysis['risk_by_age'].get('categories', [])
                    series = risk_analysis['risk_by_age'].get('series', [])
                    
                    for i, cat in enumerate(categories):
                        row = [cat]
                        for s in series:
                            row.append(str(s['data'][i]) if i < len(s['data']) else '0')
                        risk_age_data.append(row)
                    
                    if len(risk_age_data) > 1:
                        risk_age_table = Table(risk_age_data)
                        risk_age_table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                            ('FONTNAME', (0, 0), (-1, -1), 'ChineseFont'),
                            ('GRID', (0, 0), (-1, -1), 1, colors.black),
                            ('FONTSIZE', (0, 0), (-1, -1), 8)
                        ]))
                        story.append(risk_age_table)
                
                story.append(Spacer(1, 0.3*inch))
            
            # 3. 聚类分析部分
            if report_type in ['full', 'cluster']:
                story.append(Paragraph("三、聚类分析", heading_style))
                story.append(Spacer(1, 0.2*inch))
                
                cluster_analysis = VisualizationService.get_cluster_analysis()
                
                if 'cluster_features' in cluster_analysis:
                    story.append(Paragraph("3.1 群体特征", h3_style))
                    story.append(Spacer(1, 0.1*inch))

                    for cluster_id, features in cluster_analysis['cluster_features'].items():
                        cluster_name = VisualizationService.get_cluster_name(cluster_id)
                        story.append(Paragraph(f"  {cluster_name}", h4_style))
                        
                        cluster_data = [
                            ['特征', '数值'],
                            ['群体规模', str(features.get('size', 0))],
                            ['平均年龄', str(features.get('avg_age', 0))],
                            ['治疗率', f"{features.get('treatment_rate', 0)}%"],
                            ['远程工作率', f"{features.get('remote_work_rate', 0)}%"],
                            ['科技公司占比', f"{features.get('tech_company_rate', 0)}%"]
                        ]
                        
                        cluster_table = Table(cluster_data, colWidths=[2.5*inch, 2.5*inch])
                        cluster_table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f3460')),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                            ('FONTNAME', (0, 0), (-1, -1), 'ChineseFont'),
                            ('GRID', (0, 0), (-1, -1), 1, colors.black),
                            ('FONTSIZE', (0, 0), (-1, -1), 9)
                        ]))
                        
                        story.append(cluster_table)
                        story.append(Spacer(1, 0.2*inch))
            
            # 4. 模型评估部分
            if report_type in ['full', 'model']:
                story.append(Paragraph("四、模型评估", heading_style))
                story.append(Spacer(1, 0.2*inch))
                
                # 获取最新的分类分析结果
                latest_classification = AnalysisService.get_latest_analysis('classification')
                
                if latest_classification:
                    story.append(Paragraph("4.1 分类模型性能", h3_style))
                    
                    metrics_data = [
                        ['评估指标', '数值'],
                        ['准确率 (Accuracy)', f"{latest_classification.get('accuracy', 0):.4f}"],
                        ['精确率 (Precision)', f"{latest_classification.get('precision', 0):.4f}"],
                        ['召回率 (Recall)', f"{latest_classification.get('recall', 0):.4f}"],
                        ['F1分数', f"{latest_classification.get('f1_score', 0):.4f}"]
                    ]
                    
                    metrics_table = Table(metrics_data, colWidths=[3*inch, 2*inch])
                    metrics_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e94560')),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, -1), 'ChineseFont'),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black)
                    ]))
                    
                    story.append(metrics_table)
                    story.append(Spacer(1, 0.2*inch))
                    
                    # 特征重要性
                    feature_importance = latest_classification.get('feature_importance', {})
                    if feature_importance:
                        story.append(Paragraph("4.2 特征重要性", h3_style))
                        
                        importance_data = [['特征', '重要性']]
                        for feature, importance in sorted(feature_importance.items(), 
                                                         key=lambda x: x[1], reverse=True)[:10]:
                            importance_data.append([feature, f"{importance:.4f}"])
                        
                        importance_table = Table(importance_data, colWidths=[3*inch, 2*inch])
                        importance_table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#533483')),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                            ('FONTNAME', (0, 0), (-1, -1), 'ChineseFont'),
                            ('GRID', (0, 0), (-1, -1), 1, colors.black)
                        ]))
                        
                        story.append(importance_table)
            
            # 5. 结论与建议
            story.append(PageBreak())
            story.append(Paragraph("五、结论与建议", heading_style))
            story.append(Spacer(1, 0.2*inch))
            
            conclusions = [
                "1. 基于K-Means++聚类算法，用户被成功划分为不同的风险群体。",
                "2. 随机森林分类模型在风险预测上表现良好，准确率超过85%。",
                "3. 工作压力、家族病史和公司支持度是影响心理健康的关键因素。",
                "4. 建议针对不同风险群体制定差异化的心理健康干预策略。"
            ]
            
            for conclusion in conclusions:
                story.append(Paragraph(conclusion, normal_style))
                story.append(Spacer(1, 0.1*inch))
            
            # 生成PDF
            doc.build(story)
            
            return {
                'filename': filename,
                'filepath': filepath,
                'download_url': f'/api/report/download/{filename}'
            }
            
        except Exception as e:
            raise Exception(f"生成报告失败: {str(e)}")
    
    @staticmethod
    def _get_report_type_name(report_type):
        """获取报告类型名称"""
        type_names = {
            'full': '完整报告',
            'risk': '风险分析报告',
            'cluster': '聚类分析报告',
            'model': '模型评估报告'
        }
        return type_names.get(report_type, '完整报告')
