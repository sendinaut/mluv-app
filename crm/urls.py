from django.urls import path

from crm.views import (
    LessonScheduleView,
    StudentCreateView,
    StudentDeleteView,
    RecurringScheduleView,
    delete_lesson,
    get_create_form,
    edit_lesson,
)

app_name = "crm"

urlpatterns = [
    path("schedule/", LessonScheduleView.as_view(), name="schedule"),
    path("students/", StudentCreateView.as_view(), name="students"),
    path("students/<int:pk>/edit/", StudentCreateView.as_view(), name="student-edit"),
    path(
        "students/<int:pk>/delete/", StudentDeleteView.as_view(), name="student-delete"
    ),
    path("recurring/", RecurringScheduleView.as_view(), name="recurring"),
    path("lesson/<int:lesson_id>/edit/", edit_lesson, name="edit_lesson"),
    path("lesson/<int:lesson_id>/delete/", delete_lesson, name="delete_lesson"),
    path("lesson/create-form/", get_create_form, name="get_create_form"),
]
