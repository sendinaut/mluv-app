from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError

from user.models import InviteCode


class RegistrationForm(UserCreationForm):
    invite_token = forms.CharField(widget=forms.HiddenInput(), required=True)
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(
            attrs={"class": "input-field", "placeholder": "your@email.com"}
        ),
    )

    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = ("email",)
        field_classes = {}
        widgets = {
            "email": forms.EmailInput(
                attrs={"class": "input-field", "placeholder": "your@email.com"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "password1" in self.fields:
            self.fields["password1"].widget.attrs.update(
                {"class": "input-field", "placeholder": "••••••••"}
            )
        if "password2" in self.fields:
            self.fields["password2"].widget.attrs.update(
                {"class": "input-field", "placeholder": "••••••••"}
            )

    def clean_invite_token(self):
        token = self.cleaned_data.get("invite_token")

        try:
            invite = InviteCode.objects.get(code=token, is_used=False)

        except (ValueError, InviteCode.DoesNotExist):
            raise ValidationError(
                "Недійсне, застаріле або вже використане запрошувальне посилання."
            )
        return token

    def save(self, commit=True):
        user = super().save(commit=False)

        token = self.cleaned_data.get("invite_token")
        invite = InviteCode.objects.get(code=token)

        if invite.invite_role == "student":
            user.is_student = True
            user.is_teacher = False
        elif invite.invite_role == "teacher":
            user.is_student = False
            user.is_teacher = True

        if commit:
            user.save()

            user.refresh_from_db()
            user.is_student = True if invite.invite_role == "student" else False
            user.is_teacher = True if invite.invite_role == "teacher" else False
            user.save(update_fields=["is_student", "is_teacher"])

            invite.is_used = True
            invite.accepted_by = user
            invite.save()

        return user
