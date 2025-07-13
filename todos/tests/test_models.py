import pytest
from model_bakery import baker
from django.urls import reverse
from todos.models import Task


@pytest.mark.django_db
class TestTaskModel:
    def test_task_creation(self):
        """Test basic task creation"""
        task = baker.make(Task, title="Test Task")
        assert task.title == "Test Task"
        assert task.is_complete is False
        assert task.created_at is not None
        assert task.updated_at is not None

    def test_task_str_representation(self):
        """Test string representation"""
        task = baker.make(Task, title="My Task")
        assert str(task) == "My Task"

    def test_task_ordering(self):
        """Test default ordering by created_at desc"""
        task1 = baker.make(Task, title="First")
        task2 = baker.make(Task, title="Second")

        tasks = Task.objects.all()
        assert tasks[0] == task2  # Most recent first
        assert tasks[1] == task1

    # def test_get_absolute_url(self):
    #     """Test get_absolute_url method"""
    #     task = baker.make(Task)
    #     expected_url = reverse("task_detail", kwargs={"pk": task.pk})
    #     assert task.get_absolute_url() == expected_url
