from functools import wraps

from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.hashers import check_password, make_password
from django.core.paginator import Paginator
from django.db.models import Count, Q, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .models import (
    Admin, User, FoodBusiness, NGO, Customer, Volunteer,
    FoodItem, FoodEligibility, FoodRequest, Match, Pickup,
    Delivery, Notification, Analytics,
)


# -----------------------------------------------------------------------------
# Authentication helpers
# -----------------------------------------------------------------------------

def admin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        admin_id = request.session.get('admin_id')
        if not admin_id:
            return redirect('login')
        admin_obj = Admin.objects.filter(id=admin_id, is_active=True).first()
        if not admin_obj:
            request.session.flush()
            return redirect('login')
        request.admin_obj = admin_obj
        return view_func(request, *args, **kwargs)
    return wrapper


def user_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper


def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')

        admin_obj = Admin.objects.filter(email__iexact=email, is_active=True).first()
        admin_password_ok = bool(admin_obj and check_password(password, admin_obj.password))
        # Support legacy development records that stored a plain password;
        # immediately upgrade them to a secure Django password hash.
        if admin_obj and not admin_password_ok and admin_obj.password == password:
            admin_obj.password = make_password(password)
            admin_obj.save(update_fields=['password', 'updated_at'])
            admin_password_ok = True
        if admin_obj and admin_password_ok:
            request.session.flush()
            request.session['admin_id'] = admin_obj.id
            request.session['admin_role'] = admin_obj.role
            request.session.set_expiry(60 * 60 * 24 * 7 if request.POST.get('remember') else 0)
            return redirect('admin_dashboard')

        user = authenticate(request, username=email, password=password)
        if user is not None and user.is_active:
            auth_login(request, user)
            request.session['user_role'] = user.role
            return redirect('role_dashboard')

        messages.error(request, 'Invalid email or password, or the account is inactive.')

    return render(request, 'login.html')


def logout_view(request):
    auth_logout(request)
    request.session.flush()
    return redirect('login')


def register_view(request):
    if request.method == 'POST':
        role_map = {
            'business': 'FOOD_BUSINESS',
            'ngo': 'NGO',
            'customer': 'CUSTOMER',
            'volunteer': 'VOLUNTEER',
        }
        role = role_map.get(request.POST.get('role', 'business'))
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip() or None
        email = request.POST.get('email', '').strip().lower()
        contact = request.POST.get('contact', '').strip()
        password = request.POST.get('password', '')
        address = request.POST.get('address', '').strip()
        city = request.POST.get('city', '').strip()
        state = request.POST.get('state', '').strip() or 'Gujarat'
        pincode = request.POST.get('pincode', '').strip()

        errors = []
        if not role:
            errors.append('Please select a valid role.')
        if not first_name:
            errors.append('First name is required.')
        if not email:
            errors.append('Email is required.')
        if User.objects.filter(email__iexact=email).exists() or Admin.objects.filter(email__iexact=email).exists():
            errors.append('An account with this email already exists.')
        if not contact or not contact.isdigit() or len(contact) not in (10, 11, 12, 15):
            errors.append('Enter a valid contact number.')
        if User.objects.filter(contact=contact).exists() or Admin.objects.filter(contact=contact).exists():
            errors.append('This contact number is already registered.')
        if len(password) < 8:
            errors.append('Password must be at least 8 characters.')
        if not address or not city or not pincode:
            errors.append('Address, city and pincode are required.')

        if not errors:
            user = User.objects.create_user(
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                contact=contact,
                role=role,
                is_active=True,
            )

            if role == 'FOOD_BUSINESS':
                FoodBusiness.objects.create(
                    user=user, business_name=f'{first_name} Business',
                    business_type='Restaurant', contact_person=f'{first_name} {last_name or ""}'.strip(),
                    contact=contact, address=address, city=city, pincode=pincode,
                )
            elif role == 'NGO':
                NGO.objects.create(
                    user=user, organization_name=f'{first_name} NGO', receiver_type='NGO',
                    contact_person=f'{first_name} {last_name or ""}'.strip(), contact=contact,
                    address=address, city=city, pincode=pincode, capacity=1,
                )
            elif role == 'CUSTOMER':
                Customer.objects.create(user=user, address=address, city=city, pincode=pincode)
            elif role == 'VOLUNTEER':
                Volunteer.objects.create(user=user, service_area=city)

            messages.success(request, 'Account created successfully. Please log in.')
            return redirect('login')

        for error in errors:
            messages.error(request, error)

    return render(request, 'register.html')


@admin_required
def admin_dashboard(request):
    admin_obj = request.admin_obj
    context = {
        'admin_obj': admin_obj,
        'is_super_admin': admin_obj.role == 'SUPER_ADMIN',
        'total_users': User.objects.count(),
        'total_admins': Admin.objects.count(),
        'total_food_businesses': FoodBusiness.objects.count(),
        'total_ngos': NGO.objects.count(),
        'total_customers': Customer.objects.count(),
        'total_volunteers': Volunteer.objects.count(),
        'total_food_items': FoodItem.objects.count(),
        'total_requests': FoodRequest.objects.count(),
        'total_matches': Match.objects.count(),
        'total_pickups': Pickup.objects.count(),
        'total_deliveries': Delivery.objects.count(),
        'total_notifications': Notification.objects.count(),
        'unread_notifications': Notification.objects.filter(is_read=False).count(),
        'active_users': User.objects.filter(is_active=True).count(),
        'active_deliveries': Delivery.objects.exclude(status__in=['DELIVERED', 'COMPLETED', 'CANCELLED']).count(),
        'available_food': FoodItem.objects.filter(status='AVAILABLE').count(),
        'pending_requests': FoodRequest.objects.filter(status='PENDING').count(),
        'approved_matches': Match.objects.filter(status='ACCEPTED').count(),
        'recent_users': User.objects.order_by('-created_at')[:5],
        'recent_food': FoodItem.objects.select_related('provider').order_by('-created_at')[:5],
        'recent_requests': FoodRequest.objects.select_related('food', 'requester_user').order_by('-requested_at')[:5],
        'recent_notifications': Notification.objects.select_related('user').order_by('-created_at')[:5],
    }
    return render(request, 'admin/dashboard-admin.html', context)


# -----------------------------------------------------------------------------
# Public/role dashboards
# -----------------------------------------------------------------------------

def home(request):
    return render(request, 'index.html')


@user_required
def role_dashboard(request):
    role_templates = {
        'FOOD_BUSINESS': 'business/dashboard-business.html',
        'NGO': 'ngo/dashboard-ngo.html',
        'CUSTOMER': 'customer/dashboard-customer.html',
        'VOLUNTEER': 'volunteer/dashboard-volunteer.html',
    }
    template = role_templates.get(request.user.role, 'index.html')
    return render(request, template, {'user_obj': request.user})


def track(request):
    return render(request, 'track.html')


# -----------------------------------------------------------------------------
# Generic admin CRUD helpers
# -----------------------------------------------------------------------------

MODEL_CONFIG = {
    'admins': (Admin, 'Admin Management', 'admins'),
    'users': (User, 'User Management', 'users'),
    'food_businesses': (FoodBusiness, 'Food Provider Management', 'food_businesses'),
    'ngos': (NGO, 'NGO Management', 'ngos'),
    'customers': (Customer, 'Customer Management', 'customers'),
    'volunteers': (Volunteer, 'Volunteer Management', 'volunteers'),
    'food_items': (FoodItem, 'Surplus Food Management', 'food_items'),
    'food_eligibility': (FoodEligibility, 'Food Eligibility', 'food_eligibility'),
    'food_requests': (FoodRequest, 'Food Requests', 'food_requests'),
    'matches': (Match, 'Matching', 'matches'),
    'pickups': (Pickup, 'Pickup Management', 'pickups'),
    'deliveries': (Delivery, 'Delivery Management', 'deliveries'),
    'notifications': (Notification, 'Notifications', 'notifications'),
    'analytics': (Analytics, 'Analytics', 'analytics'),
}


def _model_fields(model, include_password=True):
    result = []
    for field in model._meta.fields:
        if field.primary_key or field.auto_created:
            continue
        if field.name in {'created_at', 'updated_at', 'checked_at', 'requested_at', 'matched_at'}:
            continue
        result.append(field)
    return result


def _field_value(obj, field):
    value = getattr(obj, field.name, '')
    if value is None:
        return ''
    return value


def _field_choices(field):
    return list(field.choices or [])


def _set_model_value(obj, field, raw_value):
    from django.db import models as db_models
    if isinstance(field, (db_models.ForeignKey, db_models.OneToOneField)):
        if raw_value in ('', None):
            setattr(obj, field.name, None)
            return
        related_model = field.remote_field.model
        setattr(obj, field.name, related_model.objects.get(pk=int(raw_value)))
    elif isinstance(field, db_models.BooleanField):
        setattr(obj, field.name, str(raw_value).lower() in {'1', 'true', 'on', 'yes'})
    elif isinstance(field, (db_models.IntegerField, db_models.BigIntegerField, db_models.PositiveIntegerField)):
        setattr(obj, field.name, int(raw_value) if raw_value not in ('', None) else None)
    elif isinstance(field, db_models.DecimalField):
        from decimal import Decimal
        setattr(obj, field.name, Decimal(raw_value) if raw_value not in ('', None) else None)
    elif isinstance(field, db_models.DateTimeField):
        from django.utils.dateparse import parse_datetime
        value = parse_datetime(raw_value) if raw_value else None
        if value is None and raw_value:
            raise ValueError(f'Invalid date/time for {field.verbose_name}.')
        setattr(obj, field.name, value)
    elif isinstance(field, db_models.DateField):
        from django.utils.dateparse import parse_date
        value = parse_date(raw_value) if raw_value else None
        setattr(obj, field.name, value)
    else:
        setattr(obj, field.name, raw_value.strip() if isinstance(raw_value, str) else raw_value)


def _form_fields(model, obj=None):
    fields = []
    for field in _model_fields(model):
        item = {
            'name': field.name,
            'label': field.verbose_name.replace('_', ' ').title(),
            'required': not field.blank and not field.null and not getattr(field, 'default', None) is not None,
            'value': _field_value(obj, field) if obj else (field.default if field.default is not None and field.default is not field.empty else ''),
            'choices': _field_choices(field),
            'is_bool': field.get_internal_type() == 'BooleanField',
            'is_fk': field.is_relation and field.remote_field is not None,
            'is_datetime': field.get_internal_type() == 'DateTimeField',
            'is_date': field.get_internal_type() == 'DateField',
            'is_textarea': field.get_internal_type() in {'TextField'} or field.max_length and field.max_length > 180,
            'related_objects': [],
        }
        if field.name == 'password' and obj is not None:
            item['required'] = False
        if item['is_fk']:
            related_model = field.remote_field.model
            item['related_objects'] = related_model.objects.all().order_by('pk')[:500]
            if obj:
                item['value'] = getattr(obj, field.name + '_id', '')
        fields.append(item)
    return fields


def _crud_list(request, key):
    model, title, _ = MODEL_CONFIG[key]
    qs = model.objects.all().order_by('-pk')
    search = request.GET.get('q', '').strip()
    if search:
        text_fields = [f.name for f in model._meta.fields if f.get_internal_type() in {'CharField', 'EmailField', 'TextField'}]
        q = Q()
        for name in text_fields:
            q |= Q(**{f'{name}__icontains': search})
        if q.children:
            qs = qs.filter(q)

    paginator = Paginator(qs, 10)
    page_obj = paginator.get_page(request.GET.get('page', 1))
    fields = _model_fields(model, include_password=False)
    rows = []
    for obj in page_obj.object_list:
        rows.append({
            'object': obj,
            'values': [getattr(obj, field.name, '') for field in fields],
        })
    return render(request, 'admin/crud_list.html', {
        'title': title,
        'model_key': key,
        'model': model,
        'objects': page_obj,
        'rows': rows,
        'search': search,
        'count': model.objects.count(),
        'fields': fields,
        'can_create': key not in {'food_eligibility'},
        'is_super_admin': request.admin_obj.role == 'SUPER_ADMIN',
    })


def _crud_edit(request, key, object_id=None):
    model, title, _ = MODEL_CONFIG[key]
    obj = get_object_or_404(model, pk=object_id) if object_id else model()
    fields = _model_fields(model)

    if model is Admin and object_id and request.admin_obj.role != 'SUPER_ADMIN' and obj.role == 'SUPER_ADMIN':
        return JsonResponse({'error': 'Only Super Admin can edit Super Admin accounts.'}, status=403)

    if request.method == 'POST':
        errors = []
        for field in fields:
            if field.name not in request.POST:
                continue
            raw = request.POST.get(field.name)
            if field.name == 'password' and raw == '':
                continue
            if field.name == 'is_active' and model is Admin and request.admin_obj.id == obj.pk:
                # An administrator cannot accidentally deactivate their own session.
                raw = 'on'
            if not raw and not field.blank and not field.null and not field.has_default():
                errors.append(f'{field.verbose_name.title()} is required.')
                continue
            try:
                _set_model_value(obj, field, raw)
            except Exception as exc:
                errors.append(str(exc))

        if model is Admin:
            if request.admin_obj.role != 'SUPER_ADMIN' and request.POST.get('role') == 'SUPER_ADMIN':
                errors.append('Only Super Admin can assign the SUPER_ADMIN role.')
            raw_password = request.POST.get('password', '')
            if raw_password:
                if len(raw_password) < 8:
                    errors.append('Password must be at least 8 characters.')
                else:
                    obj.password = make_password(raw_password)
            elif not object_id:
                errors.append('Password is required when creating an admin.')

        if model is User:
            raw_password = request.POST.get('password', '')
            if raw_password:
                if len(raw_password) < 8:
                    errors.append('Password must be at least 8 characters.')
                else:
                    obj.set_password(raw_password)
            elif not object_id:
                errors.append('Password is required when creating a user.')

        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            obj.save()
            messages.success(request, f'{title[:-1] if title.endswith("s") else title} saved successfully.')
            redirect_names = {
                'admins': 'admin_list', 'users': 'user_list', 'food_businesses': 'food_business_list',
                'ngos': 'ngo_list', 'customers': 'customer_list', 'volunteers': 'volunteer_list',
                'food_items': 'food_item_list', 'food_eligibility': 'food_eligibility_list',
                'food_requests': 'food_request_list', 'matches': 'match_list', 'pickups': 'pickup_list',
                'deliveries': 'delivery_list', 'notifications': 'notification_list', 'analytics': 'analytics_list',
            }
            return redirect(redirect_names[key])

    return render(request, 'admin/crud_edit.html', {
        'title': title,
        'model_key': key,
        'object': obj,
        'fields': _form_fields(model, obj if object_id else None),
        'is_create': object_id is None,
        'is_super_admin': request.admin_obj.role == 'SUPER_ADMIN',
    })


def _crud_delete(request, key, object_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required.'}, status=405)
    model, title, _ = MODEL_CONFIG[key]
    obj = get_object_or_404(model, pk=object_id)
    if model is Admin and obj.pk == request.admin_obj.pk:
        return JsonResponse({'error': 'You cannot delete your own admin session.'}, status=400)
    if model is Admin and request.admin_obj.role != 'SUPER_ADMIN':
        return JsonResponse({'error': 'Only Super Admin can delete admin accounts.'}, status=403)
    obj.delete()
    return JsonResponse({'success': True})


# -----------------------------------------------------------------------------
# Named CRUD views used by the dashboard and existing links
# -----------------------------------------------------------------------------

@admin_required
def admin_list(request): return _crud_list(request, 'admins')
@admin_required
def admin_edit(request, admin_id): return _crud_edit(request, 'admins', admin_id)
@admin_required
def admin_create(request):
    if request.admin_obj.role != 'SUPER_ADMIN':
        return JsonResponse({'error': 'Only Super Admin can create admin accounts.'}, status=403)
    return _crud_edit(request, 'admins')
@admin_required
def admin_delete(request, admin_id): return _crud_delete(request, 'admins', admin_id)

@admin_required
def user_list(request): return _crud_list(request, 'users')
@admin_required
def user_edit(request, user_id): return _crud_edit(request, 'users', user_id)
@admin_required
def user_delete(request, user_id): return _crud_delete(request, 'users', user_id)
@admin_required
def user_toggle_status(request, user_id):
    if request.method != 'POST': return JsonResponse({'error': 'POST required.'}, status=405)
    obj = get_object_or_404(User, pk=user_id)
    obj.is_active = not obj.is_active
    obj.save(update_fields=['is_active', 'updated_at'])
    return JsonResponse({'success': True, 'is_active': obj.is_active})


def _profile_crud(key):
    @admin_required
    def list_view(request): return _crud_list(request, key)
    @admin_required
    def edit_view(request, object_id): return _crud_edit(request, key, object_id)
    @admin_required
    def delete_view(request, object_id): return _crud_delete(request, key, object_id)
    return list_view, edit_view, delete_view

food_business_list, food_business_edit, food_business_delete = _profile_crud('food_businesses')
ngo_list, ngo_edit, ngo_delete = _profile_crud('ngos')
customer_list, customer_edit, customer_delete = _profile_crud('customers')
volunteer_list, volunteer_edit, volunteer_delete = _profile_crud('volunteers')
food_item_list, food_item_edit, food_item_delete = _profile_crud('food_items')
food_eligibility_list, food_eligibility_edit, food_eligibility_delete = _profile_crud('food_eligibility')
food_request_list, food_request_edit, food_request_delete = _profile_crud('food_requests')
match_list, match_edit, match_delete = _profile_crud('matches')
pickup_list, pickup_edit, pickup_delete = _profile_crud('pickups')
delivery_list, delivery_edit, delivery_delete = _profile_crud('deliveries')
notification_list, _notification_edit, notification_delete = _profile_crud('notifications')

@admin_required
def notification_add(request):
    object_id = request.GET.get('id')
    return _crud_edit(request, 'notifications', object_id) if object_id else _crud_edit(request, 'notifications')
analytics_list, analytics_edit, analytics_delete = _profile_crud('analytics')


@admin_required
def food_item_add(request):
    return _crud_edit(request, 'food_items')


@admin_required
def notification_mark_read(request, notification_id):
    if request.method != 'POST': return JsonResponse({'error': 'POST required.'}, status=405)
    obj = get_object_or_404(Notification, pk=notification_id)
    obj.is_read = True
    obj.save(update_fields=['is_read'])
    return JsonResponse({'success': True})
