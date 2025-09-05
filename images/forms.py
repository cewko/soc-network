import requests
from django.core.files.base import ContentFile
from django.utils.text import slugify
from django import forms
from PIL import Image as PILImage
from io import BytesIO
from .models import Image


class ImageDownloadService:
    VALID_EXTENSIONS = ['jpg', 'jpeg', 'png']
    REQUEST_TIMEOUT = 30
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    @classmethod
    def download_and_validate(cls, url):
        try:
            response = requests.get(url, headers=cls.HEADERS, timeout=cls.REQUEST_TIMEOUT)
            response.raise_for_status()
            
            content_type = response.headers.get('content-type', '')
            if not content_type.startswith('image/'):
                raise ValueError(f"URL does not point to an image. Content-Type: {content_type}")
            
            pil_image = PILImage.open(BytesIO(response.content))
            pil_image.verify()
            
            return response.content
        except requests.RequestException as e:
            raise ValueError(f"Error downloading image: {e}")
        except Exception as e:
            raise ValueError(f"Error processing image: {e}")
    
    @classmethod
    def validate_url_extension(cls, url):
        try:
            extension = url.rsplit(".", 1)[1].lower()
            return extension in cls.VALID_EXTENSIONS
        except IndexError:
            return False
    
    @classmethod
    def generate_filename(cls, title, url):
        name = slugify(title)
        extension = url.rsplit(".", 1)[1].lower()
        return f"{name}.{extension}"


class ImageCreateForm(forms.ModelForm):
    class Meta:
        model = Image
        fields = ["title", "url", "description"]
        widgets = {
            "url": forms.HiddenInput,
        }

    def clean_url(self):
        url = self.cleaned_data["url"]
        if not ImageDownloadService.validate_url_extension(url):
            raise forms.ValidationError(
                "The given URL does not match valid image extensions."
            )
        return url

    def save(self, commit=True):
        image = super().save(commit=False)
        image_url = self.cleaned_data["url"]
        
        try:
            image_content = ImageDownloadService.download_and_validate(image_url)
            image_name = ImageDownloadService.generate_filename(image.title, image_url)
            
            image.image.save(
                image_name,
                ContentFile(image_content),
                save=False
            )
        except ValueError as e:
            raise forms.ValidationError(str(e))
        
        if commit:
            image.save()
        return image