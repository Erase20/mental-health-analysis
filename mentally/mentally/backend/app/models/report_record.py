from datetime import datetime

from app import db


class ReportRecord(db.Model):
    """报告元数据表，用于实现报告归属和下载权限。

    学习重点：
    PDF 文件本身只包含文件名，无法可靠判断“谁生成的报告”。
    因此数据库需要单独记录报告所有者，下载前再校验 owner。
    """

    __tablename__ = 'report_records'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    filename = db.Column(db.String(255), unique=True, nullable=False, index=True)
    report_type = db.Column(db.String(30), nullable=False)  # full/risk/cluster/model/personal
    title = db.Column(db.String(255), nullable=False)
    is_personal = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship('User', backref=db.backref('report_records', lazy='dynamic'))

    def to_dict(self):
        """转换为接口返回结构。文件不存在时仍保留记录，但 size 为 0。"""
        file_size = 0
        try:
            from flask import current_app
            import os

            filepath = os.path.join(current_app.config['REPORT_PATH'], self.filename)
            if os.path.exists(filepath):
                file_size = os.path.getsize(filepath)
        except RuntimeError:
            pass

        return {
            'id': self.id,
            'user_id': self.user_id,
            'filename': self.filename,
            'report_type': self.report_type,
            'title': self.title,
            'is_personal': self.is_personal,
            'size': file_size,
            'created_at': self.created_at.timestamp() if self.created_at else None,
            'download_url': f'/api/report/download/{self.filename}'
        }
