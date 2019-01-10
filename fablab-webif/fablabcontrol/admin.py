from django.contrib import admin

from .models import FabLabUser, Machine, EnergyMonitor, ActivityDocument, Briefing, BriefingDocument, PlugwiseCircle, ESP, UserActivityMonitor
admin.site.register(PlugwiseCircle)
admin.site.register(ESP)
admin.site.register(Machine)
admin.site.register(FabLabUser)
admin.site.register(EnergyMonitor)
admin.site.register(UserActivityMonitor)
admin.site.register(ActivityDocument)
admin.site.register(Briefing)
admin.site.register(BriefingDocument)
