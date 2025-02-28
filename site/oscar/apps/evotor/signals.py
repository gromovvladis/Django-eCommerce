import django.dispatch

send_evotor_category = django.dispatch.Signal()
send_evotor_product = django.dispatch.Signal()
send_evotor_additional = django.dispatch.Signal()

send_evotor_categories = django.dispatch.Signal()
send_evotor_products = django.dispatch.Signal()
send_evotor_additionals = django.dispatch.Signal()

update_evotor_stockrecord = django.dispatch.Signal()

delete_evotor_category = django.dispatch.Signal()
delete_evotor_product = django.dispatch.Signal()
delete_evotor_additional = django.dispatch.Signal()

update_site_stores = django.dispatch.Signal()
update_site_terminals = django.dispatch.Signal()
update_site_staffs = django.dispatch.Signal()
update_site_groups = django.dispatch.Signal()
update_site_products = django.dispatch.Signal()
update_site_additionals = django.dispatch.Signal()
