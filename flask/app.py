from flask import Flask, render_template, send_from_directory, url_for, redirect, request, flash
from flask_uploads import UploadSet, IMAGES, configure_uploads
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import SubmitField
from dotenv import load_dotenv
from PIL import Image
import os

load_dotenv()

app = Flask(__name__)

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['UPLOADED_PHOTOS_DEST'] = 'uploads/images'
app.config['UPLOADED_WATERMARKS_DEST'] = 'uploads/watermarks'
app.config['PROCESSED_IMAGES_DEST'] = 'uploads/processed'  # Add this line

os.makedirs(app.config['UPLOADED_PHOTOS_DEST'], exist_ok=True)
os.makedirs(app.config['UPLOADED_WATERMARKS_DEST'], exist_ok=True)
os.makedirs(app.config['PROCESSED_IMAGES_DEST'], exist_ok=True)

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

@app.route('/uploads/processed/<filename>')
def get_processed_image(filename):
    return send_from_directory(app.config['PROCESSED_IMAGES_DEST'], filename)

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

def apply_watermark(image_path, watermark_path):
    # Open the main image
    with Image.open(image_path) as img:
        if img.mode != 'RGBA':
            img = img.convert('RGBA')

        # Open the watermark image
        with Image.open(watermark_path) as watermark:
            if watermark.mode != 'RGBA':
                watermark = watermark.convert('RGBA')

            # Calculate watermark size (1/3 of the main image width)
            img_width, img_height = img.size
            w_width = int(img_width / 3)
            w_height = int(w_width * watermark.size[1] / watermark.size[0])
            watermark = watermark.resize((w_width, w_height), Image.Resampling.LANCZOS)

            # Create a transparent layer
            transparent = Image.new('RGBA', img.size, (0, 0, 0, 0))

            # Position watermark in bottom-right corner
            position = (img_width - w_width - 10, img_height - w_height - 10)

            # Paste watermark onto transparent layer
            transparent.paste(watermark, position, watermark)

            # Combine images
            watermarked = Image.alpha_composite(img, transparent)
            watermarked = watermarked.convert('RGB')

            # Save processed image
            output_filename = f"watermarked_{os.path.basename(image_path)}"
            output_path = os.path.join(app.config['PROCESSED_IMAGES_DEST'], output_filename)
            watermarked.save(output_path, 'JPEG', quality=95)

            return output_filename

@app.route('/process_watermark/<image_filename>/<watermark_filename>')
def process_watermark(image_filename, watermark_filename):
    try:
        image_path = os.path.join(app.config['UPLOADED_PHOTOS_DEST'], image_filename)
        watermark_path = os.path.join(app.config['UPLOADED_WATERMARKS_DEST'], watermark_filename)
        
        processed_filename = apply_watermark(image_path, watermark_path)
        
        flash('Watermark applied successfully!', 'success')
        return redirect(url_for('upload_image', 
                              keep_image=image_filename,
                              keep_watermark=watermark_filename,
                              processed_filename=processed_filename))
    except Exception as e:
        flash(f'Error processing watermark: {str(e)}', 'danger')
        return redirect(url_for('upload_image'))

@app.route('/', methods=['GET', 'POST'])
def upload_image():
    form = UploadForm()
    photo_url = None
    watermark_url = None
    photo_filename = None
    watermark_filename = None
    processed_url = None
    
    if request.args.get('processed_filename'):
        processed_url = url_for('get_processed_image', 
                              filename=request.args.get('processed_filename'))

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
                         watermark_filename=watermark_filename,
                         processed_url=processed_url)

if __name__ == '__main__':
    app.run(debug=True)