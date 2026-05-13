from flask import Flask, request, send_file, render_template
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
import os, io
from pdfutils import pdf_to_text

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # 2MB limit

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return 'No file part', 400
    
    file = request.files['file']
    filename = file.filename
    if filename == '':
        return 'No selected file', 400
    
    if '..' in filename or '/' in filename:
        return 'directory traversal is not allowed', 403 

    pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    pdf_content = file.stream.read()

    try:
        # just if is a pdf
        parser = PDFParser(io.BytesIO(pdf_content))
        doc = PDFDocument(parser)
    except Exception as e:
        return str(e), 500
    
    with open(pdf_path, 'wb') as f:
        f.write(pdf_content)

    md_filename = os.path.splitext(filename)[0] + '.txt'
    txt_path = os.path.join(app.config['UPLOAD_FOLDER'], md_filename)

    try:
        pdf_to_text(pdf_path, txt_path)
    except Exception as e:
        return str(e), 500 
    
    return send_file(txt_path, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
