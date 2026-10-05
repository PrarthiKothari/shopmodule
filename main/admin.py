from django.contrib import admin
from .models import Category, Product, ProductImage, ProductURL

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1

class ProductURLInline(admin.TabularInline):
    model = ProductURL
    extra = 1

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'category', 'created_by', 'base_price', 'gst', 'delivery_type', 'created_at')
    list_filter = ('category', 'created_by', 'delivery_type', 'created_at')
    search_fields = ('name', 'code', 'description', 'created_by__username')
    readonly_fields = ('code', 'created_at', 'updated_at')
    inlines = [ProductImageInline, ProductURLInline]

@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('product', 'is_primary', 'uploaded_at')
    list_filter = ('is_primary',)

@admin.register(ProductURL)
class ProductURLAdmin(admin.ModelAdmin):
    list_display = ('product', 'title', 'url', 'created_at')
