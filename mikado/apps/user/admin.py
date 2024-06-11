from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from oscar.apps.customer.forms import PhoneUserCreationForm, UserForm
from oscar.core.loading import get_model

User = get_model("user", "User")

class CustomUserAdmin(UserAdmin):
    add_form = PhoneUserCreationForm
    form = UserForm
    model = User
    list_display = ('username', 'is_staff', 'is_active',)
    list_filter = ('username', 'is_staff', 'is_active',)
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Permissions', {'fields': ('is_staff', 'is_active')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'is_staff', 'is_active')}
        ),
    )
    search_fields = ('username',)
    ordering = ('username',)


admin.site.register(User, CustomUserAdmin)