from django.db import migrations

def create_initial_categories(apps, schema_editor):
    Category = apps.get_model('main', 'Category')
    default_categories = [
        "Electronics & Gadgets",
        "Fashion & Apparel",
        "Home & Kitchen",
        "Beauty & Personal Care",
        "Books & Stationery",
        "Sports & Fitness",
        "Groceries & Essentials",
    ]
    for name in default_categories:
        Category.objects.get_or_create(name=name)

def remove_initial_categories(apps, schema_editor):
    Category = apps.get_model('main', 'Category')
    default_categories = [
        "Electronics & Gadgets",
        "Fashion & Apparel",
        "Home & Kitchen",
        "Beauty & Personal Care",
        "Books & Stationery",
        "Sports & Fitness",
        "Groceries & Essentials",
    ]
    Category.objects.filter(name__in=default_categories).delete()

class Migration(migrations.Migration):

    dependencies = [
        ('main', '0003_alter_category_options_productimage_uploaded_at_and_more'),
    ]

    operations = [
        migrations.RunPython(create_initial_categories, remove_initial_categories),
    ]
