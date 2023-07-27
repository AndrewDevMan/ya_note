from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from notes.forms import WARNING
from notes.models import Note

User = get_user_model()


class TestNoteCreation(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.url = reverse('notes:add')
        cls.user = User.objects.create(username='TestUser')
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.user)
        cls.form_data = {
            'title': 'Заголовок',
            'text': 'Текст',
            'slug': 'slug',
            'author': cls.user,
        }

    def test_anonymous_user_cant_create_note(self):
        self.client.post(self.url, data=self.form_data)
        self.assertEqual(Note.objects.count(), 0)

    def test_auth_user_can_create_note(self):
        self.auth_client.post(self.url, data=self.form_data)
        self.assertEqual(Note.objects.count(), 1)
        note = Note.objects.get()
        self.assertEqual(note.title, self.form_data['title'])
        self.assertEqual(note.text, self.form_data['text'])
        self.assertEqual(note.author, self.user)

    def test_user_cant_use_dubled_slug(self):
        self.auth_client.post(self.url, data=self.form_data)
        bad_slug_data = {
            'title': 'Заголовок',
            'text': 'Текст',
            'slug': 'slug',
            'author': self.user,
        }
        response = self.auth_client.post(self.url, data=bad_slug_data)
        self.assertFormError(
            response,
            form='form',
            field='slug',
            errors=f'{bad_slug_data["slug"]}' + WARNING,
        )
        self.assertEqual(Note.objects.count(), 1)


class TestNoteEditDelete(TestCase):
    NOTE_TEXT = 'Текст комментария'
    NOTE_TITLE = 'Заголовок'
    NEW_NOTE_TEXT = 'Обновлённый комментарий'
    NEW_NOTE_TITLE = 'Обновлённый заголовок'

    @classmethod
    def setUpTestData(cls):

        cls.author = User.objects.create(username='Автор')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)

        cls.reader = User.objects.create(username='Не автор')
        cls.reader_client = Client()
        cls.reader_client.force_login(cls.reader)

        cls.note = Note.objects.create(
            title=cls.NOTE_TITLE,
            text=cls.NOTE_TEXT,
            author=cls.author,
        )
        cls.success_url = reverse('notes:success')
        cls.note_url = reverse('notes:detail', args=(cls.note.slug,))
        cls.edit_url = reverse('notes:edit', args=(cls.note.slug,))
        cls.delete_url = reverse('notes:delete', args=(cls.note.slug,))
        cls.form_data = {
            'title': cls.NEW_NOTE_TITLE,
            'text': cls.NEW_NOTE_TEXT,
        }

    def test_author_can_delete_note(self):
        response = self.author_client.delete(self.delete_url)
        self.assertRedirects(response, self.success_url)
        self.assertEqual(Note.objects.count(), 0)

    def test_user_cant_delete_note_of_another_user(self):
        response = self.reader_client.delete(self.delete_url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertEqual(Note.objects.count(), 1)

    def test_author_can_edit_note(self):
        response = self.author_client.post(self.edit_url, data=self.form_data)
        self.assertRedirects(response, self.success_url)
        self.note.refresh_from_db()
        self.assertEqual(self.note.text, self.NEW_NOTE_TEXT)
        self.assertEqual(self.note.title, self.NEW_NOTE_TITLE)

    def test_user_cant_edit_note_of_another_user(self):
        response = self.reader_client.post(self.edit_url, data=self.form_data)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.note.refresh_from_db()
        self.assertEqual(self.note.text, self.NOTE_TEXT)
        self.assertEqual(self.note.title, self.NOTE_TITLE)
