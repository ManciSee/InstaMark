from core import app, photos, watermarks, UploadForm
from flask import render_template, url_for, redirect, flash, request
from flask_wtf import FlaskForm
from wtforms import SubmitField
from PIL import Image
import numpy as np
import os

class InvisibleWatermarkSettingsForm(FlaskForm):
    apply = SubmitField('Apply Steganography')
    extract = SubmitField('Extract Hidden Secret')

def apply_invisible_watermark(cover_image_path, watermark_image_path):
    """Apply LSB steganography to hide watermark image in cover image"""
    try:
        with Image.open(cover_image_path) as cover_img, Image.open(watermark_image_path) as watermark_img:
            cover_img = cover_img.convert('RGB')
            watermark_img = watermark_img.convert('RGB')
            
            watermark_img = watermark_img.resize(cover_img.size, Image.LANCZOS)
            
            cover_array = np.array(cover_img)
            watermark_array = np.array(watermark_img)

            output_array = cover_array.copy()
            output_array = output_array & 0xFE  

            watermark_bits = (watermark_array >> 7) & 1
            output_array = output_array | watermark_bits

            output_filename = f"stego_{os.path.basename(cover_image_path)}"
            output_path = os.path.join(app.config['PROCESSED_IMAGES_DEST'], output_filename)
            Image.fromarray(output_array).save(output_path, 'PNG')
            
            return output_filename
    except Exception as e:
        raise Exception(f"Error in apply_invisible_watermark: {str(e)}")

def extract_watermark(stego_image_path):
    """Extract hidden watermark from steganographic image"""
    try:
        with Image.open(stego_image_path) as stego_img:
            stego_img = stego_img.convert('RGB')
            stego_array = np.array(stego_img)
            
            extracted_bits = stego_array & 1
            extracted_array = extracted_bits * 255
            
            output_filename = f"extracted_{os.path.basename(stego_image_path)}"
            output_path = os.path.join(app.config['PROCESSED_IMAGES_DEST'], output_filename)
            Image.fromarray(extracted_array.astype(np.uint8)).save(output_path, 'PNG')
            
            return output_filename
    except Exception as e:
        raise Exception(f"Error in extract_watermark: {str(e)}")

@app.route('/invisible', methods=['GET', 'POST'])
def invisible_watermark():
    form = UploadForm()
    stego_form = InvisibleWatermarkSettingsForm()
    
    photo_filename = request.args.get('photo_filename')
    watermark_filename = request.args.get('watermark_filename')
    processed_filename = request.args.get('processed_filename')
    extracted_filename = request.args.get('extracted_filename')

    if form.validate_on_submit() and (form.photo.data or form.watermark.data):
        if form.photo.data:
            photo_filename = photos.save(form.photo.data)
        if form.watermark.data:
            watermark_filename = watermarks.save(form.watermark.data)
        return redirect(url_for('invisible_watermark', 
                              photo_filename=photo_filename,
                              watermark_filename=watermark_filename))

    if request.method == 'POST':
        if stego_form.apply.data and photo_filename and watermark_filename:
            try:
                cover_path = os.path.join(app.config['UPLOADED_PHOTOS_DEST'], photo_filename)
                watermark_path = os.path.join(app.config['UPLOADED_WATERMARKS_DEST'], watermark_filename)
                
                processed_filename = apply_invisible_watermark(cover_path, watermark_path)
                flash('Steganography applied successfully!', 'success')
                
                return redirect(url_for('invisible_watermark',
                                      photo_filename=photo_filename,
                                      watermark_filename=watermark_filename,
                                      processed_filename=processed_filename))
                
            except Exception as e:
                flash(f'Error applying steganography: {str(e)}', 'danger')
        
        elif stego_form.extract.data and processed_filename:
            try:
                stego_path = os.path.join(app.config['PROCESSED_IMAGES_DEST'], processed_filename)
                extracted_filename = extract_watermark(stego_path)
                flash('Watermark extracted successfully!', 'success')
                
                return redirect(url_for('invisible_watermark',
                                      photo_filename=photo_filename,
                                      watermark_filename=watermark_filename,
                                      processed_filename=processed_filename,
                                      extracted_filename=extracted_filename))
                
            except Exception as e:
                flash(f'Error extracting watermark: {str(e)}', 'danger')

    photo_url = url_for('uploaded_image', filename=photo_filename) if photo_filename else None
    watermark_url = url_for('uploaded_watermark', filename=watermark_filename) if watermark_filename else None
    processed_url = url_for('processed_image', filename=processed_filename) if processed_filename else None
    extracted_url = url_for('processed_image', filename=extracted_filename) if extracted_filename else None

    return render_template('invisible.html',
                         form=form,
                         stego_form=stego_form,
                         photo_url=photo_url,
                         photo_filename=photo_filename,
                         watermark_url=watermark_url,
                         watermark_filename=watermark_filename,
                         processed_url=processed_url,
                         processed_filename=processed_filename,
                         extracted_url=extracted_url,
                         extracted_filename=extracted_filename)