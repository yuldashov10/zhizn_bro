class SystemObjectReadonlyMixin:
    """
    Миксин для защиты системных объектов от редактирования в админке.
    Объект считается системным если is_default=True.

    Использование:
        class MyAdmin(SystemObjectReadonlyMixin, admin.ModelAdmin):
            ...
    """

    def get_readonly_fields(self, request, obj=None):
        if obj and getattr(obj, "is_default", False):
            return [f.name for f in self.model._meta.fields]
        return super().get_readonly_fields(request, obj)
