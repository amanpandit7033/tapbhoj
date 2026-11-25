from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'^ws/table/(?P<slug>[\w-]+)/(?P<table_number>[\w-]+)/cart/?$', consumers.TableCartConsumer.as_asgi()),
    re_path(r'^ws/dashboard/(?P<slug>[\w-]+)/orders/?$', consumers.RestaurantOrdersConsumer.as_asgi()),
]
