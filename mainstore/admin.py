from django.contrib import admin, messages
from django.contrib.contenttypes.admin import GenericTabularInline
from django.db.models.aggregates import Count
from django.db.models.functions import Concat
from django.db.models import Value, F, QuerySet
from django.http import HttpRequest
from django.urls import reverse
from django.utils.html import format_html
from django.utils.http import urlencode
from .models import Cart, Customer, Collection, Order, Product, OrderItem, Promotions, CartItem
from tags.models import Tag, TaggedItem

# Collection
@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = ['title', 'products']
    autocomplete_fields = ['featured_product']
    

    def products(self, collection):

        url = (reverse('admin:mainstore_product_changelist')
               + '?'
               + urlencode({
                    'collection__id':collection.id
               })
               )

        return format_html('<a href="{}">{}</a>', url, collection.product_count)
    
    def get_queryset(self, request: HttpRequest) -> QuerySet:
        return super().get_queryset(request).annotate(
            product_count = Count('product')
        )

# Customer Order Filter
class CustomerorderFilter(admin.SimpleListFilter):
    title = 'Orders Range'
    parameter_name = 'order-range'

    LOW_ORDERS = '<2'
    MIDDLE = '<4'
    HIGH_ORDER = '>4'

    def lookups(self, request, model_admin):
        return [
            (self.LOW_ORDERS, 'low'),
            (self.MIDDLE, 'middle'),
            (self.HIGH_ORDER, 'high')
        ]
    
    def queryset(self, request, queryset: QuerySet):
        if self.value() == self.LOW_ORDERS:
            return queryset.filter(order_count__lt=2)
        elif self.value() == self.MIDDLE:
            return queryset.filter(order_count__lt=4, order_count__gte=2)
        elif self.value() == self.HIGH_ORDER:
            return queryset.filter(order_count__gte=4)

# Customer
@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['customer_name', 'membership', 'orders']
    list_editable = ['membership']
    list_per_page = 15
    list_filter = ['membership', CustomerorderFilter]
    ordering = ['first_name', 'last_name']
    search_fields = ['first_name', 'last_name']

    @admin.display(ordering='full_name')
    def customer_name(self, customer):
        return customer.full_name
    
    @admin.display(ordering='order_count')
    def orders(self, customer):
        return customer.order_count
    
    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            full_name = Concat('first_name', Value(' '), 'last_name'),
            order_count = Count('order')

        )
    

# Order Item Filter
class OrderItemFilter(admin.SimpleListFilter):
    title = 'Items Range'
    parameter_name= 'itemrange'

    LOW_ITEMS = '<200'
    MIDDLE_ITEMS = '<400'
    HIGH_ITEMS = '>400'

    def lookups(self, request, model_admin):
        return [
            (self.LOW_ITEMS, 'low'),
            (self.MIDDLE_ITEMS, 'middle'),
            (self.HIGH_ITEMS, 'high')
        ]
    def queryset(self, request, queryset: QuerySet):
        if self.value() == self.LOW_ITEMS:
            return queryset.filter(quantity__lte=200)
        elif self.value() == self.MIDDLE_ITEMS:
            return queryset.filter(quantity__lte=400, quantity__gt=200)
        elif self.value() == self.HIGH_ITEMS:
            return queryset.filter(quantity__gt=400)
# OrderItem
@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['quantity', 'products']
    list_filter = [OrderItemFilter]
    actions= ['clear_items']
    ordering = ['products']


    @admin.action(description='Remove Items')
    def clear_items(self, request, queryset:QuerySet):
        update_count = queryset.update(quantity=0)

        self.message_user(
            request,
           f'{update_count} orderitems were updated.',
           messages.INFO
           
        )

class OrderIteminline(admin.TabularInline):
    model = OrderItem
    autocomplete_fields = ['products']
    extra = 0


#Order
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['palce_at', 'customer', 'order_items']
    list_per_page = 15
    ordering = ['customer']  
    inlines = [OrderIteminline]
    autocomplete_fields = ['customer']

    @admin.display(ordering='order_items')
    def order_items(self, order):

        url = (reverse('admin:mainstore_orderitem_changelist')
                        + '?'
                        + urlencode({
                                'orders_id': order.id
                        })
                      )

        return format_html('<a href="{}">{}</a>', url, order.order_items)
    
    def get_queryset(self, request: HttpRequest) :
        return super().get_queryset(request).annotate(
            order_items = Count('orderitem')
        )
    


# Product Price Filter
class ProductPriceFilter(admin.SimpleListFilter):
    title = 'Price Range'
    parameter_name = 'price_range'

    LOW_PRICE = '<3000'
    MIDDLE_PRICE = '<4000'
    HIGH_PRICE = '>5000'


    def lookups(self, request, model_admin):
        return [
            (self.LOW_PRICE, 'Low'),
            (self.MIDDLE_PRICE, 'Middle'),
            (self.HIGH_PRICE, 'High')
        ]
    def queryset(self, request, queryset: QuerySet):
        if self.value() == self.LOW_PRICE:
            return queryset.filter(price__lte=3000)
        elif self.value() == self.MIDDLE_PRICE:
            return queryset.filter(price__lt=4000, price__gt=3000)        
        elif self.value() == self.HIGH_PRICE:
            return queryset.filter(price__gt=5000)
        

class ProductInventoryFilter(admin.SimpleListFilter):
    title = 'Inventory'
    parameter_name = 'inventory'

    LOW_INVENTORY = '<300'

    def lookups(self, request, model_admin):
        return [
            (self.LOW_INVENTORY, 'Low')
        ]
    
    def queryset(self, request, queryset: QuerySet):
        if self.value() == self.LOW_INVENTORY:
            return queryset.filter(inventory__lt=300)


class TagInlineProduct(GenericTabularInline):
    model = TaggedItem

# Product
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    #Forms    
    search_fields = ['title']
    prepopulated_fields = {
        'slug':['title']
    }
    autocomplete_fields = ['promotions']

    actions = ['clear_inventory']
    inlines = [TagInlineProduct]
    list_display = ['title', 'collection', 'price', 'inventory']
    list_per_page = 20
    list_filter = ['collection', 'last_update', ProductPriceFilter, ProductInventoryFilter]

    @admin.action(description='clear inventory')
    def clear_inventory(self, request, queryset: QuerySet):

        updated_count = queryset.update(inventory=0)

        self.message_user(
            request,
            f'{updated_count} product were updated.'
        )

# Promotions
@admin.register(Promotions)
class PromotionAdmin(admin.ModelAdmin):
    list_display = ['description']
    list_per_page = 15
    search_fields = ['description']


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['quantity']


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['created_at']

    

    




   
    






    
    

        
    





    
    

    
   

    
    
    




