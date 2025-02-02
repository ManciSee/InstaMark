import cv2
from core import app, photos, watermarks, UploadForm
from flask import render_template, url_for, redirect, flash, request
from flask_wtf import FlaskForm
from wtforms import SubmitField
from PIL import Image
import numpy as np
import os

class InvisibleWatermarkSettingsForm(FlaskForm):
    apply = SubmitField('Apply Steganography')
    extract = SubmitField('Extract Hidden Image')
    method = SubmitField('Method')
    lsb_method = SubmitField('LSB')
    dct_method = SubmitField('DCT')

def apply_invisible_watermark(cover_image_path, watermark_image_path, method='lsb'):
    """Apply steganography with the specified method (LSB or DCT)"""
    if method == 'lsb':
        return apply_lsb_watermark(cover_image_path, watermark_image_path)
    elif method == 'dct':
        return apply_dct_watermark(cover_image_path, watermark_image_path)

def apply_lsb_watermark(cover_image_path, watermark_image_path):
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
        raise Exception(f"Error in apply_invisible_watermark (LSB): {str(e)}")

def apply_dct_watermark(cover_image_path, watermark_image_path):
    """Apply DCT steganography to hide watermark image in cover image"""
    try:
        cover_img = cv2.imread(cover_image_path, cv2.IMREAD_GRAYSCALE)
        watermark_img = cv2.imread(watermark_image_path, cv2.IMREAD_GRAYSCALE)

        cover_img = cv2.resize(cover_img, (watermark_img.shape[1], watermark_img.shape[0]))
        
        # Apply DCT
        cover_dct = cv2.dct(np.float32(cover_img))
        watermark_dct = cv2.dct(np.float32(watermark_img))

        # Embed watermark into cover image using DCT
        watermark_dct[:10, :10] = watermark_dct[:10, :10] * 0.5 + cover_dct[:10, :10] * 0.5
        
        stego_img = cv2.idct(watermark_dct)
        
        stego_filename = f"stego_{os.path.basename(cover_image_path)}"
        stego_path = os.path.join(app.config['PROCESSED_IMAGES_DEST'], stego_filename)
        cv2.imwrite(stego_path, np.uint8(stego_img))
        
        return stego_filename
    except Exception as e:
        raise Exception(f"Error in apply_invisible_watermark (DCT): {str(e)}")

def extract_watermark(stego_image_path, method='lsb'):
    """Extract hidden watermark from steganographic image"""
    if method == 'lsb':
        return extract_lsb_watermark(stego_image_path)
    elif method == 'dct':
        return extract_dct_watermark(stego_image_path)

def extract_lsb_watermark(stego_image_path):
    """Extract watermark using LSB method"""
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
        raise Exception(f"Error in extract_watermark (LSB): {str(e)}")

def extract_dct_watermark(stego_image_path):
    """Extract watermark using DCT method"""
    try:
        stego_img = cv2.imread(stego_image_path, cv2.IMREAD_GRAYSCALE)
        stego_dct = cv2.dct(np.float32(stego_img))

        extracted_dct = stego_dct[:10, :10] * 2

        extracted_img = cv2.idct(extracted_dct)
        
        extracted_filename = f"extracted_{os.path.basename(stego_image_path)}"
        extracted_path = os.path.join(app.config['PROCESSED_IMAGES_DEST'], extracted_filename)
        cv2.imwrite(extracted_path, np.uint8(extracted_img))

        return extracted_filename
    except Exception as e:
        raise Exception(f"Error in extract_watermark (DCT): {str(e)}")

@app.route('/invisible', methods=['GET', 'POST'])
def invisible_watermark():
    form = UploadForm()
    stego_form = InvisibleWatermarkSettingsForm()
    
    photo_filename = request.args.get('photo_filename')
    watermark_filename = request.args.get('watermark_filename')
    processed_filename = request.args.get('processed_filename')
    extracted_filename = request.args.get('extracted_filename')
    method = request.args.get('method', 'lsb')

    if form.validate_on_submit() and (form.photo.data or form.watermark.data):
        if form.photo.data:
            photo_filename = photos.save(form.photo.data)
        if form.watermark.data:
            watermark_filename = watermarks.save(form.watermark.data)
        return redirect(url_for('invisible_watermark', 
                              photo_filename=photo_filename,
                              watermark_filename=watermark_filename))

    if request.method == 'POST':
        # Gestione della scelta del metodo
        if stego_form.lsb_method.data:
            method = 'lsb'
        elif stego_form.dct_method.data:
            method = 'dct'

        # Applicazione del watermark invisibile
        if stego_form.apply.data and photo_filename and watermark_filename:
            try:
                cover_path = os.path.join(app.config['UPLOADED_PHOTOS_DEST'], photo_filename)
                watermark_path = os.path.join(app.config['UPLOADED_WATERMARKS_DEST'], watermark_filename)
                
                processed_filename = apply_invisible_watermark(cover_path, watermark_path, method)
                flash('Steganography applied successfully!', 'success')
                
                return redirect(url_for('invisible_watermark',
                                      photo_filename=photo_filename,
                                      watermark_filename=watermark_filename,
                                      processed_filename=processed_filename,
                                      method=method))
                
            except Exception as e:
                flash(f'Error applying steganography: {str(e)}', 'danger')
        
        # Estrazione del watermark
        elif stego_form.extract.data and processed_filename:
            try:
                stego_path = os.path.join(app.config['PROCESSED_IMAGES_DEST'], processed_filename)
                extracted_filename = extract_watermark(stego_path, method)
                flash('Watermark extracted successfully!', 'success')
                
                return redirect(url_for('invisible_watermark',
                                      photo_filename=photo_filename,
                                      watermark_filename=watermark_filename,
                                      processed_filename=processed_filename,
                                      extracted_filename=extracted_filename,
                                      method=method))
                
            except Exception as e:
                flash(f'Error extracting watermark: {str(e)}', 'danger')

    # URL per le immagini e watermark
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
                         extracted_filename=extracted_filename,
                         method=method)