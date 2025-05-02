import os
import json
import datetime
from flask import Flask, render_template, request, redirect, url_for, send_file
from detector import WeaponDetector
import pandas as pd
from fpdf import FPDF
from dotenv import load_dotenv


app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'mp4', 'avi', 'mov'}
app.config['HISTORY_FILE'] = 'data/history.json'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max upload size

# Создаем необходимые директории, если они отсутствуют
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('data', exist_ok=True)
os.makedirs('static/results', exist_ok=True)

# Инициализация детектора оружия через API
load_dotenv()  
api_key = os.getenv("ROBOFLOW_API_KEY")
detector = WeaponDetector(api_key=api_key)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def load_history():
    if os.path.exists(app.config['HISTORY_FILE']):
        with open(app.config['HISTORY_FILE'], 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

def save_history(history):
    with open(app.config['HISTORY_FILE'], 'w') as f:
        json.dump(history, f, indent=4)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/detect', methods=['POST'])
def detect():
    if 'file' not in request.files:
        return redirect(request.url)
    
    file = request.files['file']
    
    if file.filename == '':
        return redirect(request.url)
    
    if file and allowed_file(file.filename):
        # Генерируем имя файла с использованием текущей даты и времени
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        file_ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"{timestamp}.{file_ext}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # Определяем тип файла (изображение или видео)
        is_video = file_ext in ['mp4', 'avi', 'mov']
        
        # Запускаем детекцию через API
        try:
            if is_video:
                result_path, detections = detector.detect_video(file_path)
            else:
                result_path, detections = detector.detect_image(file_path)
        except Exception as e:
            print(f"Error during detection: {e}")
            return redirect(url_for('index'))
        
        # Сохраняем результаты в историю
        history = load_history()
        history_entry = {
            'id': len(history) + 1,
            'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'filename': filename,
            'result_path': result_path.replace('static/', ''),
            'detections': detections,
            'is_video': is_video
        }
        history.append(history_entry)
        save_history(history)
        
        return render_template('result.html', result=history_entry)
    
    return redirect(url_for('index'))

@app.route('/history')
def history():
    history_data = load_history()
    return render_template('history.html', history=history_data)

@app.route('/export_report/<format>')
def export_report(format):
    history_data = load_history()
    
    if format == 'pdf':
        # Создаем PDF отчет
        pdf = FPDF()
        pdf.add_page()
        
        # Устанавливаем шрифт с поддержкой Unicode
        pdf.add_font('DejaVu', '', 'static/fonts/DejaVuSans.ttf', uni=True)
        pdf.set_font("DejaVu", size=12)
        
        # Заголовок
        pdf.cell(200, 10, txt="Отчет о детекции опасных предметов", ln=True, align='C')
        pdf.ln(10)
        
        # Таблица с данными
        pdf.cell(10, 10, "ID", 1)
        pdf.cell(60, 10, "Дата и время", 1)
        pdf.cell(60, 10, "Файл", 1)
        pdf.cell(60, 10, "Обнаружено объектов", 1)
        pdf.ln()
        
        for entry in history_data:
            detected_weapons = len(entry['detections'])  # Количество найденных объектов
            pdf.cell(10, 10, str(entry['id']), 1)
            pdf.cell(60, 10, entry['timestamp'], 1)
            pdf.cell(60, 10, entry['filename'], 1)
            pdf.cell(60, 10, str(detected_weapons), 1)
            pdf.ln()
        
        report_path = os.path.join('data', 'weapon_detection_report.pdf')
        pdf.output(report_path)
        
        return send_file(report_path, as_attachment=True)
    
    elif format == 'excel':
        # Создаем Excel отчет
        data = []
        for entry in history_data:
            detected_weapons = len(entry['detections'])  # Количество найденных объектов
            data.append({
                'ID': entry['id'],
                'Дата и время': entry['timestamp'],
                'Файл': entry['filename'],
                'Обнаружено объектов': detected_weapons,
                'Тип объектов': ', '.join([f"{d['class']}" for d in entry['detections']])
            })
        
        df = pd.DataFrame(data)
        report_path = os.path.join('data', 'weapon_detection_report.xlsx')
        df.to_excel(report_path, index=False)
        
        return send_file(report_path, as_attachment=True)
    
    return redirect(url_for('history'))

if __name__ == '__main__':
    app.run(debug=True)