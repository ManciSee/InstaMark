from core import app, photos, watermarks, UploadForm
from flask import render_template, url_for, redirect, flash, request
from flask_wtf import FlaskForm
from wtforms import SelectField, IntegerField, SubmitField
from wtforms.validators import NumberRange
from PIL import Image
import os

class VisibleWatermarkSettingsForm(FlaskForm):
    position = SelectField('Position', choices=[
        ('top-left', 'Top Left'),
        ('top-right', 'Top Right'),
        ('bottom-left', 'Bottom Left'),
        ('bottom-right', 'Bottom Right'),
        ('center', 'Center')
    ])
    size = IntegerField('Size (%)', default=33, 
                       validators=[NumberRange(min=1, max=100)])
    opacity = IntegerField('Opacity (%)', default=100,
                          validators=[NumberRange(min=1, max=100)])
    apply = SubmitField('Apply Watermark')

def apply_visible_watermark(image_path, watermark_path, position='bottom-right', size=33, opacity=100):
    with Image.open(image_path) as img:
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
            
        with Image.open(watermark_path) as watermark:
            if watermark.mode != 'RGBA':
                watermark = watermark.convert('RGBA')

            # Calculate watermark size
            img_width, img_height = img.size
            w_width = int(img_width * size / 100)
            w_height = int(w_width * watermark.size[1] / watermark.size[0])
            watermark = watermark.resize((w_width, w_height), Image.Resampling.LANCZOS)

            # Apply opacity
            if opacity < 100:
                watermark.putalpha(Image.eval(watermark.getchannel('A'), 
                                            lambda x: int(x * opacity / 100)))

            # Calculate position
            if position == 'top-left':
                pos = (0, 0)
            elif position == 'top-right':
                pos = (img_width - w_width - 0, 0)
            elif position == 'bottom-left':
                pos = (0, img_height - w_height - 0)
            elif position == 'bottom-right':
                pos = (img_width - w_width - 0, img_height - w_height - 0)
            else:  # center
                pos = ((img_width - w_width) // 2, (img_height - w_height) // 2)

            # Apply watermark
            transparent = Image.new('RGBA', img.size, (0, 0, 0, 0))
            transparent.paste(watermark, pos, watermark)
            watermarked = Image.alpha_composite(img, transparent)
            watermarked = watermarked.convert('RGB')

            # Save processed image
            output_filename = f"visible_watermarked_{os.path.basename(image_path)}"
            output_path = os.path.join(app.config['PROCESSED_IMAGES_DEST'], 
                                     output_filename)
            watermarked.save(output_path, 'JPEG', quality=95)

            return output_filename

@app.route('/visible', methods=['GET', 'POST'])
def visible_watermark():
    form = UploadForm()
    settings_form = VisibleWatermarkSettingsForm()
    
    # Get existing files from URL parameters
    photo_filename = request.args.get('keep_image')
    watermark_filename = request.args.get('keep_watermark')
    processed_filename = request.args.get('processed_filename')
    
    # Initialize URLs
    photo_url = url_for('uploaded_image', filename=photo_filename) if photo_filename else None
    watermark_url = url_for('uploaded_watermark', filename=watermark_filename) if watermark_filename else None
    processed_url = url_for('processed_image', filename=processed_filename) if processed_filename else None

    if request.method == 'POST':
        if form.photo.data:
            photo_filename = photos.save(form.photo.data)
            photo_url = url_for('uploaded_image', filename=photo_filename)
            
        if form.watermark.data:
            watermark_filename = watermarks.save(form.watermark.data)
            watermark_url = url_for('uploaded_watermark', filename=watermark_filename)

    return render_template('visible.html',
                         form=form,
                         settings_form=settings_form,
                         photo_url=photo_url,
                         watermark_url=watermark_url,
                         photo_filename=photo_filename,
                         watermark_filename=watermark_filename,
                         processed_url=processed_url)

@app.route('/process_visible_watermark/<image_filename>/<watermark_filename>', methods=['POST'])
def process_visible_watermark(image_filename, watermark_filename):
    settings_form = VisibleWatermarkSettingsForm()
    
    if settings_form.validate_on_submit():
        try:
            image_path = os.path.join(app.config['UPLOADED_PHOTOS_DEST'], 
                                    image_filename)
            watermark_path = os.path.join(app.config['UPLOADED_WATERMARKS_DEST'], 
                                        watermark_filename)
            
            processed_filename = apply_visible_watermark(
                image_path,
                watermark_path,
                position=settings_form.position.data,
                size=settings_form.size.data,
                opacity=settings_form.opacity.data
            )
            
            flash('Watermark applied successfully!', 'success')
            return redirect(url_for('visible_watermark',
                                  keep_image=image_filename,
                                  keep_watermark=watermark_filename,
                                  processed_filename=processed_filename))
        except Exception as e:
            flash(f'Error processing watermark: {str(e)}', 'danger')
    
    return redirect(url_for('visible_watermark',
                          keep_image=image_filename,
                          keep_watermark=watermark_filename))