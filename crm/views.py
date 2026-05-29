from datetime import datetime, timedelta
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.decorators import method_decorator
from django.views import View

from crm.models import Lesson, Student
from crm.forms import (
    LessonCreateForm,
    StudentForm,
    RecurringScheduleForm,
)


@method_decorator(login_required, name="dispatch")
class LessonScheduleView(View):
    template_name = "schedule/schedule.html"

    def get_week_bounds(self, week_str=None):
        if week_str:
            try:
                start_of_week = datetime.strptime(week_str + "-1", "%Y-W%W-%w").date()
            except ValueError:
                start_of_week = datetime.today().date() - timedelta(
                    days=datetime.today().weekday()
                )
        else:
            today = datetime.today().date()
            start_of_week = today - timedelta(days=today.weekday())

        end_of_week = start_of_week + timedelta(days=6)
        return start_of_week, end_of_week

    def get(self, request):
        selected_week = request.GET.get("week")
        start_date, end_date = self.get_week_bounds(selected_week)

        lessons = Lesson.objects.filter(
            teacher=request.user, datetime__date__range=[start_date, end_date]
        ).order_by("datetime")

        days_of_week = []
        for i in range(7):
            days_of_week.append(start_date + timedelta(days=i))

        prev_week = (start_date - timedelta(weeks=1)).strftime("%Y-W%W")
        next_week = (start_date + timedelta(weeks=1)).strftime("%Y-W%W")
        current_week_str = start_date.strftime("%Y-W%W")

        form = LessonCreateForm(user=request.user)

        WORKING_HOURS = range(9, 21)

        schedule_by_day = {}
        free_slots_by_day = {}
        for day in days_of_week:
            free_slots_by_day[day] = []
            day_lessons = sorted(
                [l for l in lessons if l.datetime.date() == day],
                key=lambda l: l.datetime,
            )

            items = []
            prev_end_hour = 9

            free_hours = []
            for hour in WORKING_HOURS:
                slot_start = datetime.combine(
                    day, datetime.min.time().replace(hour=hour)
                )
                slot_end = slot_start + timedelta(hours=1)
                is_free = True
                for lesson in day_lessons:
                    lesson_start = lesson.datetime
                    lesson_end = lesson_start + timedelta(minutes=lesson.duration)
                    if not (slot_end <= lesson_start or slot_start >= lesson_end):
                        is_free = False
                        break
                if is_free:
                    free_hours.append(hour)

            free_slots_by_day[day] = [f"{h:02d}:00" for h in free_hours]

            for lesson in day_lessons:
                lesson_start_hour = lesson.datetime.hour
                lesson_end_hour = lesson.datetime.hour + lesson.duration // 60
                if lesson.duration % 60:
                    lesson_end_hour += 1

                if lesson_start_hour > prev_end_hour:
                    items.append(
                        {
                            "type": "window",
                            "label": f"{prev_end_hour:02d}:00 – {lesson_start_hour:02d}:00",
                        }
                    )

                items.append({"type": "lesson", "obj": lesson})
                prev_end_hour = lesson_end_hour

            if prev_end_hour < 21:
                items.append(
                    {"type": "window", "label": f"{prev_end_hour:02d}:00 – 21:00"}
                )

            schedule_by_day[day] = items

        free_schedule = [free_slots_by_day[day] for day in days_of_week]

        context = {
            "lessons": lessons,
            "days_of_week": days_of_week,
            "form": form,
            "prev_week": prev_week,
            "next_week": next_week,
            "current_week_str": current_week_str,
            "start_date": start_date,
            "end_date": end_date,
            "free_schedule": free_schedule,
            "free_slots_by_day": free_slots_by_day,
            "schedule_by_day": schedule_by_day,
        }
        return render(request, self.template_name, context)

    def post(self, request):
        form = LessonCreateForm(request.POST, user=request.user)
        form.instance.teacher = request.user
        current_week_str = request.GET.get("week", "")

        if form.is_valid():
            saved_lesson = form.save(commit=False)
            saved_lesson.teacher = request.user
            if form.cleaned_data.get("is_blockout"):
                saved_lesson.student = Student.objects.get_or_create(
                    name="🔒 Зайнято / Блок", teacher=request.user
                )
            saved_lesson.save()
            return redirect(f"/schedule/?week={current_week_str}")

        start_date, end_date = self.get_week_bounds(current_week_str)
        lessons = Lesson.objects.filter(
            teacher=request.user, datetime__date__range=[start_date, end_date]
        ).order_by("datetime")

        start_date, end_date = self.get_week_bounds(current_week_str)
        lessons = Lesson.objects.filter(
            teacher=request.user, datetime__date__range=[start_date, end_date]
        ).order_by("datetime")

        days_of_week = [start_date + timedelta(days=i) for i in range(7)]
        prev_week = (start_date - timedelta(weeks=1)).strftime("%Y-W%W")
        next_week = (start_date + timedelta(weeks=1)).strftime("%Y-W%W")
        WORKING_HOURS = range(9, 21)

        schedule_by_day = {}
        free_slots_by_day = {}
        for day in days_of_week:
            free_slots_by_day[day] = []
            day_lessons = sorted(
                [l for l in lessons if l.datetime.date() == day],
                key=lambda l: l.datetime,
            )
            items = []
            prev_end_hour = 9
            free_hours = []
            for hour in WORKING_HOURS:
                slot_start = datetime.combine(
                    day, datetime.min.time().replace(hour=hour)
                )
                slot_end = slot_start + timedelta(hours=1)
                is_free = True
                for lesson in day_lessons:
                    lesson_start = lesson.datetime
                    lesson_end = lesson_start + timedelta(minutes=lesson.duration)
                    if not (slot_end <= lesson_start or slot_start >= lesson_end):
                        is_free = False
                        break
                if is_free:
                    free_hours.append(hour)
            free_slots_by_day[day] = [f"{h:02d}:00" for h in free_hours]

            for lesson in day_lessons:
                lesson_start_hour = lesson.datetime.hour
                lesson_end_hour = lesson.datetime.hour + lesson.duration // 60
                if lesson.duration % 60:
                    lesson_end_hour += 1
                if lesson_start_hour > prev_end_hour:
                    items.append(
                        {
                            "type": "window",
                            "label": f"{prev_end_hour:02d}:00 – {lesson_start_hour:02d}:00",
                        }
                    )
                items.append({"type": "lesson", "obj": lesson})
                prev_end_hour = lesson_end_hour
            if prev_end_hour < 21:
                items.append(
                    {"type": "window", "label": f"{prev_end_hour:02d}:00 – 21:00"}
                )
            schedule_by_day[day] = items

        free_schedule = [free_slots_by_day[day] for day in days_of_week]

        context = {
            "lessons": lessons,
            "days_of_week": days_of_week,
            "form": form,
            "prev_week": prev_week,
            "next_week": next_week,
            "current_week_str": current_week_str,
            "start_date": start_date,
            "end_date": end_date,
            "free_schedule": free_schedule,
            "free_slots_by_day": free_slots_by_day,
            "schedule_by_day": schedule_by_day,
        }
        return render(request, self.template_name, context)


@method_decorator(login_required, name="dispatch")
class StudentCreateView(View):
    template_name = "schedule/student_form.html"

    def get(self, request, pk=None):
        student = (
            get_object_or_404(Student, pk=pk, teacher=request.user) if pk else None
        )
        form = StudentForm(instance=student)
        students = Student.objects.filter(teacher=request.user).order_by("name")
        return render(
            request,
            self.template_name,
            {
                "form": form,
                "students": students,
                "editing": student,
            },
        )

    def post(self, request, pk=None):
        student = (
            get_object_or_404(Student, pk=pk, teacher=request.user) if pk else None
        )
        form = StudentForm(request.POST, instance=student)
        if form.is_valid():
            s = form.save(commit=False)
            s.teacher = request.user
            s.save()
            return redirect("crm:students")

        students = Student.objects.filter(teacher=request.user).order_by("name")
        return render(
            request,
            self.template_name,
            {
                "form": form,
                "students": students,
                "editing": student,
            },
        )


@method_decorator(login_required, name="dispatch")
class StudentDeleteView(View):
    def post(self, request, pk):
        student = get_object_or_404(Student, pk=pk, teacher=request.user)
        student.delete()
        messages.success(request, "Студента видалено.")
        return redirect("crm:students")


@method_decorator(login_required, name="dispatch")
class RecurringScheduleView(View):
    template_name = "schedule/recurring.html"

    DAY_CONFIGS = [
        (0, "Пн", "Понеділок"),
        (1, "Вт", "Вівторок"),
        (2, "Ср", "Середа"),
        (3, "Чт", "Четвер"),
        (4, "Пт", "П'ятниця"),
        (5, "Сб", "Субота"),
        (6, "Нд", "Неділя"),
    ]

    def get(self, request):
        form = RecurringScheduleForm(user=request.user)
        return render(
            request, self.template_name, {"form": form, "day_configs": self.DAY_CONFIGS}
        )

    def post(self, request):
        form = RecurringScheduleForm(request.POST, user=request.user)
        if not form.is_valid():
            return render(
                request,
                self.template_name,
                {"form": form, "day_configs": self.DAY_CONFIGS},
            )

        student = form.cleaned_data["student"]
        weeks = form.cleaned_data["weeks"]
        start_from = form.cleaned_data["start_from"]
        selected_days = form.cleaned_data["selected_days"]

        created = []
        for week_offset in range(weeks):
            for day_cfg in selected_days:
                weekday = day_cfg["weekday"]
                time_slot = day_cfg["time"]
                duration = day_cfg["duration"]

                days_ahead = (weekday - start_from.weekday()) % 7
                lesson_date = start_from + timedelta(days=days_ahead + week_offset * 7)
                lesson_dt = datetime.combine(lesson_date, time_slot)

                exists = Lesson.objects.filter(
                    teacher=request.user,
                    student=student,
                    datetime=lesson_dt,
                ).exists()
                if not exists:
                    created.append(
                        Lesson.objects.create(
                            teacher=request.user,
                            student=student,
                            datetime=lesson_dt,
                            duration=duration,
                        )
                    )

        messages.success(
            request, f"Створено {len(created)} урок(ів) для «{student.name}»."
        )
        return redirect("crm:students")


@login_required
def edit_lesson(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id, teacher=request.user)
    current_week_str = request.GET.get("week", "")

    if request.method == "POST":
        form = LessonCreateForm(request.POST, instance=lesson, user=request.user)
        form.instance.teacher = request.user

        if request.POST.get("is_blockout") == "on":
            blockout_student, _ = Student.objects.get_or_create(
                name="🔒 Зайнято / Блок", teacher=request.user
            )
            form.instance.student = blockout_student

        if form.is_valid():
            form.save()
            return redirect(f"/schedule/?week={current_week_str}")

        if not request.headers.get("HX-Request"):
            return redirect(f"/schedule/?week={current_week_str}")
    else:
        is_blockout = lesson.student and lesson.student.name == "🔒 Зайнято / Блок"
        form = LessonCreateForm(
            instance=lesson, user=request.user, initial={"is_blockout": is_blockout}
        )

    return render(
        request,
        "partials/edit_form.html",
        {"form": form, "lesson": lesson, "current_week_str": current_week_str},
    )


@login_required
def delete_lesson(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id, teacher=request.user)
    current_week_str = request.GET.get("week", "")
    lesson.delete()
    return redirect(f"/schedule/?week={current_week_str}")


@login_required
def get_create_form(request):
    form = LessonCreateForm(user=request.user)
    current_week_str = request.GET.get("week", "")
    return render(
        request,
        "partials/lesson_form.html",
        {"form": form, "current_week_str": current_week_str},
    )
