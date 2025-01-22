from flask import Flask, send_from_directory, url_for, redirect, request, flash, render_template
from flask_uploads import UploadSet, IMAGES, configure_uploads
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import SubmitField
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['UPLOADED_PHOTOS_DEST'] = '../uploads/images'
app.config['UPLOADED_WATERMARKS_DEST'] = '../uploads/watermarks'
app.config['PROCESSED_IMAGES_DEST'] = '../uploads/processed'

# Create directories if they don't exist
for directory in [app.config['UPLOADED_PHOTOS_DEST'], 
                 app.config['UPLOADED_WATERMARKS_DEST'],
                 app.config['PROCESSED_IMAGES_DEST']]:
    os.makedirs(directory, exist_ok=True)

# Configure upload sets
photos = UploadSet('photos', IMAGES)
watermarks = UploadSet('watermarks', IMAGES)
configure_uploads(app, (photos, watermarks))

class UploadForm(FlaskForm):
    photo = FileField(validators=[FileAllowed(photos, 'Image only!')])
    watermark = FileField(validators=[FileAllowed(watermarks, 'Image only!')])
    submit = SubmitField('Upload')

# File serving routes
@app.route('/uploads/images/<filename>')
def uploaded_image(filename):
    return send_from_directory(app.config['UPLOADED_PHOTOS_DEST'], filename)

@app.route('/uploads/watermarks/<filename>')
def uploaded_watermark(filename):
    return send_from_directory(app.config['UPLOADED_WATERMARKS_DEST'], filename)

@app.route('/uploads/processed/<filename>')
def processed_image(filename):
    return send_from_directory(app.config['PROCESSED_IMAGES_DEST'], filename)

# File deletion routes
@app.route('/delete/images/<filename>', methods=['POST'])
def delete_image_file(filename):
    file_path = os.path.join(app.config['UPLOADED_PHOTOS_DEST'], filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        flash('Image deleted successfully!', 'success')
    else:
        flash('Image not found!', 'danger')
    return_route = request.args.get('return_route', 'visible_watermark')
    return redirect(url_for(return_route, keep_watermark=request.args.get('watermark_filename')))

@app.route('/delete/watermarks/<filename>', methods=['POST'])
def delete_watermark_file(filename):
    file_path = os.path.join(app.config['UPLOADED_WATERMARKS_DEST'], filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        flash('Watermark deleted successfully!', 'success')
    else:
        flash('Watermark not found!', 'danger')
    return_route = request.args.get('return_route', 'visible_watermark')
    return redirect(url_for(return_route, keep_image=request.args.get('photo_filename')))

@app.route('/')
def home():
    return render_template('home.html')