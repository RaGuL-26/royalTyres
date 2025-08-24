from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum
from django.contrib.auth import authenticate, login, logout

from .models import Tyre, SaleLog
from .forms import TyreForm, TyreEditForm, SellForm


# --- Admin Add Stock ---
@login_required
def admin_page(request):
    if request.method == "POST":
        form = TyreForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Tyre added.")
            return redirect("inventory_page")
    else:
        form = TyreForm()
    return render(request, "admin_page.html", {"form": form})


# --- Inventory Page with Search + Filter ---
@login_required
def inventory_page(request):
    query = request.GET.get("q", "")
    tube_type = request.GET.get("tube_type", "")
    vehicle_type = request.GET.get("vehicle_type", "")

    tyres = Tyre.objects.all().order_by("brand", "model_with_size")

    if query:
        tyres = tyres.filter(
            Q(brand__icontains=query) |
            Q(model_with_size__icontains=query)
        )

    if tube_type:
        tyres = tyres.filter(tube_type__iexact=tube_type)

    if vehicle_type:
        tyres = tyres.filter(vehicle_type__iexact=vehicle_type)

    return render(request, "inventory_page.html", {
        "tyres": tyres,
        "query": query,
        "tube_type": tube_type,
        "vehicle_type": vehicle_type,
    })


# --- Edit Tyre (Invoice + Amazon fields only) ---
@login_required
def edit_tyre(request, tyre_id):
    tyre = get_object_or_404(Tyre, id=tyre_id)
    if request.method == "POST":
        form = TyreEditForm(request.POST, instance=tyre)
        if form.is_valid():
            form.save()
            messages.success(request, "Tyre updated.")
            return redirect("inventory_page")
    else:
        form = TyreEditForm(instance=tyre)
    return render(request, "edit_tyre.html", {"form": form, "tyre": tyre})


# --- Sell Tyre (quantity + Amazon/Retail + price + log profit) ---
@login_required
def sell_tyre(request, tyre_id, shop_code):
    tyre = get_object_or_404(Tyre, id=tyre_id)

    # Validate shop
    shop_code = (shop_code or "").upper()
    if shop_code not in ("TS", "GS"):
        messages.error(request, "Unknown shop. Use TS or GS.")
        return redirect("inventory_page")

    available = tyre.quantity_TS if shop_code == "TS" else tyre.quantity_GS

    if request.method == "POST":
        form = SellForm(request.POST)
        if form.is_valid():
            customer_type = form.cleaned_data['customer_type']
            customer_name = form.cleaned_data.get('customer_name') or ""
            qty = form.cleaned_data['quantity']
            custom_price = form.cleaned_data.get('custom_price')

            if qty <= 0:
                messages.error(request, "Enter a valid quantity (> 0).")
                return render(request, "sell_tyre.html", {"tyre": tyre, "shop_code": shop_code, "available": available, "form": form})

            if qty > available:
                messages.error(request, f"Not enough stock in { 'Tirupur' if shop_code=='TS' else 'Gobi' }. Available: {available}.")
                return render(request, "sell_tyre.html", {"tyre": tyre, "shop_code": shop_code, "available": available, "form": form})

            # Determine unit price
            if customer_type == "Amazon":
                if not tyre.amazon_listed or tyre.amazon_price is None:
                    messages.error(request, "This tyre is not listed on Amazon or Amazon price is missing.")
                    return render(request, "sell_tyre.html", {"tyre": tyre, "shop_code": shop_code, "available": available, "form": form})
                unit_price = tyre.amazon_price
            else:  # Retail
                if custom_price is None:
                    messages.error(request, "Enter custom price for Retail sale.")
                    return render(request, "sell_tyre.html", {"tyre": tyre, "shop_code": shop_code, "available": available, "form": form})
                unit_price = Decimal(custom_price)

            # **Validation: price cannot be below invoice**
            if unit_price < tyre.invoice_price:
                messages.error(request, f"Unit price cannot be less than invoice price ({tyre.invoice_price}).")
                return render(request, "sell_tyre.html", {"tyre": tyre, "shop_code": shop_code, "available": available, "form": form})

            total_amount = unit_price * qty
            profit = total_amount - (tyre.invoice_price * qty)

            # Deduct stock
            if shop_code == "TS":
                tyre.quantity_TS -= qty
            else:
                tyre.quantity_GS -= qty
            tyre.save()

            # Log sale
            SaleLog.objects.create(
                tyre=tyre,
                shop_code=shop_code,
                customer_type=customer_type,
                customer_name=customer_name if customer_type == "Retail" else "",
                quantity_sold=qty,
                unit_price=unit_price,
                total_amount=total_amount,
                profit=profit,
                updated_by=request.user
            )

            messages.success(request, f"Sold {qty} of {tyre.model_with_size} from {'Tirupur' if shop_code=='TS' else 'Gobi'}.")
            return redirect("sale_log")
    else:
        form = SellForm()

    return render(request, "sell_tyre.html", {"tyre": tyre, "shop_code": shop_code, "available": available, "form": form})


# --- Sale Log with Filter & Total Profit ---
@login_required
def sale_log(request):
    sales = SaleLog.objects.all().order_by("-sold_at")

    # Filters
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    shop = request.GET.get('shop')
    type_filter = request.GET.get('type')

    if start_date:
        sales = sales.filter(sold_at__date__gte=start_date)
    if end_date:
        sales = sales.filter(sold_at__date__lte=end_date)
    if shop:
        sales = sales.filter(shop_code=shop)
    if type_filter:
        sales = sales.filter(customer_type=type_filter)

    # Total profit
    total_profit = sales.aggregate(total=Sum('profit'))['total'] or 0

    return render(request, "sale_log.html", {
        "sales": sales,
        "total_profit": total_profit,
        "start_date": start_date,
        "end_date": end_date,
        "shop": shop,
        "type_filter": type_filter
    })


# --- Admin Inventory (for delete) ---
@login_required
def admin_inventory(request):
    tyres = Tyre.objects.all().order_by("brand", "model_with_size")
    return render(request, "admin_inventory.html", {"tyres": tyres})


@login_required
def delete_tyre(request, tyre_id):
    tyre = get_object_or_404(Tyre, id=tyre_id)
    tyre.delete()
    messages.success(request, "Tyre deleted successfully.")
    return redirect("admin_inventory")


# --- Auth ---
def user_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect("admin_page")
        messages.error(request, "Invalid username or password")
    return render(request, "login.html")


def user_logout(request):
    logout(request)
    return redirect("login")
