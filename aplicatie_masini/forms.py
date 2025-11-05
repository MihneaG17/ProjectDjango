from django import forms

class ContactForm(forms.Form):
    nume = forms.CharField(max_length=100, label='Nume', required=True)
    email = forms.EmailField(label='Email', required=True)
    mesaj = forms.CharField(widget=forms.Textarea, label='Mesaj', required=True)
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email.endswith('@domeniu.com'):
            raise forms.ValidationError("Adresa de email trebuie să fie de la domeniu.com")
        return email
    
    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        confirm_email = cleaned_data.get("confirm_email")
        if email and confirm_email and email != confirm_email:
            raise forms.ValidationError("Adresele de email nu coincid.")
