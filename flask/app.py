from flask import Flask
from core import app, photos, watermarks, UploadForm
import routes.visible_watermark
import routes.invisible_watermark

app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limite di 16MB per upload


@app.errorhandler(413)
def too_large(e):
    return "File is too large", 413

@app.errorhandler(404)
def not_found(e):
    return "Page not found", 404


if __name__ == '__main__':
    app.run(debug=True)