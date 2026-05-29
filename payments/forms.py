from django import forms


class PaymentInformationForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={"required": True}))
    full_name = forms.CharField(
        max_length=255, required=False, widget=forms.TextInput()
    )
    phone_number = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "+380"}),
    )
