# from flask import Flask, render_template, send_from_directory, url_for, redirect, request, flash
# from flask_uploads import UploadSet, IMAGES, configure_uploads
# from flask_wtf import FlaskForm
# from flask_wtf.file import FileField, FileAllowed, FileRequired
# from wtforms import SubmitField, SelectField, IntegerField, StringField
# from wtforms.validators import NumberRange, DataRequired
# from dotenv import load_dotenv
# from PIL import Image
# import os

# load_dotenv()

# app = Flask(__name__)

# app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
# app.config['UPLOADED_PHOTOS_DEST'] = '../uploads/images'
# app.config['UPLOADED_WATERMARKS_DEST'] = '../uploads/watermarks'
# app.config['PROCESSED_IMAGES_DEST'] = '../uploads/processed'

# os.makedirs(app.config['UPLOADED_PHOTOS_DEST'], exist_ok=True)
# os.makedirs(app.config['UPLOADED_WATERMARKS_DEST'], exist_ok=True)
# os.makedirs(app.config['PROCESSED_IMAGES_DEST'], exist_ok=True)

# photos = UploadSet('photos', IMAGES)
# watermarks = UploadSet('watermarks', IMAGES)

# configure_uploads(app, (photos, watermarks))  

# class UploadForm(FlaskForm):
#     photo = FileField(validators=[FileAllowed(photos, 'Image only!')])
#     watermark = FileField(validators=[FileAllowed(watermarks, 'Image only!')])
#     submit = SubmitField('Upload')

# class WatermarkSettingsForm(FlaskForm):
#     position = SelectField('Position', choices=[
#         ('top-left', 'Top Left'),
#         ('top-right', 'Top Right'),
#         ('bottom-left', 'Bottom Left'),
#         ('bottom-right', 'Bottom Right'),
#         ('center', 'Center')
#     ])
#     size = IntegerField('Size (%)', default=33, 
#                        validators=[NumberRange(min=1, max=100)])
#     opacity = IntegerField('Opacity (%)', default=100,
#                           validators=[NumberRange(min=1, max=100)])
#     apply = SubmitField('Apply Watermark')

# # File serving routes
# @app.route('/uploads/images/<filename>')
# def uploaded_image(filename):
#     return send_from_directory(app.config['UPLOADED_PHOTOS_DEST'], filename)

# @app.route('/uploads/watermarks/<filename>')
# def uploaded_watermark(filename):
#     return send_from_directory(app.config['UPLOADED_WATERMARKS_DEST'], filename)

# @app.route('/uploads/processed/<filename>')
# def processed_image(filename):
#     return send_from_directory(app.config['PROCESSED_IMAGES_DEST'], filename)

# # File deletion routes
# @app.route('/delete/images/<filename>', methods=['POST'])
# def delete_image_file(filename):
#     file_path = os.path.join(app.config['UPLOADED_PHOTOS_DEST'], filename)
#     if os.path.exists(file_path):
#         os.remove(file_path)
#         flash('Image deleted successfully!', 'success')
#     else:
#         flash('Image not found!', 'danger')
#     return redirect(url_for('upload_image', keep_watermark=request.args.get('watermark_filename')))

# @app.route('/delete/watermarks/<filename>', methods=['POST'])
# def delete_watermark_file(filename):
#     file_path = os.path.join(app.config['UPLOADED_WATERMARKS_DEST'], filename)
#     if os.path.exists(file_path):
#         os.remove(file_path)
#         flash('Watermark deleted successfully!', 'success')
#     else:
#         flash('Watermark not found!', 'danger')
#     return redirect(url_for('upload_image', keep_image=request.args.get('photo_filename')))

# def apply_watermark(image_path, watermark_path, position='bottom-right', size=33, opacity=100):
#     with Image.open(image_path) as img:
#         if img.mode != 'RGBA':
#             img = img.convert('RGBA')

#         with Image.open(watermark_path) as watermark:
#             if watermark.mode != 'RGBA':
#                 watermark = watermark.convert('RGBA')

#             img_width, img_height = img.size
#             w_width = int(img_width * size / 100)
#             w_height = int(w_width * watermark.size[1] / watermark.size[0])
#             watermark = watermark.resize((w_width, w_height), Image.Resampling.LANCZOS)

#             if opacity < 100:
#                 watermark.putalpha(Image.eval(watermark.getchannel('A'), lambda x: int(x * opacity / 100)))

#             if position == 'top-left':
#                 pos = (0, 0)
#             elif position == 'top-right':
#                 pos = (img_width - w_width - 0, 0)
#             elif position == 'bottom-left':
#                 pos = (0, img_height - w_height - 0)
#             elif position == 'bottom-right':
#                 pos = (img_width - w_width - 0, img_height - w_height - 0)
#             else:  
#                 pos = ((img_width - w_width) // 2, (img_height - w_height) // 2)

#             transparent = Image.new('RGBA', img.size, (0, 0, 0, 0))
#             transparent.paste(watermark, pos, watermark)
#             watermarked = Image.alpha_composite(img, transparent)
#             watermarked = watermarked.convert('RGB')

#             output_filename = f"watermarked_{os.path.basename(image_path)}"
#             output_path = os.path.join(app.config['PROCESSED_IMAGES_DEST'], output_filename)
#             watermarked.save(output_path, 'JPEG', quality=95)

#             return output_filename

# # Visible watermarking route
# @app.route('/process_watermark/<image_filename>/<watermark_filename>', methods=['POST'])
# def process_watermark(image_filename, watermark_filename):
#     settings_form = WatermarkSettingsForm()
    
#     if settings_form.validate_on_submit():
#         try:
#             image_path = os.path.join(app.config['UPLOADED_PHOTOS_DEST'], image_filename)
#             watermark_path = os.path.join(app.config['UPLOADED_WATERMARKS_DEST'], watermark_filename)
            
#             processed_filename = apply_watermark(
#                 image_path, 
#                 watermark_path,
#                 position=settings_form.position.data,
#                 size=settings_form.size.data,
#                 opacity=settings_form.opacity.data
#             )
            
#             flash('Watermark applied successfully!', 'success')
#             return redirect(url_for('upload_image', 
#                                   keep_image=image_filename,
#                                   keep_watermark=watermark_filename,
#                                   processed_filename=processed_filename))
#         except Exception as e:
#             flash(f'Error processing watermark: {str(e)}', 'danger')
#     else:
#         for field, errors in settings_form.errors.items():
#             for error in errors:
#                 flash(f'{field}: {error}', 'danger')
    
#     return redirect(url_for('upload_image', 
#                           keep_image=image_filename,
#                           keep_watermark=watermark_filename))
# @app.route('/')
# def home():
#     return render_template('home.html')

# @app.route('/visible', methods=['GET', 'POST'])
# def upload_image():
#     form = UploadForm()
#     settings_form = WatermarkSettingsForm()
#     photo_url = None
#     watermark_url = None
#     photo_filename = None
#     watermark_filename = None
#     processed_url = None
    
#     if request.args.get('processed_filename'):
#         processed_url = url_for('processed_image', 
#                               filename=request.args.get('processed_filename'))

#     if request.args.get('keep_image'):
#         photo_filename = request.args.get('keep_image')
#         photo_url = url_for('uploaded_image', filename=photo_filename)
    
#     if request.args.get('keep_watermark'):
#         watermark_filename = request.args.get('keep_watermark')
#         watermark_url = url_for('uploaded_watermark', filename=watermark_filename)

#     if request.method == 'POST':
#         if form.photo.data:
#             photo_filename = photos.save(form.photo.data)
#             photo_url = url_for('uploaded_image', filename=photo_filename)
#         elif request.args.get('keep_image'):
#             photo_filename = request.args.get('keep_image')
#             photo_url = url_for('uploaded_image', filename=photo_filename)

#         if form.watermark.data:
#             watermark_filename = watermarks.save(form.watermark.data)
#             watermark_url = url_for('uploaded_watermark', filename=watermark_filename)
#         elif request.args.get('keep_watermark'):
#             watermark_filename = request.args.get('keep_watermark')
#             watermark_url = url_for('uploaded_watermark', filename=watermark_filename)

#     return render_template('visible.html', 
#                          form=form,
#                          settings_form=settings_form,
#                          photo_url=photo_url, 
#                          watermark_url=watermark_url, 
#                          photo_filename=photo_filename, 
#                          watermark_filename=watermark_filename,
#                          processed_url=processed_url)

# if __name__ == '__main__':
#     app.run(debug=True)



from flask import Flask
from core import app, photos, watermarks, UploadForm
import routes.visible_watermark
import routes.invisible_watermark

# Registra i blueprints se necessario
#app.register_blueprint(visible_watermark.bp)
#app.register_blueprint(invisible_watermark.bp)

# Configurazione aggiuntiva dell'applicazione se necessaria
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limite di 16MB per upload

# Gestione errori personalizzata
@app.errorhandler(413)
def too_large(e):
    return "File is too large", 413

@app.errorhandler(404)
def not_found(e):
    return "Page not found", 404

# Esegui l'applicazione
if __name__ == '__main__':
    app.run(debug=True)