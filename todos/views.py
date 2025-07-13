from django.views import View
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Task
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.http import HttpResponseNotAllowed


class TaskListView(View):
    def get(self, request):
        search_query = request.GET.get("search", "").strip()

        if search_query:
            tasks = Task.objects.filter(
                Q(title__icontains=search_query)
                | Q(description__icontains=search_query)
            )
        else:
            tasks = Task.objects.all()

        return render(
            request,
            "todos/task_list.html",
            {"tasks": tasks, "search_query": search_query},
        )


class TaskCreateView(View):
    def get(self, request):
        return render(request, "todos/task_create.html")

    def post(self, request):
        title = request.POST.get("title", "").strip()
        description = request.POST.get("description", "").strip()

        if not title:
            messages.error(request, "Title is required.")
            return render(
                request,
                "todos/task_create.html",
                {"title": title, "description": description},
            )

        Task.objects.create(title=title, description=description)
        messages.success(request, "Task created successfully!")
        return redirect("task_list")


class TaskDetailView(View):
    def get(self, request, pk):
        task = get_object_or_404(Task, pk=pk)
        return render(request, "todos/task_detail.html", {"task": task})


class TaskEditView(View):
    def get(self, request, pk):
        task = get_object_or_404(Task, pk=pk)
        return render(request, "todos/task_edit.html", {"task": task})

    def post(self, request, pk):
        task = get_object_or_404(Task, pk=pk)
        title = request.POST.get("title", "").strip()
        description = request.POST.get("description", "").strip()
        is_complete = "is_complete" in request.POST

        if not title:
            messages.error(request, "Title is required.")
            return render(
                request,
                "todos/task_edit.html",
                {
                    "task": task,
                    "title": title,
                    "description": description,
                    "is_complete": is_complete,
                },
            )

        task.title = title
        task.description = description
        task.is_complete = is_complete
        task.save()

        messages.success(request, "Task updated successfully!")
        return redirect("task_list")


class TaskDeleteView(View):
    def get(self, request, pk):
        task = get_object_or_404(Task, pk=pk)
        return render(request, "todos/task_delete.html", {"task": task})

    def post(self, request, pk):
        task = get_object_or_404(Task, pk=pk)
        task_title = task.title
        task.delete()
        messages.success(request, f'Task "{task_title}" deleted successfully!')
        return redirect("task_list")


class TaskToggleView(View):
    def post(self, request, pk):
        task = get_object_or_404(Task, pk=pk)
        task.is_complete = not task.is_complete
        task.save()

        if task.is_complete:
            messages.success(request, f'Task "{task.title}" marked as complete!')
        else:
            messages.success(request, f'Task "{task.title}" marked as incomplete!')

        return redirect("task_list")

    def get(self, request, pk):
        return HttpResponseNotAllowed(["POST"])
