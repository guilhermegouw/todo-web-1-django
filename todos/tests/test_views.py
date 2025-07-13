import pytest
from django.test import Client
from django.urls import reverse
from model_bakery import baker
from todos.models import Task


@pytest.mark.django_db
class TestTaskListView:
    def setup_method(self):
        self.client = Client()
        self.url = reverse("task_list")

    def test_empty_task_list(self):
        """Test task list with no tasks"""
        response = self.client.get(self.url)
        assert response.status_code == 200
        assert "No tasks available" in response.content.decode()

    def test_task_list_with_tasks(self):
        """Test task list displays tasks"""
        baker.make(Task, title="Task 1", is_complete=False)
        baker.make(Task, title="Task 2", is_complete=True)

        response = self.client.get(self.url)
        assert response.status_code == 200
        assert "Task 1" in response.content.decode()
        assert "Task 2" in response.content.decode()
        assert "Incomplete" in response.content.decode()
        assert "Complete" in response.content.decode()

    def test_task_list_contains_view_links(self):
        """Test task list contains view links for each task"""
        task = baker.make(Task, title="Test Task")

        response = self.client.get(self.url)
        assert response.status_code == 200

        content = response.content.decode()
        expected_url = reverse("task_detail", kwargs={"pk": task.pk})
        assert f'href="{expected_url}"' in content
        assert "View" in content

    def test_task_list_contains_edit_links(self):
        """Test task list contains edit links for each task"""
        task = baker.make(Task, title="Test Task")

        response = self.client.get(self.url)
        assert response.status_code == 200

        content = response.content.decode()
        expected_url = reverse("task_edit", kwargs={"pk": task.pk})
        assert f'href="{expected_url}"' in content
        assert "Edit" in content


    def test_search_by_title(self):
        """Test search functionality by title"""
        baker.make(Task, title="Important Meeting", description="Weekly standup")
        baker.make(Task, title="Buy Groceries", description="Milk and bread")
        baker.make(Task, title="Important Project", description="Finish the report")
        
        response = self.client.get(self.url, {'search': 'Important'})
        assert response.status_code == 200
        
        content = response.content.decode()
        assert "Important Meeting" in content
        assert "Important Project" in content
        assert "Buy Groceries" not in content

    def test_search_by_description(self):
        """Test search functionality by description"""
        baker.make(Task, title="Meeting", description="Important discussion")
        baker.make(Task, title="Shopping", description="Buy milk")
        
        response = self.client.get(self.url, {'search': 'Important'})
        assert response.status_code == 200
        
        content = response.content.decode()
        assert "Meeting" in content
        assert "Shopping" not in content

    def test_search_case_insensitive(self):
        """Test search is case insensitive"""
        baker.make(Task, title="URGENT Task", description="very important")
        
        response = self.client.get(self.url, {'search': 'urgent'})
        assert response.status_code == 200
        assert "URGENT Task" in response.content.decode()
        
        response = self.client.get(self.url, {'search': 'IMPORTANT'})
        assert response.status_code == 200
        assert "URGENT Task" in response.content.decode()

    def test_search_no_results(self):
        """Test search with no matching results"""
        baker.make(Task, title="Meeting", description="Weekly standup")
        
        response = self.client.get(self.url, {'search': 'nonexistent'})
        assert response.status_code == 200
        
        content = response.content.decode()
        assert "No tasks found" in content
        assert "Meeting" not in content

    def test_search_empty_query(self):
        """Test empty search shows all tasks"""
        baker.make(Task, title="Task 1")
        baker.make(Task, title="Task 2")
        
        response = self.client.get(self.url, {'search': ''})
        assert response.status_code == 200
        
        content = response.content.decode()
        assert "Task 1" in content
        assert "Task 2" in content

    def test_search_whitespace_trimmed(self):
        """Test search query whitespace is trimmed"""
        baker.make(Task, title="Important Task")
        
        response = self.client.get(self.url, {'search': '  Important  '})
        assert response.status_code == 200
        assert "Important Task" in response.content.decode()

    def test_search_preserves_query_in_form(self):
        """Test search form preserves the search query"""
        baker.make(Task, title="Important Task")
        
        response = self.client.get(self.url, {'search': 'Important'})
        assert response.status_code == 200
        assert 'value="Important"' in response.content.decode()


@pytest.mark.django_db
class TestTaskCreateView:
    def setup_method(self):
        self.client = Client()
        self.url = reverse("task_create")

    def test_get_create_form(self):
        """Test GET request shows form"""
        response = self.client.get(self.url)
        assert response.status_code == 200
        assert "Create New Task" in response.content.decode()
        assert 'name="title"' in response.content.decode()

    def test_create_task_success(self):
        """Test successful task creation"""
        data = {"title": "New Task", "description": "Task description"}
        response = self.client.post(self.url, data)

        assert response.status_code == 302
        assert response.url == reverse("task_list")
        task = Task.objects.get(title="New Task")
        assert task.description == "Task description"
        assert task.is_complete is False

    def test_create_task_without_title(self):
        """Test validation - title required"""
        data = {"description": "No title"}
        response = self.client.post(self.url, data)

        assert response.status_code == 200
        assert "Title is required" in response.content.decode()
        assert Task.objects.count() == 0

    def test_create_task_preserves_data_on_error(self):
        """Test form preserves data when validation fails"""
        data = {"title": "", "description": "Some description"}
        response = self.client.post(self.url, data)

        assert response.status_code == 200
        assert ">Some description</textarea>" in response.content.decode()


@pytest.mark.django_db
class TestTaskDetailView:
    def setup_method(self):
        self.client = Client()

    def test_task_detail_display(self):
        """Test task detail view displays all fields"""
        task = baker.make(
            Task, title="Test Task", description="This is a test task", is_complete=True
        )
        url = reverse("task_detail", kwargs={"pk": task.pk})

        response = self.client.get(url)
        assert response.status_code == 200

        content = response.content.decode()
        assert "Test Task" in content
        assert "This is a test task" in content
        assert "Complete" in content  # Status should show as Complete
        assert task.created_at.strftime("%b %d, %Y") in content
        assert task.updated_at.strftime("%b %d, %Y") in content

    def test_task_detail_incomplete_status(self):
        """Test task detail shows incomplete status correctly"""
        task = baker.make(Task, title="Incomplete Task", is_complete=False)
        url = reverse("task_detail", kwargs={"pk": task.pk})

        response = self.client.get(url)
        assert response.status_code == 200
        assert "Incomplete" in response.content.decode()

    def test_task_detail_nonexistent_task(self):
        """Test 404 for non-existent task"""
        url = reverse("task_detail", kwargs={"pk": 999})
        response = self.client.get(url)
        assert response.status_code == 404

    def test_task_detail_empty_description(self):
        """Test task detail handles empty description"""
        task = baker.make(Task, title="No Description Task", description="")
        url = reverse("task_detail", kwargs={"pk": task.pk})

        response = self.client.get(url)
        assert response.status_code == 200
        assert "No description" in response.content.decode()


@pytest.mark.django_db
class TestTaskEditView:
    def setup_method(self):
        self.client = Client()

    def test_get_edit_form_with_prepopulated_data(self):
        """Test GET request shows form with current task data"""
        task = baker.make(
            Task,
            title="Original Title",
            description="Original description",
            is_complete=True,
        )
        url = reverse("task_edit", kwargs={"pk": task.pk})

        response = self.client.get(url)
        assert response.status_code == 200

        content = response.content.decode()
        assert 'value="Original Title"' in content
        assert "Original description" in content
        assert "checked" in content

    def test_get_edit_form_incomplete_task(self):
        """Test GET request for incomplete task"""
        task = baker.make(Task, title="Test Task", is_complete=False)
        url = reverse("task_edit", kwargs={"pk": task.pk})

        response = self.client.get(url)
        assert response.status_code == 200

        content = response.content.decode()
        assert "checked" not in content

    def test_edit_task_success(self):
        """Test successful task edit"""
        task = baker.make(
            Task, title="Old Title", description="Old description", is_complete=False
        )
        url = reverse("task_edit", kwargs={"pk": task.pk})
        data = {
            "title": "New Title",
            "description": "New description",
            "is_complete": True,
        }
        response = self.client.post(url, data)

        assert response.status_code == 302
        assert response.url == reverse("task_list")

        task.refresh_from_db()
        assert task.title == "New Title"
        assert task.description == "New description"
        assert task.is_complete is True

    def test_edit_task_without_title(self):
        """Test validation - title required"""
        task = baker.make(Task, title="Original Title")
        url = reverse("task_edit", kwargs={"pk": task.pk})
        data = {"title": "", "description": "Some description"}
        response = self.client.post(url, data)

        assert response.status_code == 200
        assert "Title is required" in response.content.decode()

        task.refresh_from_db()
        assert task.title == "Original Title"

    def test_edit_nonexistent_task(self):
        """Test 404 for non-existent task"""
        url = reverse("task_edit", kwargs={"pk": 999})
        response = self.client.get(url)
        assert response.status_code == 404

    def test_edit_preserves_data_on_validation_error(self):
        """Test form preserves data when validation fails"""
        task = baker.make(Task, title="Original")
        url = reverse("task_edit", kwargs={"pk": task.pk})

        data = {"title": "", "description": "Updated description", "is_complete": True}
        response = self.client.post(url, data)

        assert response.status_code == 200
        content = response.content.decode()
        assert ">Updated description</textarea>" in content
        assert "checked" in content


# todos/tests/test_views.py - add this new test class

@pytest.mark.django_db
class TestTaskDeleteView:
    def setup_method(self):
        self.client = Client()
        
    def test_get_delete_confirmation_page(self):
        """Test GET request shows delete confirmation with task details"""
        task = baker.make(
            Task,
            title="Task to Delete",
            description="This task will be deleted",
            is_complete=True
        )
        url = reverse('task_delete', kwargs={'pk': task.pk})
        
        response = self.client.get(url)
        assert response.status_code == 200
        
        content = response.content.decode()
        assert "Delete Task" in content
        assert "Task to Delete" in content
        assert "This task will be deleted" in content
        assert "are you sure you want to delete" in content.lower()
        assert "Delete" in content
        assert "Cancel" in content
        
    def test_delete_task_success(self):
        """Test successful task deletion"""
        task = baker.make(Task, title="Task to Delete")
        url = reverse('task_delete', kwargs={'pk': task.pk})
        
        assert Task.objects.filter(pk=task.pk).exists()
        response = self.client.post(url)
        assert response.status_code == 302
        assert response.url == reverse('task_list')
        
        assert not Task.objects.filter(pk=task.pk).exists()

        response = self.client.get(reverse('task_list'))
        assert response.status_code == 200
        assert "deleted successfully" in response.content.decode()
        
    def test_delete_nonexistent_task(self):
        """Test 404 for non-existent task"""
        url = reverse('task_delete', kwargs={'pk': 999})
        
        response = self.client.get(url)
        assert response.status_code == 404
        
        response = self.client.post(url)
        assert response.status_code == 404
        
    def test_delete_confirmation_shows_task_status(self):
        """Test confirmation page shows complete/incomplete status"""
        incomplete_task = baker.make(Task, title="Incomplete Task", is_complete=False)
        complete_task = baker.make(Task, title="Complete Task", is_complete=True)
        
        url = reverse('task_delete', kwargs={'pk': incomplete_task.pk})
        response = self.client.get(url)
        assert "Incomplete" in response.content.decode()
        
        url = reverse('task_delete', kwargs={'pk': complete_task.pk})
        response = self.client.get(url)
        assert "Complete" in response.content.decode()


@pytest.mark.django_db
class TestTaskToggleView:
    def setup_method(self):
        self.client = Client()
        
    def test_toggle_incomplete_to_complete(self):
        """Test toggling incomplete task to complete"""
        task = baker.make(Task, title="Task to Complete", is_complete=False)
        url = reverse('task_toggle', kwargs={'pk': task.pk})
        
        assert task.is_complete is False
        
        response = self.client.post(url)
        assert response.status_code == 302
        assert response.url == reverse('task_list')
        
        task.refresh_from_db()
        assert task.is_complete is True
        
        response = self.client.get(reverse('task_list'))
        assert response.status_code == 200
        assert "marked as complete" in response.content.decode().lower()
        
    def test_toggle_complete_to_incomplete(self):
        """Test toggling complete task to incomplete"""
        task = baker.make(Task, title="Task to Mark Incomplete", is_complete=True)
        url = reverse('task_toggle', kwargs={'pk': task.pk})
        
        assert task.is_complete is True
        
        response = self.client.post(url)
        assert response.status_code == 302
        assert response.url == reverse('task_list')
        
        task.refresh_from_db()
        assert task.is_complete is False
        
        response = self.client.get(reverse('task_list'))
        assert response.status_code == 200
        assert "marked as incomplete" in response.content.decode().lower()
        
    def test_toggle_nonexistent_task(self):
        """Test 404 for non-existent task"""
        url = reverse('task_toggle', kwargs={'pk': 999})
        response = self.client.post(url)
        assert response.status_code == 404
        
    def test_toggle_only_accepts_post(self):
        """Test that GET requests are not allowed"""
        task = baker.make(Task, is_complete=False)
        url = reverse('task_toggle', kwargs={'pk': task.pk})
        
        response = self.client.get(url)
        assert response.status_code == 405
        
        task.refresh_from_db()
        assert task.is_complete is False
