import io
import qrcode
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from core.decorators import owner_required
from .forms import RestaurantProfileForm


@owner_required
def dashboard_home(request):
    """Owner dashboard home screen with status, quick stats, and primary actions."""
    restaurant = request.restaurant
    categories = restaurant.categories.all()
    items = restaurant.menu_items.all()

    total_categories = categories.count()
    total_items = items.count()
    sold_out_items = items.filter(is_available=False).count()

    context = {
        'restaurant': restaurant,
        'total_categories': total_categories,
        'total_items': total_items,
        'sold_out_items': sold_out_items,
        'number_of_tables': restaurant.number_of_tables,
    }
    return render(request, 'dashboard/home.html', context)


@owner_required
def dashboard_profile(request):
    """Edit restaurant profile: name, logo, WhatsApp number, review link, etc."""
    restaurant = request.restaurant

    if request.method == 'POST':
        form = RestaurantProfileForm(request.POST, request.FILES, instance=restaurant)
        if form.is_valid():
            form.save()
            messages.success(request, 'Restaurant profile updated successfully.')
            return redirect('dashboard:profile')
    else:
        form = RestaurantProfileForm(instance=restaurant)

    return render(request, 'dashboard/profile.html', {
        'restaurant': restaurant,
        'form': form,
    })


@owner_required
def dashboard_toggle_status(request):
    """Toggle restaurant status between active and paused with one tap."""
    if request.method == 'POST':
        restaurant = request.restaurant
        if restaurant.status == 'active':
            restaurant.status = 'paused'
            messages.info(request, 'Restaurant menu is now temporarily paused for customers.')
        else:
            restaurant.status = 'active'
            messages.success(request, 'Restaurant menu is now active and accepting orders!')
        restaurant.save()
    return redirect('dashboard:home')


@owner_required
def dashboard_tables(request):
    """View and download QR codes and links for each table."""
    restaurant = request.restaurant
    base_url = request.build_absolute_uri(reverse('public:menu', kwargs={'slug': restaurant.slug}))
    
    tables = []
    for num in range(1, restaurant.number_of_tables + 1):
        table_url = f"{base_url}?table={num}"
        tables.append({
            'number': num,
            'url': table_url,
        })

    return render(request, 'dashboard/tables.html', {
        'restaurant': restaurant,
        'tables': tables,
        'base_url': base_url,
    })


@owner_required
def table_qr_code(request, table_number):
    """Generate and stream a high-resolution PNG QR code for a specific table."""
    restaurant = request.restaurant
    base_url = request.build_absolute_uri(reverse('public:menu', kwargs={'slug': restaurant.slug}))
    table_url = f"{base_url}?table={table_number}"

    # Generate QR Code image
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=2,
    )
    qr.add_data(table_url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="#123D33", back_color="#FFFFFF")

    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)

    filename = f"{restaurant.slug}-table-{table_number}-qr.png"
    response = HttpResponse(buffer.getvalue(), content_type='image/png')
    response['Content-Disposition'] = f'inline; filename="{filename}"'
    return response


@owner_required
def table_print_sheet(request):
    """Printable sheet with table QR cards for table stands or sticker prints."""
    restaurant = request.restaurant
    base_url = request.build_absolute_uri(reverse('public:menu', kwargs={'slug': restaurant.slug}))
    
    tables = []
    for num in range(1, restaurant.number_of_tables + 1):
        tables.append({
            'number': num,
            'url': f"{base_url}?table={num}",
            'qr_url': reverse('dashboard:table_qr', kwargs={'table_number': num}),
        })

    return render(request, 'dashboard/print_sheet.html', {
        'restaurant': restaurant,
        'tables': tables,
    })
