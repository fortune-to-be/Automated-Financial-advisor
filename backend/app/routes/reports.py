"""Report export endpoints: CSV and PDF"""

from flask import Blueprint, request, Response, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from io import BytesIO

from app.services.reports import ReportsService

reports_bp = Blueprint('reports', __name__, url_prefix='/api/reports')

service = ReportsService()


def _parse_date(param):
    if not param:
        return None
    try:
        return datetime.fromisoformat(param)
    except ValueError:
        return None


@reports_bp.route('/expenses', methods=['GET'])
@jwt_required()
def export_expenses():
    user_id = get_jwt_identity()
    start = _parse_date(request.args.get('start'))
    end = _parse_date(request.args.get('end'))

    try:
        generator = service.stream_expenses_csv(user_id=user_id, start_date=start, end_date=end)
        headers = {
            'Content-Type': 'text/csv',
            'Content-Disposition': f'attachment; filename="expenses_{user_id}.csv"'
        }
        return Response(generator, headers=headers)
    except Exception as e:
        return jsonify({'error': f'Failed to generate CSV: {str(e)}'}), 500


@reports_bp.route('/summary', methods=['GET'])
@jwt_required()
def summary():
    user_id = get_jwt_identity()
    start = _parse_date(request.args.get('start'))
    end = _parse_date(request.args.get('end'))
    fmt = request.args.get('format', '').lower()

    try:
        summary = service.get_summary(user_id=user_id, start_date=start, end_date=end)

        if fmt == 'pdf' or request.headers.get('Accept', '').lower().find('pdf') != -1:
            pdf_bytes = service.generate_summary_pdf(summary, user_id=user_id)
            return Response(pdf_bytes, mimetype='application/pdf', headers={
                'Content-Disposition': f'attachment; filename="summary_{user_id}.pdf"'
            })

        return jsonify({'data': summary}), 200

    except Exception as e:
        return jsonify({'error': f'Failed to generate summary: {str(e)}'}), 500
