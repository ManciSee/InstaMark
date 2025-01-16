from flask import Flask, render_template, send_from_directory, url_for, redirect, request, flash
from flask_uploads import UploadSet, IMAGES, configure_uploads
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import SubmitField
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['UPLOADED_PHOTOS_DEST'] = 'uploads/images'
app.config['UPLOADED_WATERMARKS_DEST'] = 'uploads/watermarks'

photos = UploadSet('photos', IMAGES)
watermarks = UploadSet('watermarks', IMAGES)

configure_uploads(app, photos)
configure_uploads(app, watermarks)

class UploadForm(FlaskForm):
    photo = FileField(validators=[FileAllowed(photos, 'Image only!')])
    watermark = FileField(validators=[FileAllowed(watermarks, 'Image only!')])
    submit = SubmitField('Upload')

@app.route('/uploads/images/<filename>')
def get_image_file(filename):
    return send_from_directory(app.config['UPLOADED_PHOTOS_DEST'], filename)

@app.route('/uploads/watermarks/<filename>')
def get_watermark_file(filename):
    return send_from_directory(app.config['UPLOADED_WATERMARKS_DEST'], filename)

@app.route('/delete/images/<filename>', methods=['POST'])
def delete_image_file(filename):
    file_path = os.path.join(app.config['UPLOADED_PHOTOS_DEST'], filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        flash('Image deleted successfully!', 'success')
    else:
        flash('Image not found!', 'danger')
    return redirect(url_for('upload_image', keep_watermark=request.args.get('watermark_filename')))

@app.route('/delete/watermarks/<filename>', methods=['POST'])
def delete_watermark_file(filename):
    file_path = os.path.join(app.config['UPLOADED_WATERMARKS_DEST'], filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        flash('Watermark deleted successfully!', 'success')
    else:
        flash('Watermark not found!', 'danger')
    return redirect(url_for('upload_image', keep_image=request.args.get('photo_filename')))

@app.route('/', methods=['GET', 'POST'])
def upload_image():
    form = UploadForm()
    photo_url = None
    watermark_url = None
    photo_filename = None
    watermark_filename = None

    if request.args.get('keep_image'):
        photo_filename = request.args.get('keep_image')
        photo_url = url_for('get_image_file', filename=photo_filename)
    
    if request.args.get('keep_watermark'):
        watermark_filename = request.args.get('keep_watermark')
        watermark_url = url_for('get_watermark_file', filename=watermark_filename)

    if request.method == 'POST':
        if form.photo.data:
            photo_filename = photos.save(form.photo.data)
            photo_url = url_for('get_image_file', filename=photo_filename)
        elif request.args.get('keep_image'):
            photo_filename = request.args.get('keep_image')
            photo_url = url_for('get_image_file', filename=photo_filename)

        if form.watermark.data:
            watermark_filename = watermarks.save(form.watermark.data)
            watermark_url = url_for('get_watermark_file', filename=watermark_filename)
        elif request.args.get('keep_watermark'):
            watermark_filename = request.args.get('keep_watermark')
            watermark_url = url_for('get_watermark_file', filename=watermark_filename)

    return render_template('index.html', 
                         form=form, 
                         photo_url=photo_url, 
                         watermark_url=watermark_url, 
                         photo_filename=photo_filename, 
                         watermark_filename=watermark_filename)

if __name__ == '__main__':
    app.run(debug=True)