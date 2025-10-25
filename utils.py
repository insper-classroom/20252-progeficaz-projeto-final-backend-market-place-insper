from flask_jwt_extended import (
    JWTManager)
from flask_bcrypt import Bcrypt

# JWT E BCRYPT SETUP
jwt = JWTManager()
bcrypt = Bcrypt()


def init_app(app):
    jwt.init_app(app)
    bcrypt.init_app(app)
    return app


# CLOUDINARY SETUP
import cloudinary
import cloudinary.uploader
import os
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True
)

def upload_image(file_path):
    """
    Faz upload de uma imagem para o Cloudinary
    recebe-> arquivo;
    retorna -> URL.
    """
    try:
        result = cloudinary.uploader.upload(
            file_path,
            folder="marketplace",
            transformation=[
                {'width': 1200, 'height': 1200, 'crop': 'limit'},  # reduz tamanho
                {'quality': 'auto:low'},  # compressão
                {'fetch_format': 'auto'}  # converte para webp
            ],
            resource_type="auto"
        )
        return result['secure_url']
    except Exception as e:
        print(f"Erro no upload da imagem: {e}")
        return None
    

def upload_multiple_images(files):
    """
    recebe -> lista ou dicionário de arquivos
    retorna -> lista de URLs das imagens
    """
    uploaded_urls = []
    
    for file in files:
        url = upload_image(file)
        if url:
            uploaded_urls.append(url)
    
    return uploaded_urls
 
def delete_image(image_url):
    """
    Deleta imagem do Cloudinary
    recebe -> URL da imagem 
    retorna -> True se deletou
    """
    try:
        parts = image_url.split('/') # pega o public_id da URL
        print(parts)
        upload_index = parts.index('upload') # acha o índice de 'upload'
        # pega tudo depois de upload, remove versão e extensão
        public_id_parts = parts[upload_index + 2:]  # pula 'upload' e versão
        public_id = '/'.join(public_id_parts).split('.')[0]
        
        result = cloudinary.uploader.destroy(public_id) # deleta a image
        return result.get('result') == 'ok'
    except Exception as e:
        print(f"Erro ao deletar imagem: {e}")
        return False
