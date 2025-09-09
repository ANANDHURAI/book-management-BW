from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from .models import Book, ReadingList, ReadingListItem


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password',
                  'password_confirm', 'first_name', 'last_name']

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "A user with this email already exists.")
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match.")
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email',
                  'first_name', 'last_name', 'date_joined']
        read_only_fields = ['id', 'username', 'date_joined']


class BookSerializer(serializers.ModelSerializer):
    created_by_username = serializers.CharField(
        source='created_by.username', read_only=True)

    class Meta:
        model = Book
        fields = ['id', 'title', 'authors', 'genre', 'publication_date', 'description',
                  'created_by', 'created_by_username', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']

    def validate_publication_date(self, value):
        from datetime import date
        if value > date.today():
            raise serializers.ValidationError(
                "Publication date cannot be in the future.")
        return value


class ReadingListSerializer(serializers.ModelSerializer):
    books_count = serializers.SerializerMethodField()

    class Meta:
        model = ReadingList
        fields = ['id', 'name', 'description',
                  'books_count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_books_count(self, obj):
        return obj.items.count()


class ReadingListItemSerializer(serializers.ModelSerializer):
    book = BookSerializer(read_only=True)
    book_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = ReadingListItem
        fields = ['id', 'book', 'book_id', 'order', 'added_at']
        read_only_fields = ['id', 'added_at']

    def validate_book_id(self, value):
        try:
            Book.objects.get(id=value)
        except Book.DoesNotExist:
            raise serializers.ValidationError("Book does not exist.")
        return value


class ReadingListDetailSerializer(serializers.ModelSerializer):
    items = ReadingListItemSerializer(many=True, read_only=True)

    class Meta:
        model = ReadingList
        fields = ['id', 'name', 'description',
                  'items', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
