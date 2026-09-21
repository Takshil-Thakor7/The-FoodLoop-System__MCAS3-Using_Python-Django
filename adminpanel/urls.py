from django.urls import path
from . import views


urlpatterns = [

    # ============================================================
    # ADMIN
    # ============================================================

    path('admins/', views.admin_list, name='admin_list'),
    path('admins/<int:admin_id>/edit/', views.admin_edit, name='admin_edit'),
    path('admins/<int:admin_id>/delete/', views.admin_delete, name='admin_delete'),


    # ============================================================
    # USERS
    # Food Business / NGO / Customer / Volunteer
    # ============================================================

    path('users/', views.user_list, name='user_list'),
    path('users/<int:user_id>/edit/', views.user_edit, name='user_edit'),
    path('users/<int:user_id>/delete/', views.user_delete, name='user_delete'),
    path(
        'users/<int:user_id>/toggle-status/',
        views.user_toggle_status,
        name='user_toggle_status'
    ),


    # ============================================================
    # FOOD BUSINESS
    # ============================================================

    path(
        'food-businesses/',
        views.food_business_list,
        name='food_business_list'
    ),
    path(
        'food-businesses/<int:business_id>/edit/',
        views.food_business_edit,
        name='food_business_edit'
    ),
    path(
        'food-businesses/<int:business_id>/delete/',
        views.food_business_delete,
        name='food_business_delete'
    ),


    # ============================================================
    # NGO
    # ============================================================

    path(
        'ngos/',
        views.ngo_list,
        name='ngo_list'
    ),
    path(
        'ngos/<int:ngo_id>/edit/',
        views.ngo_edit,
        name='ngo_edit'
    ),
    path(
        'ngos/<int:ngo_id>/delete/',
        views.ngo_delete,
        name='ngo_delete'
    ),


    # ============================================================
    # CUSTOMER
    # ============================================================

    path(
        'customers/',
        views.customer_list,
        name='customer_list'
    ),
    path(
        'customers/<int:customer_id>/edit/',
        views.customer_edit,
        name='customer_edit'
    ),
    path(
        'customers/<int:customer_id>/delete/',
        views.customer_delete,
        name='customer_delete'
    ),


    # ============================================================
    # VOLUNTEER
    # ============================================================

    path(
        'volunteers/',
        views.volunteer_list,
        name='volunteer_list'
    ),
    path(
        'volunteers/<int:volunteer_id>/edit/',
        views.volunteer_edit,
        name='volunteer_edit'
    ),
    path(
        'volunteers/<int:volunteer_id>/delete/',
        views.volunteer_delete,
        name='volunteer_delete'
    ),


    # ============================================================
    # FOOD ITEM
    # ============================================================

    path(
        'food-items/',
        views.food_item_list,
        name='food_item_list'
    ),
    path(
        'food-items/add/',
        views.food_item_add,
        name='food_item_add'
    ),
    path(
        'food-items/<int:item_id>/edit/',
        views.food_item_edit,
        name='food_item_edit'
    ),
    path(
        'food-items/<int:item_id>/delete/',
        views.food_item_delete,
        name='food_item_delete'
    ),


    # ============================================================
    # FOOD ELIGIBILITY
    # ============================================================

    path(
        'food-eligibility/',
        views.food_eligibility_list,
        name='food_eligibility_list'
    ),
    path(
        'food-eligibility/<int:eligibility_id>/edit/',
        views.food_eligibility_edit,
        name='food_eligibility_edit'
    ),
    path(
        'food-eligibility/<int:eligibility_id>/delete/',
        views.food_eligibility_delete,
        name='food_eligibility_delete'
    ),


    # ============================================================
    # FOOD REQUEST
    # ============================================================

    path(
        'food-requests/',
        views.food_request_list,
        name='food_request_list'
    ),
    path(
        'food-requests/<int:request_id>/edit/',
        views.food_request_edit,
        name='food_request_edit'
    ),
    path(
        'food-requests/<int:request_id>/delete/',
        views.food_request_delete,
        name='food_request_delete'
    ),


    # ============================================================
    # MATCH
    # ============================================================

    path(
        'matches/',
        views.match_list,
        name='match_list'
    ),
    path(
        'matches/<int:match_id>/edit/',
        views.match_edit,
        name='match_edit'
    ),
    path(
        'matches/<int:match_id>/delete/',
        views.match_delete,
        name='match_delete'
    ),


    # ============================================================
    # PICKUP
    # ============================================================

    path(
        'pickups/',
        views.pickup_list,
        name='pickup_list'
    ),
    path(
        'pickups/<int:pickup_id>/edit/',
        views.pickup_edit,
        name='pickup_edit'
    ),
    path(
        'pickups/<int:pickup_id>/delete/',
        views.pickup_delete,
        name='pickup_delete'
    ),


    # ============================================================
    # DELIVERY
    # ============================================================

    path(
        'deliveries/',
        views.delivery_list,
        name='delivery_list'
    ),
    path(
        'deliveries/<int:delivery_id>/edit/',
        views.delivery_edit,
        name='delivery_edit'
    ),
    path(
        'deliveries/<int:delivery_id>/delete/',
        views.delivery_delete,
        name='delivery_delete'
    ),


    # ============================================================
    # NOTIFICATION
    # ============================================================

    path(
        'notifications/',
        views.notification_list,
        name='notification_list'
    ),
    path(
        'notifications/add/',
        views.notification_add,
        name='notification_add'
    ),
    path(
        'notifications/<int:notification_id>/mark-read/',
        views.notification_mark_read,
        name='notification_mark_read'
    ),
    path(
        'notifications/<int:notification_id>/delete/',
        views.notification_delete,
        name='notification_delete'
    ),


    # ============================================================
    # ANALYTICS
    # ============================================================

    path(
        'analytics/',
        views.analytics_list,
        name='analytics_list'
    ),
    path(
        'analytics/<int:analytics_id>/edit/',
        views.analytics_edit,
        name='analytics_edit'
    ),
    path(
        'analytics/<int:analytics_id>/delete/',
        views.analytics_delete,
        name='analytics_delete'
    ),

]