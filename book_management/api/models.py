from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator


class Book(models.Model):
    title = models.CharField(max_length=200)
    authors = models.CharField(
        max_length=300)
    genre = models.CharField(max_length=100)
    publication_date = models.DateField()
    description = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='books_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class ReadingList(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='reading_lists')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['user', 'name']

    def __str__(self):
        return f"{self.user.username} - {self.name}"


class ReadingListItem(models.Model):
    reading_list = models.ForeignKey(
        ReadingList, on_delete=models.CASCADE, related_name='items')
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order']
        unique_together = ['reading_list', 'book']

    def __str__(self):
        return f"{self.reading_list.name} - {self.book.title}"
