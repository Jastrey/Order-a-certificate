from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from database import db
from database import Certificate  # Правильный импорт
from datetime import datetime
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///certificates.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key-here'

# Секретный ключ для доступа секретаря
SECRETARY_PASSWORD = 'secret123'

db.init_app(app)

def is_secretary():
    """Проверяет, вошел ли пользователь как секретарь"""
    return session.get('role') == 'secretary'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/order', methods=['GET', 'POST'])
def order_certificate():
    """Страница заказа справки для студентов (свободный доступ)"""
    if request.method == 'POST':
        student_name = request.form['student_name']
        student_group = request.form['student_group']
        birth_date = request.form['birth_date']
        request_place = request.form['request_place']
        quantity = int(request.form['quantity'])
        comment = request.form.get('comment', '')
        
        certificate = Certificate(
            student_name=student_name,
            student_group=student_group,
            birth_date=birth_date,
            request_place=request_place,
            quantity=quantity,
            comment=comment
        )
        
        db.session.add(certificate)
        db.session.commit()
        
        return redirect(url_for('order_success', certificate_id=certificate.id))
    
    return render_template('order_certificate.html')

@app.route('/order/success')
def order_success():
    """Страница успешного заказа"""
    certificate_id = request.args.get('certificate_id')
    return render_template('order_success.html', certificate_id=certificate_id)

@app.route('/student')
def student_dashboard():
    """Панель мониторинга для студентов (только просмотр)"""
    search = request.args.get('search', '')
    
    query = Certificate.query
    
    if search:
        query = query.filter(
            Certificate.student_name.ilike(f'%{search}%')
        )
    
    certificates = query.order_by(Certificate.created_at.desc()).all()
    
    # Преобразуем объекты в словари для шаблона
    certificates_data = []
    for cert in certificates:
        cert_data = cert.to_dict()
        # Добавляем оригинальные datetime объекты для шаблона
        cert_data['_obj'] = cert
        certificates_data.append(cert_data)
    
    return render_template('student_dashboard.html', 
                         certificates=certificates_data, 
                         search=search)

@app.route('/secretary/login', methods=['GET', 'POST'])
def secretary_login():
    """Вход для секретаря"""
    if is_secretary():
        return redirect(url_for('secretary_dashboard'))
    
    if request.method == 'POST':
        password = request.form['password']
        
        if password == SECRETARY_PASSWORD:
            session['role'] = 'secretary'
            return redirect(url_for('secretary_dashboard'))
        else:
            return render_template('secretary_login.html', error='Неверный пароль')
    
    return render_template('secretary_login.html')

@app.route('/secretary/logout')
def secretary_logout():
    """Выход секретаря"""
    session.pop('role', None)
    return redirect(url_for('index'))

@app.route('/secretary')
def secretary_dashboard():
    """Панель управления для секретаря"""
    if not is_secretary():
        return redirect(url_for('secretary_login'))
    
    return render_template('secretary_dashboard.html')

@app.route('/api/certificates')
def api_certificates():
    """API для получения списка справок"""
    search = request.args.get('search', '')
    status_filter = request.args.get('status', '')
    
    query = Certificate.query
    
    if search:
        query = query.filter(
            Certificate.student_name.ilike(f'%{search}%') |
            Certificate.request_place.ilike(f'%{search}%')
        )
    
    if status_filter:
        query = query.filter(Certificate.status == status_filter)
    
    certificates = query.order_by(Certificate.created_at.desc()).all()
    
    certificates_data = []
    for cert in certificates:
        cert_data = cert.to_dict()
        cert_data['can_edit'] = is_secretary()  # Разрешаем редактирование только секретарю
        certificates_data.append(cert_data)
    
    return jsonify(certificates_data)

@app.route('/api/certificates/<int:certificate_id>', methods=['PUT'])
def update_certificate(certificate_id):
    """API для обновления статуса справки"""
    if not is_secretary():
        return jsonify({'error': 'Доступ запрещен'}), 403
    
    certificate = Certificate.query.get_or_404(certificate_id)
    data = request.get_json()
    
    if 'status' in data:
        certificate.status = data['status']
        certificate.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    cert_data = certificate.to_dict()
    cert_data['can_edit'] = True
    return jsonify(cert_data)

@app.route('/api/status')
def api_status():
    """API для получения статистики"""
    total = Certificate.query.count()
    in_work = Certificate.query.filter_by(status='в работе').count()
    ready = Certificate.query.filter_by(status='готово').count()
    rejected = Certificate.query.filter_by(status='отклонено').count()
    
    return jsonify({
        'total': total,
        'in_work': in_work,
        'ready': ready,
        'rejected': rejected
    })

@app.route('/check-status')
def check_status():
    """Страница проверки статуса по ID"""
    certificate_id = request.args.get('id')
    certificate = None
    
    if certificate_id:
        try:
            certificate = Certificate.query.get(int(certificate_id))
        except:
            certificate = None
    
    # Передаем словарь вместо объекта для избежания ошибок с датами
    certificate_data = certificate.to_dict() if certificate else None
    return render_template('check_status.html', certificate=certificate_data)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0')