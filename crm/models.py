from __future__ import annotations
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F

from user.models import InviteCode

User = get_user_model()


class Student(models.Model):
    name = models.CharField(max_length=255, verbose_name="Ім'я учня")
    teacher = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="created_students",
        blank=False,
        null=False,
    )
    description = models.TextField(blank=True)
    student_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name="student_profile",
        blank=True,
        null=True,
    )

    invitation_code = models.ForeignKey(
        InviteCode,
        on_delete=models.SET_NULL,
        related_name="linked_students",
        blank=True,
        null=True,
        editable=False,
    )

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.invitation_code_id:
            from user.models import InviteCode

            super().save(*args, **kwargs)

            code = InviteCode.objects.create(
                invite_role="student",
                created_by=self.teacher,
            )

            self.invitation_code = code
            kwargs["force_insert"] = False

        super().save(*args, **kwargs)


class Lesson(models.Model):
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name="lessons")
    student = models.ForeignKey(
        Student, on_delete=models.CASCADE, related_name="lessons"
    )
    datetime = models.DateTimeField(verbose_name="Дата та час")
    duration = models.PositiveIntegerField(verbose_name="Тривалість (хв)")

    def __str__(self):
        return f"Урок {self.student.name} ({self.datetime.strftime('%d.%m %H:%M')})"

    def clean(self):
        super().clean()

        if not self.datetime or not self.duration or not self.teacher_id:
            return

        new_start = self.datetime
        new_end = new_start + timedelta(minutes=self.duration)

        overlapping_lessons = Lesson.objects.filter(
            teacher_id=self.teacher_id, datetime__lt=new_end
        )

        if self.pk:
            overlapping_lessons = overlapping_lessons.exclude(pk=self.pk)

        if overlapping_lessons.exists():
            conflict = overlapping_lessons.first()
            raise ValidationError(
                {
                    "datetime": f"У цей час уже є заняття! Перетин з уроком о {conflict.datetime.strftime('%H:%M')}."
                }
            )
