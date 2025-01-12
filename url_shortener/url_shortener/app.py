from flask import Flask, render_template, request, redirect, url_for, flash, abort, session, jsonify
import json
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'static', 'user_files')
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = 'your_secret_key'

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def home():
    return render_template('index.html', codes=session.keys())

@app.route('/your-url', methods=['GET', 'POST'])
def your_url():
    if request.method == 'POST':
        urls = {}
        if os.path.exists('urls.json'):
            try:
                with open('urls.json') as urls_file:
                    urls = json.load(urls_file)
            except json.JSONDecodeError:
                flash('Error reading URL data. Please try again.')
                return redirect(url_for('home'))

        code = request.form['code']
        if code in urls.keys():
            flash('That short name has already been taken. Please select another name.')
            return redirect(url_for('home'))

        if 'url' in request.form:
            urls[code] = {'url': request.form['url']}
        elif 'file' in request.files:
            f = request.files['file']
            if f and allowed_file(f.filename):
                full_name = code + '_' + secure_filename(f.filename)
                file_path = os.path.join(UPLOAD_FOLDER, full_name)
                f.save(file_path)
                urls[code] = {'file': full_name}
            else:
                flash('Invalid file type. Allowed types: ' + ', '.join(ALLOWED_EXTENSIONS))
                return redirect(url_for('home'))

        try:
            with open('urls.json', 'w') as url_file:
                json.dump(urls, url_file)
            session[code] = True
        except Exception as e:
            flash(f"Error saving URL data: {e}")
            return redirect(url_for('home'))

        return render_template('your_url.html', code=code)
    else:
        return redirect(url_for('home'))

@app.route('/<string:code>')
def redirect_to_url(code):
    if os.path.exists('urls.json'):
        try:
            with open('urls.json') as urls_file:
                urls = json.load(urls_file)
                if code in urls.keys():
                    if 'url' in urls[code]:
                        return redirect(urls[code]['url'])
                    elif 'file' in urls[code]:
                        return redirect(url_for('static', filename='user_files/' + urls[code]['file']))
        except json.JSONDecodeError:
            abort(500, description="Error reading URL data.")
    return abort(404)

@app.errorhandler(404)
def page_not_found(error):
    return render_template('page_not_found.html'), 404

@app.route('/api')
def session_api():
    return jsonify(list(session.keys()))

if __name__ == "__main__":
    app.run(debug=True)
