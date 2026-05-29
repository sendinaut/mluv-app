from django import forms
from django.contrib.auth import get_user_model
from crm.models import Lesson, Student

User = get_user_model()


class LessonCreateForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ["student", "datetime", "duration", "status"]
        widgets = {
            "datetime": forms.DateTimeInput(
                format="%Y-%m-%dT%H:%M",
                attrs={"type": "datetime-local", "class": "input-field"},
            ),
            "student": forms.Select(attrs={"class": "input-field"}),
            "duration": forms.NumberInput(
                attrs={"class": "input-field", "placeholder": "Хвилин (напр. 60)"}
            ),
            "status": forms.Select(attrs={"class": "input-field"}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        self.fields["student"].required = False

        if user:
            self.fields["student"].queryset = Student.objects.filter(teacher=user)


class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ["name", "lessons_count", "lesson_price"]
        widgets = {
            "name": forms.TextInput(
                attrs={"class": "input-field", "placeholder": "Ім'я студента"}
            ),
            "lessons_count": forms.NumberInput(
                attrs={
                    "class": "input-field",
                    "placeholder": "Баланс занять",
                    "min": "0",
                }
            ),
            "lesson_price": forms.NumberInput(
                attrs={
                    "class": "input-field",
                    "placeholder": "Ціна за одне заняття",
                    "step": "0.01",
                    "min": "0",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["lessons_count"].widget.attrs.update(
            {
                "class": "input-field",
                "min": "-999",
            }
        )


WEEKDAY_CHOICES = [
    (0, "Понеділок"),
    (1, "Вівторок"),
    (2, "Середа"),
    (3, "Четвер"),
    (4, "П'ятниця"),
    (5, "Субота"),
    (6, "Неділя"),
]


class RecurringScheduleForm(forms.Form):
    student = forms.ModelChoiceField(
        queryset=Student.objects.none(),
        widget=forms.Select(attrs={"class": "input-field"}),
        label="Студент",
    )
    weeks = forms.IntegerField(
        min_value=1,
        max_value=52,
        initial=4,
        widget=forms.NumberInput(attrs={"class": "input-field"}),
        label="На скільки тижнів",
    )
    start_from = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date", "class": "input-field"}),
        label="Починаючи з",
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            self.fields["student"].queryset = Student.objects.filter(teacher=user)

    def clean(self):
        cleaned = super().clean()
        selected_days = []
        for value, _ in WEEKDAY_CHOICES:
            if self.data.get(f"day_{value}"):
                time_str = self.data.get(f"time_{value}", "").strip()
                duration_str = self.data.get(f"duration_{value}", "").strip()
                errors = []
                if not time_str:
                    errors.append(f"Вкажіть час для дня {value}")
                if not duration_str:
                    errors.append(f"Вкажіть тривалість для дня {value}")
                if errors:
                    for e in errors:
                        self.add_error(None, e)
                    continue
                try:
                    from datetime import time as dtime

                    h, m = map(int, time_str.split(":"))
                    t = dtime(h, m)
                except (ValueError, AttributeError):
                    self.add_error(None, f"Невірний формат часу для дня {value}")
                    continue
                try:
                    dur = int(duration_str)
                    if dur < 15 or dur > 240:
                        raise ValueError
                except ValueError:
                    self.add_error(None, f"Невірна тривалість для дня {value}")
                    continue
                selected_days.append({"weekday": value, "time": t, "duration": dur})

        if not selected_days:
            self.add_error(None, "Оберіть хоча б один день тижня")

        cleaned["selected_days"] = selected_days
        return cleaned
