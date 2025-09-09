from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    # Authentication
    path('auth/register/', views.register, name='register'),
    path('auth/login/', views.login, name='login'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/profile/', views.profile, name='profile'),

    # Books
    path('books/', views.BookListCreateView.as_view(), name='book-list-create'),
    path('books/<int:pk>/', views.BookDetailView.as_view(), name='book-detail'),

    # Reading Lists
    path('reading-lists/', views.ReadingListView.as_view(), name='reading-list'),
    path('reading-lists/<int:pk>/', views.ReadingListDetailView.as_view(),
         name='reading-list-detail'),
    path('reading-lists/<int:reading_list_id>/add-book/',
         views.add_book_to_reading_list, name='add-book-to-list'),
    path('reading-lists/<int:reading_list_id>/remove-book/<int:book_id>/',
         views.remove_book_from_reading_list, name='remove-book-from-list'),
    path('reading-lists/<int:reading_list_id>/reorder/',
         views.reorder_reading_list, name='reorder-reading-list'),
]
