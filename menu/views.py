from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from core.decorators import role_required
from .forms import CategoryForm, MenuItemForm
from .models import Category, MenuItem


@role_required('owner', 'manager', 'waiter', 'kitchen')
def menu_manager(request):
    """View and manage all categories and menu items for the owner's restaurant."""
    restaurant = request.restaurant
    categories = restaurant.categories.all().prefetch_related('items')

    return render(request, 'dashboard/menu_manager.html', {
        'restaurant': restaurant,
        'categories': categories,
    })


@role_required('owner', 'manager')
def category_create(request):
    """Create a new category for the owner's restaurant."""
    restaurant = request.restaurant

    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save(commit=False)
            category.restaurant = restaurant  # Tenant isolation enforcement
            category.save()
            messages.success(request, f'Category "{category.name}" added successfully.')
            return redirect('dashboard:menu')
    else:
        # Default position to next available
        next_pos = restaurant.categories.count() + 1
        form = CategoryForm(initial={'position': next_pos})

    return render(request, 'dashboard/category_form.html', {
        'restaurant': restaurant,
        'form': form,
        'is_edit': False,
    })


@role_required('owner', 'manager')
def category_edit(request, pk):
    """Edit an existing category scoped strictly to the owner's restaurant."""
    restaurant = request.restaurant
    category = get_object_or_404(restaurant.categories, pk=pk)

    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, f'Category "{category.name}" updated successfully.')
            return redirect('dashboard:menu')
    else:
        form = CategoryForm(instance=category)

    return render(request, 'dashboard/category_form.html', {
        'restaurant': restaurant,
        'category': category,
        'form': form,
        'is_edit': True,
    })


@role_required('owner', 'manager')
def category_delete(request, pk):
    """Delete a category scoped strictly to the owner's restaurant."""
    restaurant = request.restaurant
    category = get_object_or_404(restaurant.categories, pk=pk)

    if request.method == 'POST':
        cat_name = category.name
        category.delete()
        messages.success(request, f'Category "{cat_name}" and all its items were deleted.')
        return redirect('dashboard:menu')

    return render(request, 'dashboard/confirm_delete.html', {
        'restaurant': restaurant,
        'object_type': 'Category',
        'object_name': category.name,
        'cancel_url': 'dashboard:menu',
    })


@role_required('owner', 'manager')
def item_create(request):
    """Add a new menu item scoped strictly to the owner's restaurant."""
    restaurant = request.restaurant

    if request.method == 'POST':
        form = MenuItemForm(request.POST, request.FILES, restaurant=restaurant)
        if form.is_valid():
            item = form.save(commit=False)
            item.restaurant = restaurant  # Tenant isolation enforcement
            item.save()
            messages.success(request, f'Item "{item.name}" added to menu.')
            return redirect('dashboard:menu')
    else:
        form = MenuItemForm(restaurant=restaurant)

    return render(request, 'dashboard/dish_form.html', {
        'restaurant': restaurant,
        'form': form,
        'is_edit': False,
    })


@role_required('owner', 'manager')
def item_edit(request, pk):
    """Edit a menu item scoped strictly to the owner's restaurant."""
    restaurant = request.restaurant
    item = get_object_or_404(restaurant.menu_items, pk=pk)

    if request.method == 'POST':
        form = MenuItemForm(request.POST, request.FILES, instance=item, restaurant=restaurant)
        if form.is_valid():
            form.save()
            messages.success(request, f'Item "{item.name}" updated.')
            return redirect('dashboard:menu')
    else:
        form = MenuItemForm(instance=item, restaurant=restaurant)

    return render(request, 'dashboard/dish_form.html', {
        'restaurant': restaurant,
        'item': item,
        'form': form,
        'is_edit': True,
    })


@role_required('owner', 'manager')
def item_delete(request, pk):
    """Delete a menu item scoped strictly to the owner's restaurant."""
    restaurant = request.restaurant
    item = get_object_or_404(restaurant.menu_items, pk=pk)

    if request.method == 'POST':
        item_name = item.name
        item.delete()
        messages.success(request, f'Item "{item_name}" deleted.')
        return redirect('dashboard:menu')

    return render(request, 'dashboard/confirm_delete.html', {
        'restaurant': restaurant,
        'object_type': 'Menu Item',
        'object_name': item.name,
        'cancel_url': 'dashboard:menu',
    })


@role_required('owner', 'manager', 'waiter', 'kitchen')
def item_toggle_availability(request, pk):
    """1-Tap toggle: Mark item available or sold out."""
    if request.method == 'POST':
        restaurant = request.restaurant
        item = get_object_or_404(restaurant.menu_items, pk=pk)
        item.is_available = not item.is_available
        item.save()

        # If AJAX request, return json
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('ajax'):
            return JsonResponse({
                'id': item.id,
                'is_available': item.is_available,
                'name': item.name
            })

        status_text = "available" if item.is_available else "sold out"
        messages.info(request, f'"{item.name}" marked as {status_text}.')
        
    return redirect('dashboard:menu')
