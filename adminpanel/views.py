from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum
from django.contrib import messages
from django.http import JsonResponse, Http404, HttpResponseRedirect
from django.contrib.auth.hashers import check_password, make_password
from django.utils import timezone
import uuid
import os

from .models import (
    Admin, User, FoodBusiness, NGO, Customer, Volunteer,
    FoodItem, FoodEligibility, FoodRequest, Match, Pickup,
    Delivery, Notification, Analytics,
)


# =======================================================================================================
# ADMIN
# =======================================================================================================

def admin_list(request):
    admins_qs = Admin.objects.all().order_by('-created_at')

    # ==============================
    # DASHBOARD COUNTS
    # ==============================

    total_admins = Admin.objects.count()
    active_admins = Admin.objects.filter(is_active=True).count()
    inactive_admins = Admin.objects.filter(is_active=False).count()
    super_admins = Admin.objects.filter(role='SUPER_ADMIN').count()

    # ---- search ----
    search = request.GET.get('q', '').strip()
    if search:
        admins_qs = admins_qs.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(email__icontains=search)
        )

    # ---- filter by role ----
    role = request.GET.get('role', '').strip()
    if role:
        admins_qs = admins_qs.filter(role=role)

    # ---- pagination ----
    paginator = Paginator(admins_qs, 10)
    page_number = request.GET.get('page', 1)
    admins = paginator.get_page(page_number)

    context = {
        'admins': admins,
        'search': search,
        'role': role,

        'total_admins': total_admins,
        'active_admins': active_admins,
        'inactive_admins': inactive_admins,
        'super_admins': super_admins,
    }
    return render(request, 'admin/admin_list.html', context)


def admin_edit(request, admin_id):
    admin_obj = get_object_or_404(Admin, id=admin_id)
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

    if request.method == 'POST':
        errors = {}

        new_first_name = admin_obj.first_name
        new_last_name = admin_obj.last_name
        new_email = admin_obj.email
        new_contact = admin_obj.contact
        new_role = admin_obj.role
        new_is_active = admin_obj.is_active

        if 'first_name' in request.POST:
            new_first_name = request.POST.get('first_name', '').strip()
            if not new_first_name:
                errors['first_name'] = 'First name is required.'

        if 'last_name' in request.POST:
            new_last_name = request.POST.get('last_name', '').strip() or None

        if 'email' in request.POST:
            new_email = request.POST.get('email', '').strip()
            if not new_email:
                errors['email'] = 'Email is required.'
            elif Admin.objects.exclude(id=admin_obj.id).filter(email__iexact=new_email).exists():
                errors['email'] = 'This email is already in use by another admin.'

        if 'contact' in request.POST:
            new_contact = request.POST.get('contact', '').strip()
            if not new_contact:
                errors['contact'] = 'Contact is required.'
            elif Admin.objects.exclude(id=admin_obj.id).filter(contact=new_contact).exists():
                errors['contact'] = 'This contact number is already in use by another admin.'

        if 'role' in request.POST:
            new_role = request.POST.get('role', admin_obj.role)
            if new_role not in dict(Admin.ROLE_CHOICES):
                errors['role'] = 'Invalid role.'

        if 'is_active' in request.POST:
            new_is_active = request.POST.get('is_active') in ('1', 'true', 'True', 'on')

        # ---- optional password change ----
        new_password_raw = request.POST.get('password', '').strip()
        if new_password_raw and len(new_password_raw) < 8:
            errors['password'] = 'Password must be at least 8 characters.'

        if errors:
            first_error = next(iter(errors.values()))
            if is_ajax:
                return JsonResponse({'error': first_error, 'errors': errors}, status=400)
            for field_error in errors.values():
                messages.error(request, field_error)
            return redirect('admin_edit', admin_id=admin_obj.id)

        admin_obj.first_name = new_first_name
        admin_obj.last_name = new_last_name
        admin_obj.email = new_email
        admin_obj.contact = new_contact
        admin_obj.role = new_role
        admin_obj.is_active = new_is_active
        if new_password_raw:
            admin_obj.password = make_password(new_password_raw)
        admin_obj.save()

        if is_ajax:
            return JsonResponse({'success': True, 'is_active': admin_obj.is_active})

        messages.success(request, 'Admin updated successfully.')
        return redirect('admin_list')

    return render(request, 'admin/admin_edit.html', {'admin_obj': admin_obj})


def admin_delete(request, admin_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method.'}, status=405)

    admin_obj = get_object_or_404(Admin, id=admin_id)
    admin_obj.delete()

    return JsonResponse({'success': True})


# =======================================================================================================
# USER (base account -- Food Business / NGO / Customer / Volunteer all sit on top of this)
# =======================================================================================================

def user_list(request):
    # select_related on all four possible profile OneToOnes so the template
    # can read user.food_business / user.ngo / user.customer / user.volunteer
    # without an extra query per row (the ones that don't apply are just None).
    users_qs = User.objects.select_related(
        'food_business', 'ngo', 'customer', 'volunteer'
    ).order_by('-created_at')

    # ==============================
    # DASHBOARD COUNTS
    # ==============================

    total_users = User.objects.count()
    total_food_businesses = User.objects.filter(role='FOOD_BUSINESS').count()
    total_ngos = User.objects.filter(role='NGO').count()
    total_customers = User.objects.filter(role='CUSTOMER').count()
    total_volunteers = User.objects.filter(role='VOLUNTEER').count()
    active_users = User.objects.filter(is_active=True).count()
    inactive_users = User.objects.filter(is_active=False).count()

    # ---- search ----
    search = request.GET.get('q', '').strip()
    if search:
        users_qs = users_qs.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(email__icontains=search) |
            Q(contact__icontains=search)
        )

    # ---- filter by role ----
    role = request.GET.get('role', '').strip()
    if role:
        users_qs = users_qs.filter(role=role)

    # ---- filter by status ----
    status = request.GET.get('status', '').strip()
    if status == 'active':
        users_qs = users_qs.filter(is_active=True)
    elif status == 'inactive':
        users_qs = users_qs.filter(is_active=False)

    # ---- pagination ----
    paginator = Paginator(users_qs, 10)
    page_number = request.GET.get('page', 1)
    users = paginator.get_page(page_number)

    context = {
        'users': users,
        'search': search,
        'role': role,
        'status': status,

        'total_users': total_users,
        'total_food_businesses': total_food_businesses,
        'total_ngos': total_ngos,
        'total_customers': total_customers,
        'total_volunteers': total_volunteers,
        'active_users': active_users,
        'inactive_users': inactive_users,
    }
    return render(request, 'admin/user_list.html', context)


def user_edit(request, user_id):
    user_obj = get_object_or_404(User, id=user_id)
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

    if request.method == 'POST':
        errors = {}

        new_first_name = user_obj.first_name
        new_last_name = user_obj.last_name
        new_email = user_obj.email
        new_contact = user_obj.contact
        new_is_active = user_obj.is_active

        if 'first_name' in request.POST:
            new_first_name = request.POST.get('first_name', '').strip()
            if not new_first_name:
                errors['first_name'] = 'First name is required.'

        if 'last_name' in request.POST:
            new_last_name = request.POST.get('last_name', '').strip() or None

        if 'email' in request.POST:
            new_email = request.POST.get('email', '').strip()
            if not new_email:
                errors['email'] = 'Email is required.'
            elif User.objects.exclude(id=user_obj.id).filter(email__iexact=new_email).exists():
                errors['email'] = 'This email is already in use by another user.'

        if 'contact' in request.POST:
            new_contact = request.POST.get('contact', '').strip()
            if not new_contact:
                errors['contact'] = 'Contact is required.'
            elif User.objects.exclude(id=user_obj.id).filter(contact=new_contact).exists():
                errors['contact'] = 'This contact number is already in use by another user.'

        if 'is_active' in request.POST:
            new_is_active = request.POST.get('is_active') in ('1', 'true', 'True', 'on')

        if errors:
            first_error = next(iter(errors.values()))
            if is_ajax:
                return JsonResponse({'error': first_error, 'errors': errors}, status=400)
            for field_error in errors.values():
                messages.error(request, field_error)
            return redirect('user_edit', user_id=user_obj.id)

        user_obj.first_name = new_first_name
        user_obj.last_name = new_last_name
        user_obj.email = new_email
        user_obj.contact = new_contact
        user_obj.is_active = new_is_active
        user_obj.save()

        if is_ajax:
            return JsonResponse({'success': True, 'is_active': user_obj.is_active})

        messages.success(request, 'User updated successfully.')
        return redirect('user_list')

    return render(request, 'admin/user_edit.html', {'user_obj': user_obj})


def user_delete(request, user_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method.'}, status=405)

    user_obj = get_object_or_404(User, id=user_id)
    user_obj.delete()  # cascades to whichever profile (FoodBusiness/NGO/Customer/Volunteer) exists

    return JsonResponse({'success': True})


def user_toggle_status(request, user_id):
    """AJAX-only quick toggle, same pattern as the approval-action branch
    in the reference file's user_edit -- a single-purpose action handled
    separately from the full field-by-field edit."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method.'}, status=405)

    user_obj = get_object_or_404(User, id=user_id)
    user_obj.is_active = not user_obj.is_active
    user_obj.save()

    return JsonResponse({'success': True, 'is_active': user_obj.is_active})


# =======================================================================================================
# FOOD BUSINESS (profile attached to a User with role='FOOD_BUSINESS')
# =======================================================================================================

def food_business_list(request):
    businesses_qs = FoodBusiness.objects.select_related('user').annotate(
        food_item_count=Count('food_items')
    ).order_by('-created_at')

    # ==============================
    # DASHBOARD COUNTS
    # ==============================

    total_businesses = FoodBusiness.objects.count()
    active_businesses = FoodBusiness.objects.filter(user__is_active=True).count()
    inactive_businesses = FoodBusiness.objects.filter(user__is_active=False).count()

    # ---- search ----
    search = request.GET.get('q', '').strip()
    if search:
        businesses_qs = businesses_qs.filter(
            Q(business_name__icontains=search) |
            Q(business_type__icontains=search) |
            Q(city__icontains=search) |
            Q(user__email__icontains=search)
        )

    # ---- filter by city ----
    city = request.GET.get('city', '').strip()
    if city:
        businesses_qs = businesses_qs.filter(city__iexact=city)

    # ---- pagination ----
    paginator = Paginator(businesses_qs, 10)
    page_number = request.GET.get('page', 1)
    businesses = paginator.get_page(page_number)

    context = {
        'businesses': businesses,
        'search': search,
        'city': city,

        'total_businesses': total_businesses,
        'active_businesses': active_businesses,
        'inactive_businesses': inactive_businesses,
    }
    return render(request, 'admin/food_business_list.html', context)


def food_business_edit(request, business_id):
    business = get_object_or_404(FoodBusiness, id=business_id)
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

    if request.method == 'POST':
        errors = {}

        new_business_name = business.business_name
        new_business_type = business.business_type
        new_contact_person = business.contact_person
        new_contact = business.contact
        new_address = business.address
        new_city = business.city
        new_pincode = business.pincode

        if 'business_name' in request.POST:
            new_business_name = request.POST.get('business_name', '').strip()
            if not new_business_name:
                errors['business_name'] = 'Business name is required.'

        if 'business_type' in request.POST:
            new_business_type = request.POST.get('business_type', '').strip()
            if not new_business_type:
                errors['business_type'] = 'Business type is required.'

        if 'contact_person' in request.POST:
            new_contact_person = request.POST.get('contact_person', '').strip()
            if not new_contact_person:
                errors['contact_person'] = 'Contact person is required.'

        if 'contact' in request.POST:
            new_contact = request.POST.get('contact', '').strip()
            if not new_contact:
                errors['contact'] = 'Contact is required.'

        if 'address' in request.POST:
            new_address = request.POST.get('address', '').strip()
            if not new_address:
                errors['address'] = 'Address is required.'

        if 'city' in request.POST:
            new_city = request.POST.get('city', '').strip()
            if not new_city:
                errors['city'] = 'City is required.'

        if 'pincode' in request.POST:
            new_pincode = request.POST.get('pincode', '').strip()
            if not new_pincode:
                errors['pincode'] = 'Pincode is required.'

        if errors:
            first_error = next(iter(errors.values()))
            if is_ajax:
                return JsonResponse({'error': first_error, 'errors': errors}, status=400)
            for field_error in errors.values():
                messages.error(request, field_error)
            return redirect('food_business_edit', business_id=business.id)

        business.business_name = new_business_name
        business.business_type = new_business_type
        business.contact_person = new_contact_person
        business.contact = new_contact
        business.address = new_address
        business.city = new_city
        business.pincode = new_pincode
        business.save()

        if is_ajax:
            return JsonResponse({'success': True})

        messages.success(request, 'Food business updated successfully.')
        return redirect('food_business_list')

    return render(request, 'admin/food_business_edit.html', {'business': business})


def food_business_delete(request, business_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method.'}, status=405)

    business = get_object_or_404(FoodBusiness, id=business_id)
    business.delete()

    return JsonResponse({'success': True})


# =======================================================================================================
# NGO (profile attached to a User with role='NGO')
# =======================================================================================================

def ngo_list(request):
    ngos_qs = NGO.objects.select_related('user').order_by('-created_at')

    # ==============================
    # DASHBOARD COUNTS
    # ==============================

    total_ngos = NGO.objects.count()
    active_ngos = NGO.objects.filter(user__is_active=True).count()
    inactive_ngos = NGO.objects.filter(user__is_active=False).count()

    # ---- search ----
    search = request.GET.get('q', '').strip()
    if search:
        ngos_qs = ngos_qs.filter(
            Q(organization_name__icontains=search) |
            Q(city__icontains=search) |
            Q(user__email__icontains=search)
        )

    # ---- filter by receiver type ----
    receiver_type = request.GET.get('receiver_type', '').strip()
    if receiver_type:
        ngos_qs = ngos_qs.filter(receiver_type=receiver_type)

    # ---- pagination ----
    paginator = Paginator(ngos_qs, 10)
    page_number = request.GET.get('page', 1)
    ngos = paginator.get_page(page_number)

    context = {
        'ngos': ngos,
        'search': search,
        'receiver_type': receiver_type,

        'total_ngos': total_ngos,
        'active_ngos': active_ngos,
        'inactive_ngos': inactive_ngos,
    }
    return render(request, 'admin/ngo_list.html', context)


def ngo_edit(request, ngo_id):
    ngo = get_object_or_404(NGO, id=ngo_id)
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

    if request.method == 'POST':
        errors = {}

        new_organization_name = ngo.organization_name
        new_receiver_type = ngo.receiver_type
        new_contact_person = ngo.contact_person
        new_contact = ngo.contact
        new_address = ngo.address
        new_city = ngo.city
        new_pincode = ngo.pincode
        new_capacity = ngo.capacity
        new_requirements = ngo.requirements

        if 'organization_name' in request.POST:
            new_organization_name = request.POST.get('organization_name', '').strip()
            if not new_organization_name:
                errors['organization_name'] = 'Organization name is required.'

        if 'receiver_type' in request.POST:
            new_receiver_type = request.POST.get('receiver_type', '').strip()
            if not new_receiver_type:
                errors['receiver_type'] = 'Receiver type is required.'

        if 'contact_person' in request.POST:
            new_contact_person = request.POST.get('contact_person', '').strip()
            if not new_contact_person:
                errors['contact_person'] = 'Contact person is required.'

        if 'contact' in request.POST:
            new_contact = request.POST.get('contact', '').strip()
            if not new_contact:
                errors['contact'] = 'Contact is required.'

        if 'address' in request.POST:
            new_address = request.POST.get('address', '').strip()
            if not new_address:
                errors['address'] = 'Address is required.'

        if 'city' in request.POST:
            new_city = request.POST.get('city', '').strip()
            if not new_city:
                errors['city'] = 'City is required.'

        if 'pincode' in request.POST:
            new_pincode = request.POST.get('pincode', '').strip()
            if not new_pincode:
                errors['pincode'] = 'Pincode is required.'

        if 'capacity' in request.POST:
            new_capacity = request.POST.get('capacity', '').strip()
            try:
                if new_capacity == '' or float(new_capacity) <= 0:
                    errors['capacity'] = 'Capacity must be greater than 0.'
            except ValueError:
                errors['capacity'] = 'Capacity must be a number.'

        if 'requirements' in request.POST:
            new_requirements = request.POST.get('requirements', '').strip() or None

        if errors:
            first_error = next(iter(errors.values()))
            if is_ajax:
                return JsonResponse({'error': first_error, 'errors': errors}, status=400)
            for field_error in errors.values():
                messages.error(request, field_error)
            return redirect('ngo_edit', ngo_id=ngo.id)

        ngo.organization_name = new_organization_name
        ngo.receiver_type = new_receiver_type
        ngo.contact_person = new_contact_person
        ngo.contact = new_contact
        ngo.address = new_address
        ngo.city = new_city
        ngo.pincode = new_pincode
        ngo.capacity = new_capacity
        ngo.requirements = new_requirements
        ngo.save()

        if is_ajax:
            return JsonResponse({'success': True})

        messages.success(request, 'NGO updated successfully.')
        return redirect('ngo_list')

    return render(request, 'admin/ngo_edit.html', {'ngo': ngo})


def ngo_delete(request, ngo_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method.'}, status=405)

    ngo = get_object_or_404(NGO, id=ngo_id)
    ngo.delete()

    return JsonResponse({'success': True})


# =======================================================================================================
# CUSTOMER (profile attached to a User with role='CUSTOMER')
# =======================================================================================================

def customer_list(request):
    customers_qs = Customer.objects.select_related('user').order_by('-created_at')

    # ==============================
    # DASHBOARD COUNTS
    # ==============================

    total_customers = Customer.objects.count()
    active_customers = Customer.objects.filter(user__is_active=True).count()
    inactive_customers = Customer.objects.filter(user__is_active=False).count()

    # ---- search ----
    search = request.GET.get('q', '').strip()
    if search:
        customers_qs = customers_qs.filter(
            Q(user__first_name__icontains=search) |
            Q(user__last_name__icontains=search) |
            Q(user__email__icontains=search) |
            Q(city__icontains=search)
        )

    # ---- filter by city ----
    city = request.GET.get('city', '').strip()
    if city:
        customers_qs = customers_qs.filter(city__iexact=city)

    # ---- pagination ----
    paginator = Paginator(customers_qs, 10)
    page_number = request.GET.get('page', 1)
    customers = paginator.get_page(page_number)

    context = {
        'customers': customers,
        'search': search,
        'city': city,

        'total_customers': total_customers,
        'active_customers': active_customers,
        'inactive_customers': inactive_customers,
    }
    return render(request, 'admin/customer_list.html', context)


def customer_edit(request, customer_id):
    customer = get_object_or_404(Customer, id=customer_id)
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

    if request.method == 'POST':
        errors = {}

        new_address = customer.address
        new_city = customer.city
        new_pincode = customer.pincode
        new_food_preferences = customer.food_preferences

        if 'address' in request.POST:
            new_address = request.POST.get('address', '').strip()
            if not new_address:
                errors['address'] = 'Address is required.'

        if 'city' in request.POST:
            new_city = request.POST.get('city', '').strip()
            if not new_city:
                errors['city'] = 'City is required.'

        if 'pincode' in request.POST:
            new_pincode = request.POST.get('pincode', '').strip()
            if not new_pincode:
                errors['pincode'] = 'Pincode is required.'

        if 'food_preferences' in request.POST:
            new_food_preferences = request.POST.get('food_preferences', '').strip() or None

        if errors:
            first_error = next(iter(errors.values()))
            if is_ajax:
                return JsonResponse({'error': first_error, 'errors': errors}, status=400)
            for field_error in errors.values():
                messages.error(request, field_error)
            return redirect('customer_edit', customer_id=customer.id)

        customer.address = new_address
        customer.city = new_city
        customer.pincode = new_pincode
        customer.food_preferences = new_food_preferences
        customer.save()

        if is_ajax:
            return JsonResponse({'success': True})

        messages.success(request, 'Customer updated successfully.')
        return redirect('customer_list')

    return render(request, 'admin/customer_edit.html', {'customer': customer})


def customer_delete(request, customer_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method.'}, status=405)

    customer = get_object_or_404(Customer, id=customer_id)
    customer.delete()

    return JsonResponse({'success': True})


# =======================================================================================================
# VOLUNTEER (profile attached to a User with role='VOLUNTEER')
# =======================================================================================================

def volunteer_list(request):
    volunteers_qs = Volunteer.objects.select_related('user').annotate(
        pickup_count=Count('pickups')
    ).order_by('-created_at')

    # ==============================
    # DASHBOARD COUNTS
    # ==============================

    total_volunteers = Volunteer.objects.count()
    available_volunteers = Volunteer.objects.filter(availability_status='AVAILABLE').count()
    unavailable_volunteers = Volunteer.objects.exclude(availability_status='AVAILABLE').count()

    # ---- search ----
    search = request.GET.get('q', '').strip()
    if search:
        volunteers_qs = volunteers_qs.filter(
            Q(user__first_name__icontains=search) |
            Q(user__last_name__icontains=search) |
            Q(user__email__icontains=search) |
            Q(service_area__icontains=search)
        )

    # ---- filter by availability ----
    availability_status = request.GET.get('availability_status', '').strip()
    if availability_status:
        volunteers_qs = volunteers_qs.filter(availability_status=availability_status)

    # ---- pagination ----
    paginator = Paginator(volunteers_qs, 10)
    page_number = request.GET.get('page', 1)
    volunteers = paginator.get_page(page_number)

    context = {
        'volunteers': volunteers,
        'search': search,
        'availability_status': availability_status,

        'total_volunteers': total_volunteers,
        'available_volunteers': available_volunteers,
        'unavailable_volunteers': unavailable_volunteers,
    }
    return render(request, 'admin/volunteer_list.html', context)


def volunteer_edit(request, volunteer_id):
    volunteer = get_object_or_404(Volunteer, id=volunteer_id)
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

    if request.method == 'POST':
        errors = {}

        new_vehicle_type = volunteer.vehicle_type
        new_availability_status = volunteer.availability_status
        new_service_area = volunteer.service_area

        if 'vehicle_type' in request.POST:
            new_vehicle_type = request.POST.get('vehicle_type', '').strip() or None

        if 'availability_status' in request.POST:
            new_availability_status = request.POST.get('availability_status', '').strip()
            if new_availability_status not in ('AVAILABLE', 'BUSY', 'OFFLINE'):
                errors['availability_status'] = 'Invalid availability status.'

        if 'service_area' in request.POST:
            new_service_area = request.POST.get('service_area', '').strip() or None

        if errors:
            first_error = next(iter(errors.values()))
            if is_ajax:
                return JsonResponse({'error': first_error, 'errors': errors}, status=400)
            for field_error in errors.values():
                messages.error(request, field_error)
            return redirect('volunteer_edit', volunteer_id=volunteer.id)

        volunteer.vehicle_type = new_vehicle_type
        volunteer.availability_status = new_availability_status
        volunteer.service_area = new_service_area
        volunteer.save()

        if is_ajax:
            return JsonResponse({
                'success': True,
                'availability_status': volunteer.availability_status,
            })

        messages.success(request, 'Volunteer updated successfully.')
        return redirect('volunteer_list')

    return render(request, 'admin/volunteer_edit.html', {'volunteer': volunteer})


def volunteer_delete(request, volunteer_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method.'}, status=405)

    volunteer = get_object_or_404(Volunteer, id=volunteer_id)
    volunteer.delete()

    return JsonResponse({'success': True})


# =======================================================================================================
# FOOD ITEM
# =======================================================================================================

def food_item_list(request):
    items_qs = FoodItem.objects.select_related('provider', 'provider__user').annotate(
        request_count=Count('requests')
    ).order_by('-created_at')

    # ==============================
    # DASHBOARD COUNTS
    # ==============================

    total_items = FoodItem.objects.count()
    available_items = FoodItem.objects.filter(status='AVAILABLE').count()
    reserved_items = FoodItem.objects.filter(status='RESERVED').count()
    expired_items = FoodItem.objects.filter(expiry_time__lt=timezone.now()).count()

    # ---- search ----
    search = request.GET.get('q', '').strip()
    if search:
        items_qs = items_qs.filter(
            Q(food_name__icontains=search) |
            Q(category__icontains=search) |
            Q(provider__business_name__icontains=search)
        )

    # ---- filter by status ----
    status = request.GET.get('status', '').strip()
    if status:
        items_qs = items_qs.filter(status=status)

    # ---- filter by destination type ----
    destination_type = request.GET.get('destination_type', '').strip()
    if destination_type:
        items_qs = items_qs.filter(destination_type=destination_type)

    # ---- pagination ----
    paginator = Paginator(items_qs, 10)
    page_number = request.GET.get('page', 1)
    items = paginator.get_page(page_number)

    context = {
        'items': items,
        'search': search,
        'status': status,
        'destination_type': destination_type,

        'total_items': total_items,
        'available_items': available_items,
        'reserved_items': reserved_items,
        'expired_items': expired_items,
    }
    return render(request, 'admin/food_item_list.html', context)


def food_item_add(request):
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

    if request.method == 'POST':
        errors = {}

        provider_id = request.POST.get('provider', '').strip()
        food_name = request.POST.get('food_name', '').strip()
        category = request.POST.get('category', '').strip()
        quantity = request.POST.get('quantity', '').strip()
        unit = request.POST.get('unit', '').strip()
        preparation_time = request.POST.get('preparation_time') or None
        expiry_time = request.POST.get('expiry_time') or None
        condition = request.POST.get('condition', '').strip()
        destination_type = request.POST.get('destination_type', '').strip() or None
        status = request.POST.get('status', 'AVAILABLE').strip()

        provider = FoodBusiness.objects.filter(id=provider_id).first()
        if not provider:
            errors['provider'] = 'Select a valid food business.'
        if not food_name:
            errors['food_name'] = 'Food name is required.'
        if not category:
            errors['category'] = 'Category is required.'
        if not quantity:
            errors['quantity'] = 'Quantity is required.'
        else:
            try:
                if float(quantity) <= 0:
                    errors['quantity'] = 'Quantity must be greater than 0.'
            except ValueError:
                errors['quantity'] = 'Quantity must be a number.'
        if not unit:
            errors['unit'] = 'Unit is required.'
        if not preparation_time:
            errors['preparation_time'] = 'Preparation time is required.'
        if not expiry_time:
            errors['expiry_time'] = 'Expiry time is required.'
        if not condition:
            errors['condition'] = 'Condition is required.'
        if destination_type and destination_type not in dict(FoodItem.DESTINATION_TYPE_CHOICES):
            errors['destination_type'] = 'Invalid destination type.'

        # expiry must be after preparation -- mirrors the model's CheckConstraint
        if preparation_time and expiry_time and not errors.get('preparation_time') and not errors.get('expiry_time'):
            if expiry_time <= preparation_time:
                errors['expiry_time'] = 'Expiry time must be after preparation time.'

        if errors:
            first_error = next(iter(errors.values()))
            if is_ajax:
                return JsonResponse({'error': first_error, 'errors': errors}, status=400)
            for field_error in errors.values():
                messages.error(request, field_error)
            return redirect('food_item_add')

        item = FoodItem.objects.create(
            provider=provider,
            food_name=food_name,
            category=category,
            quantity=quantity,
            unit=unit,
            preparation_time=preparation_time,
            expiry_time=expiry_time,
            condition=condition,
            destination_type=destination_type,
            status=status,
        )

        if is_ajax:
            return JsonResponse({'success': True, 'item_id': item.id})

        messages.success(request, 'Food item added successfully.')
        return redirect('food_item_list')

    providers = FoodBusiness.objects.select_related('user').order_by('business_name')
    return render(request, 'admin/food_item_add.html', {'providers': providers})


def food_item_edit(request, item_id):
    item = get_object_or_404(FoodItem, id=item_id)
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

    if request.method == 'POST':
        errors = {}

        new_food_name = item.food_name
        new_category = item.category
        new_quantity = item.quantity
        new_unit = item.unit
        new_preparation_time = item.preparation_time
        new_expiry_time = item.expiry_time
        new_condition = item.condition
        new_destination_type = item.destination_type
        new_status = item.status

        if 'food_name' in request.POST:
            new_food_name = request.POST.get('food_name', '').strip()
            if not new_food_name:
                errors['food_name'] = 'Food name is required.'

        if 'category' in request.POST:
            new_category = request.POST.get('category', '').strip()
            if not new_category:
                errors['category'] = 'Category is required.'

        if 'quantity' in request.POST:
            new_quantity = request.POST.get('quantity', '').strip()
            try:
                if new_quantity == '' or float(new_quantity) <= 0:
                    errors['quantity'] = 'Quantity must be greater than 0.'
            except ValueError:
                errors['quantity'] = 'Quantity must be a number.'

        if 'unit' in request.POST:
            new_unit = request.POST.get('unit', '').strip()
            if not new_unit:
                errors['unit'] = 'Unit is required.'

        if 'preparation_time' in request.POST:
            new_preparation_time = request.POST.get('preparation_time') or None

        if 'expiry_time' in request.POST:
            new_expiry_time = request.POST.get('expiry_time') or None

        if 'condition' in request.POST:
            new_condition = request.POST.get('condition', '').strip()
            if not new_condition:
                errors['condition'] = 'Condition is required.'

        if 'destination_type' in request.POST:
            new_destination_type = request.POST.get('destination_type', '').strip() or None
            if new_destination_type and new_destination_type not in dict(FoodItem.DESTINATION_TYPE_CHOICES):
                errors['destination_type'] = 'Invalid destination type.'

        if 'status' in request.POST:
            new_status = request.POST.get('status', '').strip()

        if new_preparation_time and new_expiry_time and not errors.get('preparation_time') and not errors.get('expiry_time'):
            if new_expiry_time <= new_preparation_time:
                errors['expiry_time'] = 'Expiry time must be after preparation time.'

        if errors:
            first_error = next(iter(errors.values()))
            if is_ajax:
                return JsonResponse({'error': first_error, 'errors': errors}, status=400)
            for field_error in errors.values():
                messages.error(request, field_error)
            return redirect('food_item_edit', item_id=item.id)

        item.food_name = new_food_name
        item.category = new_category
        item.quantity = new_quantity
        item.unit = new_unit
        item.preparation_time = new_preparation_time
        item.expiry_time = new_expiry_time
        item.condition = new_condition
        item.destination_type = new_destination_type
        item.status = new_status
        item.save()

        if is_ajax:
            return JsonResponse({'success': True, 'status': item.status})

        messages.success(request, 'Food item updated successfully.')
        return redirect('food_item_list')

    return render(request, 'admin/food_item_edit.html', {'item': item})


def food_item_delete(request, item_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method.'}, status=405)

    item = get_object_or_404(FoodItem, id=item_id)
    item.delete()

    return JsonResponse({'success': True})


# =======================================================================================================
# FOOD ELIGIBILITY (one-to-one with FoodItem)
# =======================================================================================================

def food_eligibility_list(request):
    eligibility_qs = FoodEligibility.objects.select_related('food', 'food__provider').order_by('-checked_at')

    # ==============================
    # DASHBOARD COUNTS
    # ==============================

    total_checks = FoodEligibility.objects.count()
    eligible_count = FoodEligibility.objects.filter(is_eligible=True).count()
    ineligible_count = FoodEligibility.objects.filter(is_eligible=False).count()

    # ---- search ----
    search = request.GET.get('q', '').strip()
    if search:
        eligibility_qs = eligibility_qs.filter(
            Q(food__food_name__icontains=search) |
            Q(reason__icontains=search)
        )

    # ---- filter by eligibility status ----
    eligibility_status = request.GET.get('eligibility_status', '').strip()
    if eligibility_status:
        eligibility_qs = eligibility_qs.filter(eligibility_status=eligibility_status)

    # ---- pagination ----
    paginator = Paginator(eligibility_qs, 10)
    page_number = request.GET.get('page', 1)
    eligibility_records = paginator.get_page(page_number)

    context = {
        'eligibility_records': eligibility_records,
        'search': search,
        'eligibility_status': eligibility_status,

        'total_checks': total_checks,
        'eligible_count': eligible_count,
        'ineligible_count': ineligible_count,
    }
    return render(request, 'admin/food_eligibility_list.html', context)


def food_eligibility_edit(request, eligibility_id):
    eligibility = get_object_or_404(FoodEligibility, id=eligibility_id)
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

    if request.method == 'POST':
        errors = {}

        new_is_eligible = eligibility.is_eligible
        new_eligibility_status = eligibility.eligibility_status
        new_reason = eligibility.reason

        if 'is_eligible' in request.POST:
            new_is_eligible = request.POST.get('is_eligible') in ('1', 'true', 'True', 'on')

        if 'eligibility_status' in request.POST:
            new_eligibility_status = request.POST.get('eligibility_status', '').strip()
            if new_eligibility_status not in dict(FoodEligibility.ELIGIBILITY_STATUS_CHOICES):
                errors['eligibility_status'] = 'Invalid eligibility status.'

        if 'reason' in request.POST:
            new_reason = request.POST.get('reason', '').strip() or None

        if errors:
            first_error = next(iter(errors.values()))
            if is_ajax:
                return JsonResponse({'error': first_error, 'errors': errors}, status=400)
            for field_error in errors.values():
                messages.error(request, field_error)
            return redirect('food_eligibility_edit', eligibility_id=eligibility.id)

        eligibility.is_eligible = new_is_eligible
        eligibility.eligibility_status = new_eligibility_status
        eligibility.reason = new_reason
        eligibility.save()

        if is_ajax:
            return JsonResponse({'success': True})

        messages.success(request, 'Eligibility record updated successfully.')
        return redirect('food_eligibility_list')

    return render(request, 'admin/food_eligibility_edit.html', {'eligibility': eligibility})


def food_eligibility_delete(request, eligibility_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method.'}, status=405)

    eligibility = get_object_or_404(FoodEligibility, id=eligibility_id)
    eligibility.delete()

    return JsonResponse({'success': True})


# =======================================================================================================
# FOOD REQUEST
# =======================================================================================================

def food_request_list(request):
    requests_qs = FoodRequest.objects.select_related('food', 'requester_user').order_by('-requested_at')

    # ==============================
    # DASHBOARD COUNTS
    # ==============================

    total_requests = FoodRequest.objects.count()
    pending_requests = FoodRequest.objects.filter(status='PENDING').count()
    approved_requests = FoodRequest.objects.filter(status='APPROVED').count()
    rejected_requests = FoodRequest.objects.filter(status='REJECTED').count()

    # ---- search ----
    search = request.GET.get('q', '').strip()
    if search:
        requests_qs = requests_qs.filter(
            Q(food__food_name__icontains=search) |
            Q(requester_user__email__icontains=search) |
            Q(requester_user__first_name__icontains=search)
        )

    # ---- filter by status ----
    status = request.GET.get('status', '').strip()
    if status:
        requests_qs = requests_qs.filter(status=status)

    # ---- filter by request type ----
    request_type = request.GET.get('request_type', '').strip()
    if request_type:
        requests_qs = requests_qs.filter(request_type=request_type)

    # ---- pagination ----
    paginator = Paginator(requests_qs, 10)
    page_number = request.GET.get('page', 1)
    food_requests = paginator.get_page(page_number)

    context = {
        'food_requests': food_requests,
        'search': search,
        'status': status,
        'request_type': request_type,

        'total_requests': total_requests,
        'pending_requests': pending_requests,
        'approved_requests': approved_requests,
        'rejected_requests': rejected_requests,
    }
    return render(request, 'admin/food_request_list.html', context)


def food_request_edit(request, request_id):
    """Mainly used to approve/reject a request -- same status-only-update
    shape as the reference file's approval_action branch."""
    food_request = get_object_or_404(FoodRequest, id=request_id)
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

    if request.method == 'POST':
        errors = {}

        new_requested_quantity = food_request.requested_quantity
        new_status = food_request.status

        if 'requested_quantity' in request.POST:
            new_requested_quantity = request.POST.get('requested_quantity', '').strip()
            try:
                if new_requested_quantity == '' or float(new_requested_quantity) <= 0:
                    errors['requested_quantity'] = 'Requested quantity must be greater than 0.'
            except ValueError:
                errors['requested_quantity'] = 'Requested quantity must be a number.'

        if 'status' in request.POST:
            new_status = request.POST.get('status', '').strip()
            if new_status not in ('PENDING', 'APPROVED', 'REJECTED', 'FULFILLED', 'CANCELLED'):
                errors['status'] = 'Invalid status.'

        if errors:
            first_error = next(iter(errors.values()))
            if is_ajax:
                return JsonResponse({'error': first_error, 'errors': errors}, status=400)
            for field_error in errors.values():
                messages.error(request, field_error)
            return redirect('food_request_edit', request_id=food_request.id)

        food_request.requested_quantity = new_requested_quantity
        food_request.status = new_status
        food_request.save()

        if is_ajax:
            return JsonResponse({'success': True, 'status': food_request.status})

        messages.success(request, 'Food request updated successfully.')
        return redirect('food_request_list')

    return render(request, 'admin/food_request_edit.html', {'food_request': food_request})


def food_request_delete(request, request_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method.'}, status=405)

    food_request = get_object_or_404(FoodRequest, id=request_id)
    food_request.delete()

    return JsonResponse({'success': True})


# =======================================================================================================
# MATCH
# =======================================================================================================

def match_list(request):
    matches_qs = Match.objects.select_related('food', 'receiver_user').order_by('-matched_at')

    # ==============================
    # DASHBOARD COUNTS
    # ==============================

    total_matches = Match.objects.count()
    proposed_matches = Match.objects.filter(status='PROPOSED').count()
    accepted_matches = Match.objects.filter(status='ACCEPTED').count()
    completed_matches = Match.objects.filter(status='COMPLETED').count()
    rejected_matches = Match.objects.filter(status='REJECTED').count()

    # ---- search ----
    search = request.GET.get('q', '').strip()
    if search:
        matches_qs = matches_qs.filter(
            Q(food__food_name__icontains=search) |
            Q(receiver_user__email__icontains=search)
        )

    # ---- filter by status ----
    status = request.GET.get('status', '').strip()
    if status:
        matches_qs = matches_qs.filter(status=status)

    # ---- pagination ----
    paginator = Paginator(matches_qs, 10)
    page_number = request.GET.get('page', 1)
    matches = paginator.get_page(page_number)

    context = {
        'matches': matches,
        'search': search,
        'status': status,

        'total_matches': total_matches,
        'proposed_matches': proposed_matches,
        'accepted_matches': accepted_matches,
        'completed_matches': completed_matches,
        'rejected_matches': rejected_matches,
    }
    return render(request, 'admin/match_list.html', context)


def match_edit(request, match_id):
    match = get_object_or_404(Match, id=match_id)
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

    if request.method == 'POST':
        errors = {}

        new_distance_km = match.distance_km
        new_matched_quantity = match.matched_quantity
        new_match_score = match.match_score
        new_status = match.status

        if 'distance_km' in request.POST:
            new_distance_km = request.POST.get('distance_km', '').strip() or None
            if new_distance_km is not None:
                try:
                    if float(new_distance_km) < 0:
                        errors['distance_km'] = 'Distance cannot be negative.'
                except ValueError:
                    errors['distance_km'] = 'Distance must be a number.'

        if 'matched_quantity' in request.POST:
            new_matched_quantity = request.POST.get('matched_quantity', '').strip()
            try:
                if new_matched_quantity == '' or float(new_matched_quantity) <= 0:
                    errors['matched_quantity'] = 'Matched quantity must be greater than 0.'
            except ValueError:
                errors['matched_quantity'] = 'Matched quantity must be a number.'

        if 'match_score' in request.POST:
            new_match_score = request.POST.get('match_score', '').strip() or None

        if 'status' in request.POST:
            new_status = request.POST.get('status', '').strip()
            if new_status not in dict(Match.STATUS_CHOICES):
                errors['status'] = 'Invalid status.'

        if errors:
            first_error = next(iter(errors.values()))
            if is_ajax:
                return JsonResponse({'error': first_error, 'errors': errors}, status=400)
            for field_error in errors.values():
                messages.error(request, field_error)
            return redirect('match_edit', match_id=match.id)

        match.distance_km = new_distance_km
        match.matched_quantity = new_matched_quantity
        match.match_score = new_match_score
        match.status = new_status
        match.save()

        if is_ajax:
            return JsonResponse({
                'success': True,
                'status': match.status,
                'status_display': match.get_status_display(),
            })

        messages.success(request, 'Match updated successfully.')
        return redirect('match_list')

    return render(request, 'admin/match_edit.html', {'match': match})


def match_delete(request, match_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method.'}, status=405)

    match = get_object_or_404(Match, id=match_id)
    match.delete()

    return JsonResponse({'success': True})


# =======================================================================================================
# PICKUP
# =======================================================================================================

def pickup_list(request):
    pickups_qs = Pickup.objects.select_related('food', 'volunteer', 'volunteer__user').order_by('-created_at')

    # ==============================
    # DASHBOARD COUNTS
    # ==============================

    total_pickups = Pickup.objects.count()
    assigned_pickups = Pickup.objects.filter(status='ASSIGNED').count()
    in_progress_pickups = Pickup.objects.filter(status='IN_PROGRESS').count()
    completed_pickups = Pickup.objects.filter(status='COMPLETED').count()

    # ---- search ----
    search = request.GET.get('q', '').strip()
    if search:
        pickups_qs = pickups_qs.filter(
            Q(food__food_name__icontains=search) |
            Q(volunteer__user__email__icontains=search)
        )

    # ---- filter by status ----
    status = request.GET.get('status', '').strip()
    if status:
        pickups_qs = pickups_qs.filter(status=status)

    # ---- pagination ----
    paginator = Paginator(pickups_qs, 10)
    page_number = request.GET.get('page', 1)
    pickups = paginator.get_page(page_number)

    context = {
        'pickups': pickups,
        'search': search,
        'status': status,

        'total_pickups': total_pickups,
        'assigned_pickups': assigned_pickups,
        'in_progress_pickups': in_progress_pickups,
        'completed_pickups': completed_pickups,
    }
    return render(request, 'admin/pickup_list.html', context)


def pickup_edit(request, pickup_id):
    pickup = get_object_or_404(Pickup, id=pickup_id)
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

    if request.method == 'POST':
        errors = {}

        new_pickup_time = pickup.pickup_time
        new_status = pickup.status
        new_otp_code = pickup.otp_code

        if 'pickup_time' in request.POST:
            new_pickup_time = request.POST.get('pickup_time') or None
            if not new_pickup_time:
                errors['pickup_time'] = 'Pickup time is required.'

        if 'status' in request.POST:
            new_status = request.POST.get('status', '').strip()

        if 'otp_code' in request.POST:
            new_otp_code = request.POST.get('otp_code', '').strip() or None

        if errors:
            first_error = next(iter(errors.values()))
            if is_ajax:
                return JsonResponse({'error': first_error, 'errors': errors}, status=400)
            for field_error in errors.values():
                messages.error(request, field_error)
            return redirect('pickup_edit', pickup_id=pickup.id)

        pickup.pickup_time = new_pickup_time
        pickup.status = new_status
        pickup.otp_code = new_otp_code
        pickup.save()

        if is_ajax:
            return JsonResponse({'success': True, 'status': pickup.status})

        messages.success(request, 'Pickup updated successfully.')
        return redirect('pickup_list')

    return render(request, 'admin/pickup_edit.html', {'pickup': pickup})


def pickup_delete(request, pickup_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method.'}, status=405)

    pickup = get_object_or_404(Pickup, id=pickup_id)
    pickup.delete()

    return JsonResponse({'success': True})


# =======================================================================================================
# DELIVERY
# =======================================================================================================

def delivery_list(request):
    deliveries_qs = Delivery.objects.select_related(
        'pickup', 'pickup__food', 'receiver_user'
    ).order_by('-created_at')

    # ==============================
    # DASHBOARD COUNTS
    # ==============================

    total_deliveries = Delivery.objects.count()
    in_transit_deliveries = Delivery.objects.filter(status='IN_TRANSIT').count()
    delivered_deliveries = Delivery.objects.filter(status='DELIVERED').count()
    failed_deliveries = Delivery.objects.filter(status='FAILED').count()

    # ---- search ----
    search = request.GET.get('q', '').strip()
    if search:
        deliveries_qs = deliveries_qs.filter(
            Q(pickup__food__food_name__icontains=search) |
            Q(receiver_user__email__icontains=search)
        )

    # ---- filter by status ----
    status = request.GET.get('status', '').strip()
    if status:
        deliveries_qs = deliveries_qs.filter(status=status)

    # ---- pagination ----
    paginator = Paginator(deliveries_qs, 10)
    page_number = request.GET.get('page', 1)
    deliveries = paginator.get_page(page_number)

    context = {
        'deliveries': deliveries,
        'search': search,
        'status': status,

        'total_deliveries': total_deliveries,
        'in_transit_deliveries': in_transit_deliveries,
        'delivered_deliveries': delivered_deliveries,
        'failed_deliveries': failed_deliveries,
    }
    return render(request, 'admin/delivery_list.html', context)


def delivery_edit(request, delivery_id):
    delivery = get_object_or_404(Delivery, id=delivery_id)
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

    if request.method == 'POST':
        errors = {}

        new_delivery_time = delivery.delivery_time
        new_status = delivery.status
        new_verification_code = delivery.verification_code

        if 'delivery_time' in request.POST:
            new_delivery_time = request.POST.get('delivery_time') or None

        if 'status' in request.POST:
            new_status = request.POST.get('status', '').strip()

        if 'verification_code' in request.POST:
            new_verification_code = request.POST.get('verification_code', '').strip() or None

        # Delivered deliveries should carry a delivery_time -- guard rather
        # than silently allowing an inconsistent state.
        if new_status == 'DELIVERED' and not new_delivery_time:
            errors['delivery_time'] = 'Delivery time is required when marking as delivered.'

        if errors:
            first_error = next(iter(errors.values()))
            if is_ajax:
                return JsonResponse({'error': first_error, 'errors': errors}, status=400)
            for field_error in errors.values():
                messages.error(request, field_error)
            return redirect('delivery_edit', delivery_id=delivery.id)

        delivery.delivery_time = new_delivery_time
        delivery.status = new_status
        delivery.verification_code = new_verification_code
        delivery.save()

        if is_ajax:
            return JsonResponse({'success': True, 'status': delivery.status})

        messages.success(request, 'Delivery updated successfully.')
        return redirect('delivery_list')

    return render(request, 'admin/delivery_edit.html', {'delivery': delivery})


def delivery_delete(request, delivery_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method.'}, status=405)

    delivery = get_object_or_404(Delivery, id=delivery_id)
    delivery.delete()

    return JsonResponse({'success': True})


# =======================================================================================================
# NOTIFICATION
# =======================================================================================================

def notification_list(request):
    notifications_qs = Notification.objects.select_related('user').order_by('-created_at')

    # ==============================
    # DASHBOARD COUNTS
    # ==============================

    total_notifications = Notification.objects.count()
    read_notifications = Notification.objects.filter(is_read=True).count()
    unread_notifications = Notification.objects.filter(is_read=False).count()

    # ---- search ----
    search = request.GET.get('q', '').strip()
    if search:
        notifications_qs = notifications_qs.filter(
            Q(title__icontains=search) |
            Q(message__icontains=search) |
            Q(user__email__icontains=search)
        )

    # ---- filter by type ----
    notification_type = request.GET.get('notification_type', '').strip()
    if notification_type:
        notifications_qs = notifications_qs.filter(notification_type=notification_type)

    # ---- filter by read status ----
    is_read = request.GET.get('is_read', '').strip()
    if is_read == '1':
        notifications_qs = notifications_qs.filter(is_read=True)
    elif is_read == '0':
        notifications_qs = notifications_qs.filter(is_read=False)

    # ---- pagination ----
    paginator = Paginator(notifications_qs, 10)
    page_number = request.GET.get('page', 1)
    notifications = paginator.get_page(page_number)

    context = {
        'notifications': notifications,
        'search': search,
        'notification_type': notification_type,
        'is_read': is_read,

        'total_notifications': total_notifications,
        'read_notifications': read_notifications,
        'unread_notifications': unread_notifications,
    }
    return render(request, 'admin/notification_list.html', context)


def notification_add(request):
    """Send a single notification to one user. For broadcast-to-many-users,
    follow the reference file's admin_notification_add pattern: resolve a
    queryset of recipients, then Notification.objects.bulk_create(...)."""
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

    if request.method == 'POST':
        errors = {}

        user_id = request.POST.get('user', '').strip()
        title = request.POST.get('title', '').strip()
        message = request.POST.get('message', '').strip()
        notification_type = request.POST.get('notification_type', '').strip()

        target_user = User.objects.filter(id=user_id).first()
        if not target_user:
            errors['user'] = 'Select a valid user.'
        if not title:
            errors['title'] = 'Title is required.'
        if not message:
            errors['message'] = 'Message is required.'
        if not notification_type:
            errors['notification_type'] = 'Notification type is required.'

        if errors:
            first_error = next(iter(errors.values()))
            if is_ajax:
                return JsonResponse({'error': first_error, 'errors': errors}, status=400)
            for field_error in errors.values():
                messages.error(request, field_error)
            return redirect('notification_add')

        notification = Notification.objects.create(
            user=target_user,
            title=title,
            message=message,
            notification_type=notification_type,
        )

        if is_ajax:
            return JsonResponse({'success': True, 'notification_id': notification.id})

        messages.success(request, 'Notification sent successfully.')
        return redirect('notification_list')

    users_for_picker = User.objects.values('id', 'first_name', 'last_name', 'email', 'role').order_by('first_name')
    return render(request, 'admin/notification_add.html', {'users_for_picker': list(users_for_picker)})


def notification_mark_read(request, notification_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method.'}, status=405)

    notification = get_object_or_404(Notification, id=notification_id)
    notification.is_read = True
    notification.save()

    return JsonResponse({'success': True})


def notification_delete(request, notification_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method.'}, status=405)

    notification = get_object_or_404(Notification, id=notification_id)
    notification.delete()

    return JsonResponse({'success': True})


# =======================================================================================================
# ANALYTICS
# =======================================================================================================

def analytics_list(request):
    analytics_qs = Analytics.objects.select_related('food', 'food__provider').order_by('-record_date')

    # ==============================
    # DASHBOARD COUNTS
    # ==============================

    total_records = Analytics.objects.count()
    totals = Analytics.objects.aggregate(
        total_prepared=Sum('prepared_quantity'),
        total_sold=Sum('sold_quantity'),
        total_donated=Sum('donated_quantity'),
        total_rescued=Sum('rescued_quantity'),
        total_wasted=Sum('wasted_quantity'),
    )

    # ---- search ----
    search = request.GET.get('q', '').strip()
    if search:
        analytics_qs = analytics_qs.filter(
            Q(food__food_name__icontains=search) |
            Q(food__provider__business_name__icontains=search) |
            Q(remarks__icontains=search)
        )

    # ---- filter by date range ----
    date_from = request.GET.get('date_from', '').strip()
    date_to = request.GET.get('date_to', '').strip()
    if date_from:
        analytics_qs = analytics_qs.filter(record_date__gte=date_from)
    if date_to:
        analytics_qs = analytics_qs.filter(record_date__lte=date_to)

    # ---- pagination ----
    paginator = Paginator(analytics_qs, 10)
    page_number = request.GET.get('page', 1)
    analytics_records = paginator.get_page(page_number)

    context = {
        'analytics_records': analytics_records,
        'search': search,
        'date_from': date_from,
        'date_to': date_to,

        'total_records': total_records,
        'total_prepared': totals['total_prepared'] or 0,
        'total_sold': totals['total_sold'] or 0,
        'total_donated': totals['total_donated'] or 0,
        'total_rescued': totals['total_rescued'] or 0,
        'total_wasted': totals['total_wasted'] or 0,
    }
    return render(request, 'admin/analytics_list.html', context)


def analytics_edit(request, analytics_id):
    record = get_object_or_404(Analytics, id=analytics_id)
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

    if request.method == 'POST':
        errors = {}

        new_prepared_quantity = record.prepared_quantity
        new_sold_quantity = record.sold_quantity
        new_donated_quantity = record.donated_quantity
        new_rescued_quantity = record.rescued_quantity
        new_wasted_quantity = record.wasted_quantity
        new_record_date = record.record_date
        new_remarks = record.remarks

        def _clean_decimal(field_name, current_value, required=False):
            if field_name in request.POST:
                raw = request.POST.get(field_name, '').strip()
                if not raw:
                    if required:
                        errors[field_name] = f'{field_name.replace("_", " ").capitalize()} is required.'
                    return current_value
                try:
                    value = float(raw)
                    if value < 0:
                        errors[field_name] = f'{field_name.replace("_", " ").capitalize()} cannot be negative.'
                    return raw
                except ValueError:
                    errors[field_name] = f'{field_name.replace("_", " ").capitalize()} must be a number.'
                    return current_value
            return current_value

        new_prepared_quantity = _clean_decimal('prepared_quantity', new_prepared_quantity, required=True)
        new_sold_quantity = _clean_decimal('sold_quantity', new_sold_quantity)
        new_donated_quantity = _clean_decimal('donated_quantity', new_donated_quantity)
        new_rescued_quantity = _clean_decimal('rescued_quantity', new_rescued_quantity)
        new_wasted_quantity = _clean_decimal('wasted_quantity', new_wasted_quantity)

        if 'record_date' in request.POST:
            new_record_date = request.POST.get('record_date') or None
            if not new_record_date:
                errors['record_date'] = 'Record date is required.'

        if 'remarks' in request.POST:
            new_remarks = request.POST.get('remarks', '').strip() or None

        if errors:
            first_error = next(iter(errors.values()))
            if is_ajax:
                return JsonResponse({'error': first_error, 'errors': errors}, status=400)
            for field_error in errors.values():
                messages.error(request, field_error)
            return redirect('analytics_edit', analytics_id=record.id)

        record.prepared_quantity = new_prepared_quantity
        record.sold_quantity = new_sold_quantity
        record.donated_quantity = new_donated_quantity
        record.rescued_quantity = new_rescued_quantity
        record.wasted_quantity = new_wasted_quantity
        record.record_date = new_record_date
        record.remarks = new_remarks
        record.save()

        if is_ajax:
            return JsonResponse({'success': True})

        messages.success(request, 'Analytics record updated successfully.')
        return redirect('analytics_list')

    return render(request, 'admin/analytics_edit.html', {'record': record})


def analytics_delete(request, analytics_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method.'}, status=405)

    record = get_object_or_404(Analytics, id=analytics_id)
    record.delete()

    return JsonResponse({'success': True})