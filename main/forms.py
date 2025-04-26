from django import forms


class UploadFileForm(forms.Form):
    file = forms.FileField(
        label="Текстовый файл (.txt, UTF-8)",
        widget=forms.ClearableFileInput(
            attrs={"class": "form-control", "accept": ".txt"}
        ),
    )
