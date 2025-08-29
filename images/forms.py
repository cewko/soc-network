import requests
from django.core.files.base import ContentFile
from django.utils.text import slugify
from django import forms
from PIL import Image as PILImage
from io import BytesIO
from .models import Image

class ImageCreateForm(forms.ModelForm):
    class Meta:
        model = Image
        fields = ["title", "url", "description"]
        widgets = {
            "url": forms.HiddenInput,
        }

    def clean_url(self):
        url = self.cleaned_data["url"]
        valid_extensions = ["jpg", "jpeg", "png"]
        extension = url.rsplit(".", 1)[1].lower()
        if extension not in valid_extensions:
            raise forms.ValidationError(
                "The given URL does not match valid image extensions."
            )
        return url

    def save(self, force_insert=False, force_update=False, commit=True):
        image = super().save(commit=False)
        image_url = self.cleaned_data["url"]
        name = slugify(image.title)
        extension = image_url.rsplit(".", 1)[1].lower()
        image_name = f"{name}.{extension}"
        
        # Download image from the given URL
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        try:
            response = requests.get(image_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Verify content type
            content_type = response.headers.get('content-type', '')
            if not content_type.startswith('image/'):
                raise forms.ValidationError(f"URL does not point to an image. Content-Type: {content_type}")
            
            # Validate that the content is actually an image
            pil_image = PILImage.open(BytesIO(response.content))
            pil_image.verify()
            
            image.image.save(
                image_name,
                ContentFile(response.content),
                save=False
            )
            
        except requests.RequestException as e:
            raise forms.ValidationError(f"Error downloading image: {e}")
        except Exception as e:
            raise forms.ValidationError(f"Error processing image: {e}")
        
        if commit:
            image.save()
        return image