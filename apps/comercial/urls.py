from django.urls import path
from django.contrib.auth.decorators import login_required
from apps.comercial.views import *
from apps.comercial.view_passenger import *
from apps.comercial.views_PDF import print_ticket_order_commodity, print_ticket_order_passenger, \
    print_bill_order_commodity, print_manifest_passengers, print_mock_up_passengers, print_manifest_comidity, \
    print_guide_comidity, print_ticket_old, print_manifest_passengers_old, print_report_commodity, \
    print_report_receive_commodity

urlpatterns = [
    path('', login_required(Index.as_view()), name='index'),
    # truck
    path('truck_list/', login_required(TruckList.as_view()), name='truck_list'),
    path('truck_create/', login_required(TruckCreate.as_view()), name='truck_create'),
    path('truck_update/<int:pk>/', login_required(TruckUpdate.as_view()), name='truck_update'),
    # pilot associated to truck
    path('get_truck/', login_required(get_truck), name='get_truck'),
    path('new_pilot_associate/', login_required(new_pilot_associate), name='new_pilot_associate'),
    path('get_pilots_associated/', login_required(get_pilots_associated), name='get_pilots_associated'),
    # towing
    path('towing_list/', login_required(TowingList.as_view()), name='towing_list'),
    path('towing_create/', login_required(TowingCreate.as_view()), name='towing_create'),
    path('towing_update/<int:pk>/', login_required(TowingUpdate.as_view()), name='towing_update'),
    # programming
    path('programming_list/', login_required(ProgrammingList.as_view()), name='programming_list'),
    path('programming_create/', login_required(ProgrammingCreate.as_view()), name='programming_create'),
    path('new_programming/', new_programming, name='new_programming'),
    path('get_programming/', get_programming, name='get_programming'),
    path('update_programming/', update_programming, name='update_programming'),
    # guide
    path('new_guide/', new_guide, name='new_guide'),
    path('get_programming_guide/', get_programming_guide, name='get_programming_guide'),
    path('get_quantity_product/', get_quantity_product, name='get_quantity_product'),
    path('create_order/', create_order, name='create_order'),
    path('guide_detail_list/', guide_detail_list, name='guide_detail_list'),
    path('guide_by_programming/', guide_by_programming, name='guide_by_programming'),
    path('programmings_by_date/', programmings_by_date, name='programmings_by_date'),
    path('programming_receive_by_sucursal/', programming_receive_by_sucursal,
         name='programming_receive_by_sucursal'),
    path('programming_receive_by_sucursal_detail_guide/', programming_receive_by_sucursal_detail_guide,
         name='programming_receive_by_sucursal_detail_guide'),
    path('get_stock_by_store/', get_stock_by_store, name='get_stock_by_store'),
    path('update_stock_from_programming/', update_stock_from_programming,
         name='update_stock_from_programming'),

    # IO guides
    path('get_address_subsidiary_by_id/', get_address_subsidiary_by_id, name='get_address_subsidiary_by_id'),

    # ReportLab
    path('print_ticket_order_commodity/<int:pk>/', print_ticket_order_commodity, name='print_ticket_order_commodity'),
    path('print_ticket_order_passenger/<int:pk>/', print_ticket_order_passenger, name='print_ticket_order_passenger'),
    path('print_bill_order_commodity/<int:pk>/', print_bill_order_commodity, name='print_bill_order_commodity'),
    path('print_manifest_passengers/<int:pk>/', print_manifest_passengers, name='print_manifest_passengers'),
    path('print_mock_up_passengers/<int:pk>/', print_mock_up_passengers, name='print_mock_up_passengers'),
    path('print_manifest_comidity/<int:pk>/', print_manifest_comidity, name='print_manifest_comidity'),
    path('print_guide_comidity/<int:pk>/', print_guide_comidity, name='print_guide_comidity'),
    path('print_ticket_old/<int:pk>/', print_ticket_old, name='print_ticket_old'),
    path('print_manifest_passengers_old/<int:pk>/', print_manifest_passengers_old, name='print_manifest_passengers_old'),
    path('print_report_commodity/<str:start_date>/<str:end_date>/<int:user_type>/<str:way_to_pay>/<str:destiny>', print_report_commodity, name='print_report_commodity'),
    path('print_report_receive_commodity/<str:start_date>/<str:end_date>', print_report_receive_commodity, name='print_report_receive_commodity'),

    # plan
    path('truck_plan/', login_required(truck_plan), name='truck_plan'),
    path('truck_plan/<int:pk>/', login_required(truck_plan), name='truck_plan'),
    path('fill_form_programming_seat/', login_required(fill_form_programming_seat),
         name='fill_form_programming_seat'),
    path('get_correlative_document/', login_required(get_correlative_document),
         name='get_correlative_document'),
    path('get_correlative_document_commodity/', login_required(get_correlative_document_commodity),
         name='get_correlative_document_commodity'),
    path('get_rendered_seat/', login_required(get_rendered_seat), name='get_rendered_seat'),
    path('get_programming_seat_of_programming/', login_required(get_programming_seat_of_programming), name='get_programming_seat_of_programming'),


    path('go_processing_of_sale/', login_required(go_processing_of_sale), name='go_processing_of_sale'),
    path('go_selling_with_destination_limit/', login_required(go_selling_with_destination_limit), name='go_selling_with_destination_limit'),
    path('go_release_seat/', login_required(go_release_seat), name='go_release_seat'),
    path('go_reserve_seat_with_name/', login_required(go_reserve_seat_with_name), name='go_reserve_seat_with_name'),
    path('go_reserve_seat_without_name/', login_required(go_reserve_seat_without_name), name='go_reserve_seat_without_name'),
    path('go_cancellation_of_sale/', login_required(go_cancellation_of_sale), name='go_cancellation_of_sale'),
    path('go_postponement_of_sale/', login_required(go_postponement_of_sale), name='go_postponement_of_sale'),
    path('go_release_seat_with_destination_limit/', login_required(go_release_seat_with_destination_limit), name='go_release_seat_with_destination_limit'),

    # query dni
    path('get_name_business/', login_required(get_name_business), name='get_name_business'),
    # path
    path('get_path_list/', login_required(get_path_list), name='get_path_list'),
    path('get_create_path_form/', login_required(get_create_path_form), name='get_create_path_form'),
    path('new_path/', login_required(new_path), name='new_path'),
    path('get_path/', login_required(get_path), name='get_path'),
    path('update_path/', login_required(update_path), name='update_path'),
    path('delete_path/', login_required(delete_path), name='delete_path'),
    # road
    path('get_create_road_form/', login_required(get_create_road_form), name='get_create_road_form'),
    path('new_road/', login_required(new_road), name='new_road'),
    path('get_road/', login_required(get_road), name='get_road'),
    path('update_road/', login_required(update_road), name='update_road'),
    path('delete_road/', login_required(delete_road), name='delete_road'),

    # destiny
    path('get_create_destiny_form/', login_required(get_create_destiny_form), name='get_create_destiny_form'),
    path('new_destiny/', login_required(new_destiny), name='new_destiny'),
    path('get_destiny/', login_required(get_destiny), name='get_destiny'),
    path('update_destiny/', login_required(update_destiny), name='update_destiny'),
    path('delete_destiny/', login_required(delete_destiny), name='delete_destiny'),

    # associate
    path('get_create_associate_subsidiary_form/', login_required(get_create_associate_subsidiary_form), name='get_create_associate_subsidiary_form'),
    path('new_associate_subsidiary/', login_required(new_associate_subsidiary), name='new_associate_subsidiary'),
    path('get_associate_subsidiary/', login_required(get_associate_subsidiary), name='get_associate_subsidiary'),
    path('delete_associate_subsidiary/', login_required(delete_associate_subsidiary), name='delete_associate_subsidiary'),

    # passengers
    path('create_order_passenger/', login_required(create_order_passenger), name='create_order_passenger'),
    path('get_ticket_inquiry_list/', login_required(get_ticket_inquiry_list), name='get_ticket_inquiry_list'),
    path('get_manifest_passenger_inquiry_list/', login_required(get_manifest_passenger_inquiry_list), name='get_manifest_passenger_inquiry_list'),

    # manifest
    path('manifest_comodity_list/', login_required(manifest_comodity_list), name='manifest_comodity_list'),
    path('get_programming_manifest/', login_required(get_programming_manifest), name='get_programming_manifest'),
    path('add_order_to_order_programming/', login_required(add_order_to_order_programming), name='add_order_to_order_programming'),
    path('remove_order_to_order_programming/', login_required(remove_order_to_order_programming), name='remove_order_to_order_programming'),

    # programmings
    path('get_programming_query_list/', login_required(get_programming_query_list), name='get_programming_query_list'),
    path('get_create_legacy_programming_form/', login_required(get_create_legacy_programming_form), name='get_create_legacy_programming_form'),
    path('new_legacy_programming/', login_required(new_legacy_programming), name='new_legacy_programming'),
    path('generate_manifest/', login_required(generate_manifest), name='generate_manifest'),

    # commidity
    path('get_add_detail/', login_required(get_add_detail), name='get_add_detail'),
    path('generate_guide/', login_required(generate_guide), name='generate_guide'),
    path('get_modal_change/', login_required(get_modal_change), name='get_modal_change'),
    path('change_destiny/', login_required(change_destiny), name='change_destiny'),

    # path('report_comodity/', login_required(report_comodity), name='report_comodity'),
    path('report_comodity_grid/', login_required(report_comodity_grid), name='report_comodity_grid'),
    path('cancel_commodity/', login_required(cancel_commodity), name='cancel_commodity'),

    # report_manifest
    path('report_manifest_grid/', login_required(report_manifest_grid), name='report_manifest_grid'),

    # postponements
    path('get_postponements/', login_required(get_postponements), name='get_postponements'),
    path('get_reschedule_form/', login_required(get_reschedule_form), name='get_reschedule_form'),
    path('save_seat_rescheduled/', login_required(save_seat_rescheduled), name='save_seat_rescheduled'),

    # reassigns
    path('get_seat_to_reassign/', login_required(get_seat_to_reassign), name='get_seat_to_reassign'),
    path('save_seat_to_reassign/', login_required(save_seat_to_reassign), name='save_seat_to_reassign'),

    # receive_manifest
    path('receive_manifests/', login_required(receive_manifests), name='receive_manifests'),
    path('change_type_commodity/', login_required(change_type_commodity), name='change_type_commodity'),

    # guide_asign
    path('add_order_to_order_programming_guide/', login_required(add_order_to_order_programming_guide), name='add_order_to_order_programming_guide'),
    path('remove_order_to_order_programming_guide/', login_required(remove_order_to_order_programming_guide), name='remove_order_to_order_programming_guide'),

    # get phone
    path('get_phone_number_by_name_addressee/', login_required(get_phone_number_by_name_addressee), name='get_phone_number_by_name_addressee'),

    # reports
    path('departures_of_month/', login_required(departures_of_month), name='departures_of_month'),
    path('report_expiration_soat_and_technical/', login_required(report_expiration_soat_and_technical), name='report_expiration_soat_and_technical'),

    # modal-way-to-pay
    path('get_modal_way_pay/', login_required(get_modal_way_pay), name='get_modal_way_pay'),
    path('change_way_to_pay/', login_required(change_way_to_pay), name='change_way_to_pay'),

    # modal-delivery
    path('save_delivery_code/', login_required(save_delivery_code), name='save_delivery_code'),
]