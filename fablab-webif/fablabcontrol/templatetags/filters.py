from django import template
register = template.Library()


@register.filter(name='lookup_user_by_uuid')
def lookup_user_by_uuid(fablabusers, uuid):
    for user in fablabusers:
        if user.rfid_uuid == uuid:
            return user
    return None
