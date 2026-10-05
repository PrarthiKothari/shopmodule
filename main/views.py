from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count

from .forms import RegisterForm, ProductForm
from .models import Product, Category, ProductImage, ProductURL

@login_required(login_url='/login/')
def home(request):
    total_products = Product.objects.filter(is_deleted=False).count()
    total_categories = Category.objects.count()
    recent_products = Product.objects.filter(is_deleted=False).select_related('category').prefetch_related('images').order_by('-created_at')[:5]

    context = {
        'total_products': total_products,
        'total_categories': total_categories,
        'recent_products': recent_products,
    }
    return render(request, 'main/home.html', context)

def sign_up(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, f"Welcome to Shop Module, {user.username}! Your account has been created.")
            return redirect('home')
        else:
            messages.error(request, "Registration failed. Please check the errors below.")
    else:
        form = RegisterForm()

    return render(request, 'registration/sign_up.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('home')
        else:
            messages.error(request, "Invalid username/email or password.")
    else:
        form = AuthenticationForm()

    return render(request, 'registration/login.html', {'form': form})

def logout_view(request):
    auth_logout(request)
    messages.info(request, "You have been successfully logged out.")
    return redirect('login')

@login_required(login_url='/login/')
def create_product(request):
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.created_by = request.user
            product.save()

            images = request.FILES.getlist("images")
            for idx, img in enumerate(images):
                ProductImage.objects.create(
                    product=product,
                    image=img,
                    is_primary=(idx == 0)
                )

            urls_text = form.cleaned_data.get("urls", "")
            if urls_text:
                for line in urls_text.splitlines():
                    clean_url = line.strip()
                    if clean_url:
                        ProductURL.objects.create(product=product, url=clean_url)

            messages.success(request, f"Product '{product.name}' (Code: {product.code}) was created successfully!")
            return redirect("product_list")
        else:
            messages.error(request, "Please correct the errors in the form below.")
    else:
        form = ProductForm(initial={
            'delivery_type': 'STANDARD',
            'delivery_time': Product.DELIVERY_TIME_MAP.get('STANDARD', '3-5 Business Days'),
        })

    return render(request, "products/create_product.html", {"form": form})

@login_required(login_url='/login/')
def product_list(request):
    products = Product.objects.filter(is_deleted=False).select_related('category', 'created_by').prefetch_related('images').order_by('-created_at')
    trash_count = Product.objects.filter(is_deleted=True, created_by=request.user).count()
    return render(request, "products/product_list.html", {
        "products": products,
        "trash_count": trash_count,
    })

@login_required(login_url='/login/')
def product_detail(request, product_id):
    product = get_object_or_404(
        Product.objects.select_related('category', 'created_by').prefetch_related('images', 'urls'),
        id=product_id
    )
    if product.is_deleted:
        if product.created_by_id != request.user.id:
            messages.error(request, "This product has been removed.")
            return redirect("product_list")
    return render(request, 'products/product_detail.html', {'product': product})

@login_required(login_url='/login/')
def edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_deleted=False)

    if product.created_by_id != request.user.id:
        messages.error(request, "Permission Denied: You cannot edit a product created by another user.")
        return redirect("product_list")

    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            product = form.save(commit=False)
            if not product.created_by:
                product.created_by = request.user
            product.save()

            new_images = request.FILES.getlist("images")
            has_primary = product.images.filter(is_primary=True).exists()
            for idx, img in enumerate(new_images):
                ProductImage.objects.create(
                    product=product,
                    image=img,
                    is_primary=(not has_primary and idx == 0)
                )

            urls_text = form.cleaned_data.get("urls", "")
            if urls_text is not None:
                product.urls.all().delete()
                for line in urls_text.splitlines():
                    clean_url = line.strip()
                    if clean_url:
                        ProductURL.objects.create(product=product, url=clean_url)

            messages.success(request, f"Product '{product.name}' was updated successfully.")
            return redirect("product_detail", product_id=product.id)
        else:
            messages.error(request, "Please correct the errors in the form below.")
    else:
        existing_urls = "\n".join([u.url for u in product.urls.all()])
        initial_data = {'urls': existing_urls}
        if not product.delivery_time and product.delivery_type in Product.DELIVERY_TIME_MAP:
            initial_data['delivery_time'] = Product.DELIVERY_TIME_MAP[product.delivery_type]
        form = ProductForm(instance=product, initial=initial_data)

    return render(request, "products/edit_product.html", {
        "form": form,
        "product": product,
    })

@login_required(login_url='/login/')
def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_deleted=False)

    if product.created_by_id != request.user.id:
        messages.error(request, "Permission Denied: You cannot delete a product created by another user.")
        return redirect("product_list")

    if request.method == "POST":
        product_name = product.name
        product_code = product.code
        product.soft_delete()
        messages.warning(
            request,
            f"Product '{product_name}' ({product_code}) has been moved to Trash. "
            f"It will be permanently removed in 30 days. You can revive this product anytime from your Trash."
        )
        return redirect("product_list")

    return render(request, "products/delete_confirm.html", {"product": product})

@login_required(login_url='/login/')
def trash_list(request):
    deleted_products = Product.objects.filter(
        is_deleted=True,
        created_by=request.user
    ).select_related('category').prefetch_related('images').order_by('-deleted_at')
    return render(request, "products/trash_list.html", {"products": deleted_products})

@login_required(login_url='/login/')
def revive_product(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_deleted=True)

    if product.created_by_id != request.user.id:
        messages.error(request, "Permission Denied: You cannot revive a product created by another user.")
        return redirect("product_list")

    product.revive()
    messages.success(request, f"Product '{product.name}' ({product.code}) has been revived and restored to your catalog.")
    return redirect("product_list")

@login_required(login_url='/login/')
def permanent_delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_deleted=True)

    if product.created_by_id != request.user.id:
        messages.error(request, "Permission Denied: You cannot delete a product created by another user.")
        return redirect("trash_list")

    if request.method == "POST":
        product_name = product.name
        product_code = product.code
        product.delete()
        messages.success(request, f"Product '{product_name}' ({product_code}) was permanently deleted.")
    return redirect("trash_list")

@login_required(login_url='/login/')
def delete_product_image(request, product_id, image_id):
    product = get_object_or_404(Product, id=product_id)

    if product.created_by_id != request.user.id:
        messages.error(request, "Permission Denied: You cannot delete images for a product created by another user.")
        return redirect("product_list")

    image = get_object_or_404(ProductImage, id=image_id, product=product)

    if request.method == "POST":
        image.delete()
        messages.success(request, "Image was deleted.")
    return redirect("edit_product", product_id=product.id)
