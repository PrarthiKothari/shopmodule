from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from .models import Product, Category, ProductImage, ProductURL

class RegisterForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "Enter your email address"}),
        help_text="Required. Used for login and communication."
    )
    first_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "First Name (optional)"})
    )
    last_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Last Name (optional)"})
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email address already exists.")
        return email

class MultipleFileInput(forms.FileInput):
    allow_multiple_selected = True

class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput(attrs={"class": "form-control", "accept": "image/*"}))
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data if d]
        elif data:
            result = [single_file_clean(data, initial)]
        else:
            result = []
        return result

class ProductForm(forms.ModelForm):
    images = MultipleFileField(
        required=False,
        help_text="Select one or more product images to upload."
    )

    urls = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            "rows": 3,
            "class": "form-control",
            "placeholder": "Enter product/reference URLs (one per line or separated by commas)\ne.g. https://example.com/product\nhttps://partner.com/info"
        }),
        help_text="Add external links or documentation URLs for this product."
    )

    delivery_time = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            "class": "form-control bg-light",
            "readonly": "readonly",
            "id": "id_delivery_time",
            "placeholder": "Auto-filled based on delivery type"
        }),
        help_text="Automatically determined based on delivery type (non-editable)."
    )

    class Meta:
        model = Product
        fields = [
            'name',
            'category',
            'description',
            'base_price',
            'gst',
            'other_taxes',
            'delivery_type',
            'delivery_time',
            'delivery_charges',
            'other_information',
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter product name"}),
            "category": forms.Select(attrs={"class": "form-select"}),
            "description": forms.Textarea(attrs={"rows": 4, "class": "form-control", "placeholder": "Detailed product description"}),
            "base_price": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "min": "0", "placeholder": "0.00"}),
            "gst": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "min": "0", "max": "18", "placeholder": "e.g. 18.00"}),
            "other_taxes": forms.Textarea(attrs={"rows": 2, "class": "form-control", "placeholder": "Details of any other taxes (Cess, surcharge, etc.)"}),
            "delivery_type": forms.Select(attrs={"class": "form-select", "id": "id_delivery_type"}),
            "delivery_time": forms.TextInput(attrs={"class": "form-control bg-light", "readonly": "readonly", "id": "id_delivery_time", "placeholder": "Auto-filled based on delivery type"}),
            "delivery_charges": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "min": "0", "max": "100", "id": "id_delivery_charges", "placeholder": "0.00"}),
            "other_information": forms.Textarea(attrs={"rows": 3, "class": "form-control", "placeholder": "Any other relevant product specifications or details"}),
        }

    def clean(self):
        cleaned_data = super().clean()
        delivery_type = cleaned_data.get('delivery_type')
        if delivery_type in Product.DELIVERY_TIME_MAP:
            cleaned_data['delivery_time'] = Product.DELIVERY_TIME_MAP[delivery_type]
        elif not cleaned_data.get('delivery_time'):
            cleaned_data['delivery_time'] = Product.DELIVERY_TIME_MAP.get('STANDARD', "3-5 Business Days")

        if delivery_type == Product.DeliveryType.PICKUP:
            cleaned_data['delivery_charges'] = 0
        return cleaned_data

    def clean_base_price(self):
        price = self.cleaned_data.get('base_price')
        if price is not None and price < 0:
            raise forms.ValidationError("Base price cannot be negative.")
        return price

    def clean_gst(self):
        gst = self.cleaned_data.get('gst')
        if gst is not None:
            if gst < 0:
                raise forms.ValidationError("GST cannot be negative.")
            if gst > 18:
                raise forms.ValidationError("GST cannot be more than 18%.")
        return gst

    def clean_delivery_charges(self):
        delivery_type = self.cleaned_data.get('delivery_type') or self.data.get('delivery_type')
        if delivery_type == Product.DeliveryType.PICKUP:
            return 0

        charges = self.cleaned_data.get('delivery_charges')
        if charges is not None:
            if charges < 0:
                raise forms.ValidationError("Delivery charges cannot be negative.")
            if charges > 100:
                raise forms.ValidationError("Delivery charges cannot be more than 100.")
        return charges

    def clean_urls(self):
        urls_raw = self.cleaned_data.get('urls', '')
        if not urls_raw:
            return ""

        url_validator = URLValidator()
        valid_urls = []
        for line in urls_raw.replace(",", "\n").splitlines():
            clean_url = line.strip()
            if clean_url:
                if not (clean_url.startswith("http://") or clean_url.startswith("https://")):
                    clean_url = "https://" + clean_url
                try:
                    url_validator(clean_url)
                    valid_urls.append(clean_url)
                except ValidationError:
                    raise forms.ValidationError(f"Invalid URL entered: '{clean_url}'. Please enter a valid URL.")

        return "\n".join(valid_urls)