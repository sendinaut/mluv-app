from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from crm.models import Lesson, LessonStatus


def manage_finished_lessons():
    queryset = Lesson.objects.filter(
        status=LessonStatus.PLANNED,
        datetime__lte=timezone.now() - timedelta(hours=2),
    )

    with transaction.atomic():
        for lesson in queryset:
            lesson.status = LessonStatus.FINISHED
            lesson.save()
