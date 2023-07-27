from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notes.models import Note

User = get_user_model()


class TestListPage(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.URL = 'notes:list'
        cls.author1 = User.objects.create(username='Автор1')
        cls.author2 = User.objects.create(username='Автор2')
        cls.note_auth1 = Note.objects.create(
            title=f'Заголовок {cls.author1}',
            text=f'Текст {cls.author1}',
            author=cls.author1,
        )
        cls.note_auth2 = Note.objects.create(
            title=f'Заголовок {cls.author2}',
            text=f'Текст {cls.author2}',
            author=cls.author2,
        )

    def test_list_notes_context(self):
        self.client.force_login(self.author1)
        response = self.client.get(reverse(self.URL))
        self.assertIn(self.note_auth1, response.context['object_list'])

    def test_different_lists(self):
        users_notes = (
            (self.author1, self.note_auth2),
            (self.author2, self.note_auth1),
        )
        for user, note in users_notes:
            self.client.force_login(user)
            response = self.client.get(reverse(self.URL))
            self.assertNotIn(note, response.context['object_list'])
