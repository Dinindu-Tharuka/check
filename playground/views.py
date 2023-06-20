from django.shortcuts import render
from django.http import HttpResponse
from django.db.models import Q, F, Value, Func, ExpressionWrapper, DecimalField
from django.db.models.aggregates import Count, Max, Min, Avg, Sum
from django.db.models.functions import Concat
from django.db import transaction, connection
from django.contrib.contenttypes.models import ContentType
from mainstore.models import Product, OrderItem, Collection, Promotions, Customer, Order
from tags.models import TaggedItem, Tag


def say_hello(request):

    

    return render(request, 'hello.html')
