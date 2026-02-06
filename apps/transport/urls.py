from django.urls import path
from django.contrib.auth.decorators import login_required
from apps.transport.views import *
# from apps.transport.viewsets import *
from rest_framework import routers

router = routers.DefaultRouter()

urlpatterns = [

    # path('api/v1/get_programming_list/', get_programming_list),
    # path('api/v1/get_programming/<int:pk>', get_programming),
    # path('api/v1/get_order_ticket/<int:pk>', get_order_ticket),
    # path('api/v1/get_order_invoice/<int:pk>', get_order_invoice),

    path('programming_list/', login_required(programming_list), name='programming_list'),

    path('truck_plan/', login_required(truck_plan), name='truck_plan'),
    path('truck_plan/<int:pk>/', login_required(truck_plan), name='truck_plan'),

    path('go_processing_of_sale/', login_required(go_processing_of_sale), name='go_processing_of_sale'),
    path('go_release_seat/', login_required(go_release_seat), name='go_release_seat'),
    path('go_cancellation_of_sale/', login_required(go_cancellation_of_sale), name='go_cancellation_of_sale'),
    path('get_seat_to_reassign/', login_required(get_seat_to_reassign), name='get_seat_to_reassign'),
    path('save_seat_to_reassign/', login_required(save_seat_to_reassign), name='save_seat_to_reassign'),
    path('go_reserve_seat_without_name/', login_required(go_reserve_seat_without_name), name='go_reserve_seat_without_name'),
]