from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.db import transaction
from .models import Book, ReadingList, ReadingListItem
from .serializers import (
    UserRegistrationSerializer, UserProfileSerializer, BookSerializer,
    ReadingListSerializer, ReadingListDetailSerializer, ReadingListItemSerializer
)

# authdication views


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            'message': 'User registered successfully',
            'user': UserProfileSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):

    username = request.data.get('username')
    password = request.data.get('password')

    if not username or not password:
        return Response({
            'error': 'Username and password are required'
        }, status=status.HTTP_400_BAD_REQUEST)

    user = authenticate(username=username, password=password)
    if user:
        refresh = RefreshToken.for_user(user)
        return Response({
            'message': 'Login successful',
            'user': UserProfileSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        })
    return Response({
        'error': 'Invalid credentials'
    }, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def profile(request):

    if request.method == 'GET':
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = UserProfileSerializer(
            request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Profile updated successfully',
                'user': serializer.data
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Book Management Views for add , update , delete


class BookListCreateView(generics.ListCreateAPIView):

    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            return Response({
                'message': 'Book created successfully',
                'book': serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BookDetailView(generics.RetrieveUpdateDestroyAPIView):

    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return [permissions.IsAuthenticated(), IsOwnerOrReadOnly()]
        return [permissions.IsAuthenticated()]

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.created_by != request.user:
            return Response({
                'error': 'You can only delete books you created'
            }, status=status.HTTP_403_FORBIDDEN)

        self.perform_destroy(instance)
        return Response({
            'message': 'Book deleted successfully'
        }, status=status.HTTP_204_NO_CONTENT)


# Reading List Views for CRUD

class ReadingListView(generics.ListCreateAPIView):

    serializer_class = ReadingListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ReadingList.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            return Response({
                'message': 'Reading list created successfully',
                'reading_list': serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ReadingListDetailView(generics.RetrieveUpdateDestroyAPIView):

    serializer_class = ReadingListDetailSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ReadingList.objects.filter(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({
            'message': 'Reading list deleted successfully'
        }, status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_book_to_reading_list(request, reading_list_id):

    try:
        reading_list = ReadingList.objects.get(
            id=reading_list_id, user=request.user)
    except ReadingList.DoesNotExist:
        return Response({
            'error': 'Reading list not found'
        }, status=status.HTTP_404_NOT_FOUND)

    book_id = request.data.get('book_id')
    order = request.data.get('order')

    if not book_id:
        return Response({
            'error': 'book_id is required'
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        book = Book.objects.get(id=book_id)
    except Book.DoesNotExist:
        return Response({
            'error': 'Book not found'
        }, status=status.HTTP_404_NOT_FOUND)

    if ReadingListItem.objects.filter(reading_list=reading_list, book=book).exists():
        return Response({
            'error': 'Book already in reading list'
        }, status=status.HTTP_400_BAD_REQUEST)

    # Set order to last position if not provided
    if not order:
        last_item = reading_list.items.last()
        order = (last_item.order + 1) if last_item else 1

    with transaction.atomic():
        # Shift existing items if necessary
        ReadingListItem.objects.filter(
            reading_list=reading_list,
            order__gte=order
        ).update(order=models.F('order') + 1)

        item = ReadingListItem.objects.create(
            reading_list=reading_list,
            book=book,
            order=order
        )

    serializer = ReadingListItemSerializer(item)
    return Response({
        'message': 'Book added to reading list successfully',
        'item': serializer.data
    }, status=status.HTTP_201_CREATED)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def remove_book_from_reading_list(request, reading_list_id, book_id):

    try:
        reading_list = ReadingList.objects.get(
            id=reading_list_id, user=request.user)
    except ReadingList.DoesNotExist:
        return Response({
            'error': 'Reading list not found'
        }, status=status.HTTP_404_NOT_FOUND)

    try:
        item = ReadingListItem.objects.get(
            reading_list=reading_list,
            book_id=book_id
        )
    except ReadingListItem.DoesNotExist:
        return Response({
            'error': 'Book not found in reading list'
        }, status=status.HTTP_404_NOT_FOUND)

    with transaction.atomic():
        removed_order = item.order
        item.delete()

        # Reorder remaining items
        ReadingListItem.objects.filter(
            reading_list=reading_list,
            order__gt=removed_order
        ).update(order=models.F('order') - 1)

    return Response({
        'message': 'Book removed from reading list successfully'
    }, status=status.HTTP_204_NO_CONTENT)



@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def reorder_reading_list(request, reading_list_id):

    try:
        reading_list = ReadingList.objects.get(
            id=reading_list_id, user=request.user)
    except ReadingList.DoesNotExist:
        return Response({
            'error': 'Reading list not found'
        }, status=status.HTTP_404_NOT_FOUND)

    book_orders = request.data.get('book_orders', [])
    if not book_orders:
        return Response({
            'error': 'book_orders list is required'
        }, status=status.HTTP_400_BAD_REQUEST)

    with transaction.atomic():
        for item in book_orders:
            book_id = item.get('book_id')
            order = item.get('order')

            try:
                reading_list_item = ReadingListItem.objects.get(
                    reading_list=reading_list,
                    book_id=book_id
                )
                reading_list_item.order = order
                reading_list_item.save()
            except ReadingListItem.DoesNotExist:
                continue

    return Response({
        'message': 'Reading list reordered successfully'
    })


class IsOwnerOrReadOnly(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.created_by == request.user
