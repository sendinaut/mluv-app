from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.db import transaction
from crm.models import Lesson, LessonStatus


@receiver(pre_save, sender=Lesson)
def handle_lesson_status_change(sender, instance: Lesson, **kwargs):
    if not instance.pk:
        old_status = None
    else:
        try:
            old_instance = Lesson.objects.get(pk=instance.pk)
            old_status = old_instance.status
        except Lesson.DoesNotExist:
            old_status = None

    new_status = instance.status

    if instance.student:
        transaction.on_commit(
            lambda: update_student_balance(instance.student, old_status, new_status)
        )


def update_student_balance(student, old_status, new_status):
    student.refresh_from_db()

    if (
        old_status not in (LessonStatus.FINISHED, LessonStatus.CANCELED)
        and new_status == LessonStatus.FINISHED
    ):
        student.lessons_count -= 1
        student.save(update_fields=["lessons_count"])
    elif (
        old_status not in (LessonStatus.FINISHED, LessonStatus.CANCELED)
        and new_status == LessonStatus.CANCELED
    ):
        student.lessons_count -= 1
        student.save(update_fields=["lessons_count"])
    elif old_status == LessonStatus.FINISHED and new_status == LessonStatus.PLANNED:
        student.lessons_count += 1
        student.save(update_fields=["lessons_count"])
