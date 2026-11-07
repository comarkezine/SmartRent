from django import forms
from .models import Property


class PropertyForm(forms.ModelForm):

    class Meta:
        model = Property

        fields = [
            "name",
            "location",
            "units",
            "property_manager",
            "status",
        ]

        widgets = {
            "name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter property name"
            }),

            "location": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter property location"
            }),

            "units": forms.NumberInput(attrs={
                "class": "form-control",
                "min": "1"
            }),

            "property_manager": forms.Select(attrs={
                "class": "form-select"
            }),

            "status": forms.Select(attrs={
                "class": "form-select"
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Only users assigned to the Property Manager group
        # should appear in the dropdown.
        from django.contrib.auth import get_user_model

        User = get_user_model()

        self.fields["property_manager"].queryset = User.objects.filter(
            groups__name="Property Manager",
            is_active=True
        ).distinct()