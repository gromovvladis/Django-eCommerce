import django.dispatch

order_placed = django.dispatch.Signal()

order_status_changed = django.dispatch.Signal()

order_line_status_changed = django.dispatch.Signal()

send_order_to_evotor = django.dispatch.Signal()
