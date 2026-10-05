from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('home/', views.home, name='home'),
    path('sign-up/', views.sign_up, name='sign_up'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('create-product/', views.create_product, name='create_product'),
    path('products/', views.product_list, name='product_list'),
    path('products/trash/', views.trash_list, name='trash_list'),
    path('products/<int:product_id>/', views.product_detail, name='product_detail'),
    path('products/<int:product_id>/edit/', views.edit_product, name='edit_product'),
    path('products/<int:product_id>/delete/', views.delete_product, name='delete_product'),
    path('products/<int:product_id>/revive/', views.revive_product, name='revive_product'),
    path('products/<int:product_id>/purge/', views.permanent_delete_product, name='permanent_delete_product'),
    path('products/<int:product_id>/images/<int:image_id>/delete/', views.delete_product_image, name='delete_product_image'),
]