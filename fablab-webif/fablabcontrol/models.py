# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import models
from django.conf import settings
from django.utils.encoding import python_2_unicode_compatible
import datetime
import os

@python_2_unicode_compatible
class Briefing(models.Model):
    name = models.CharField(max_length=200, verbose_name='Briefing')
    description = models.TextField(null=True, blank=True, verbose_name='Description')

    def __str__(self):
        return '%s' % (self.name)

    def __unicode__(self):
        return u'%s' % (self.name)


@python_2_unicode_compatible
class BriefingDocument(models.Model):
    file = models.FileField(upload_to='briefings/')
    briefing = models.ForeignKey(
        Briefing,
        on_delete=models.CASCADE,
        related_name='documents',
    )

    def __str__(self):
        return '%s' % (self.file.url)

    def __unicode__(self):
        return u'%s' % (self.file.url)

    def delete(self):
        os.remove(settings.MEDIA_ROOT + 'briefings/' + self.file.path)
        return super(BriefingDocument, self).delete()


def get_path_and_name_for_picture(instance, filename):
    ext = filename.split('.')[1]
    new_name = 'user_images/%s.%s' % (instance.user.id, ext)
    return new_name


@python_2_unicode_compatible
class FabLabUser(models.Model):
    rfid_uuid = models.CharField(max_length=14, unique=True, verbose_name='RFID UUID')
    image = models.ImageField(
        upload_to=get_path_and_name_for_picture,
        default='user_images/no-img.jpg',
        verbose_name='Image')
    briefings = models.ManyToManyField(
        Briefing,
        blank=True,
        verbose_name='Briefings',
        related_name='users')
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return '%s %s %s' % (self.user.first_name, self.user.last_name, self.rfid_uuid)

    def __unicode__(self):
        return u'%s %s %s' % (self.user.first_name, self.user.last_name, self.rfid_uuid)

    def delete(self):
        os.remove(settings.MEDIA_ROOT + 'user_images/' + self.image.path)
        return super(BriefingDocument, self).delete()


#@python_2_unicode_compatible
# class NewMachine(models.Model):
#    name = models.CharField(max_length=200, unique=True, verbose_name='Machine name')
#    users = models.ManyToManyField(FabLabUser,  blank=True,  verbose_name='Assigned users', related_name='machines')
#    category  = models.CharField(max_length=200, blank=True, verbose_name='Category')
#    location = models.CharField(max_length=200,  blank=True,  verbose_name='Location')
#    description = models.TextField(null=True, blank=True, verbose_name='Description')
#
#    def __str__(self):
#       return '%s' % self.name
#
#    def __unicode__(self):
#        return u'%s' % self.name
#
# class NewMachineForm(forms.ModelForm):
#    class Meta:
#        model = NewMachine
#        fields =  '__all__'
#
#
#


@python_2_unicode_compatible
class Machine(models.Model):
    name = models.CharField(max_length=200, unique=True, verbose_name='Machine name')
#    circle_mac = models.CharField(max_length=16 , unique=True, verbose_name='Plugwise Circle MAC')
#    circle_status = models.CharField(max_length=16, blank=True, verbose_name='Circle status')
#    esp_mac = models.CharField(max_length=12,  unique=True, verbose_name='ESP Controller MAC')
#    esp_status = models.CharField(max_length=16, blank=True, verbose_name='ESP status')
    users = models.ManyToManyField(
        FabLabUser,
        blank=True,
        verbose_name='Assigned users',
        related_name='machines')
    user = models.ForeignKey(
        FabLabUser,
        on_delete=models.CASCADE,
        related_name='logged_in',
        blank=True,
        null=True,
        verbose_name='Current user')
    category = models.CharField(max_length=200, blank=True, verbose_name='Category')
#    loginterval = models.IntegerField( blank=True,  verbose_name='Log interval in min.')
#    always_on = models.BooleanField(blank=True,  verbose_name='Always on')
    location = models.CharField(max_length=200, blank=True, verbose_name='Location')
#    monitor = models.BooleanField(blank=True,  default=True , verbose_name='Monitor (10s)')
    description = models.TextField(null=True, blank=True, verbose_name='Description')

    def __str__(self):
        return '%s' % self.name

    def __unicode__(self):
        return u'%s' % self.name


@python_2_unicode_compatible
class PlugwiseCircle(models.Model):
    machine = models.ForeignKey(
        Machine,
        on_delete=models.CASCADE,
        related_name='circles',
    )
    mac = models.CharField(max_length=16, unique=True, verbose_name='Plugwise Circle MAC')
    status = models.CharField(max_length=16, blank=True, verbose_name='Circle status', default='Offline')
    loginterval = models.IntegerField(blank=True, verbose_name='Log interval in min.')
    always_on = models.BooleanField(blank=True, verbose_name='Always on', default=False)
    monitor = models.BooleanField(blank=True, default=True, verbose_name='Monitor (10s)')
    production = models.BooleanField(
        blank=True,
        default=False,
        verbose_name='Energy producer')
    schedule_state = models.CharField(
        blank=True,
        default='off',
        max_length=3,
        verbose_name='Schedule state')
    schedule = models.CharField(blank=True, default='', max_length=16, verbose_name='Schedule')
    savelog = models.BooleanField(
        blank=True,
        default=True,
        verbose_name='Save energy log')

    def __str__(self):
        return '%s' % self.mac

    def __unicode__(self):
        return u'%s' % self.mac


@python_2_unicode_compatible
class ESP(models.Model):
    machine = models.ForeignKey(
        Machine,
        on_delete=models.CASCADE,
        related_name='esps',
        blank=True,
        null=True)
    mac = models.CharField(max_length=12, unique=True, verbose_name='ESP MAC')

    def __str__(self):
        return '%s' % self.mac

    def __unicode__(self):
        return u'%s' % self.mac


@python_2_unicode_compatible
class EnergyMonitor(models.Model):
    date = models.DateTimeField(verbose_name='Date', )
    power = models.DecimalField(
        max_digits=12,
        decimal_places=6,
        verbose_name='Consumed energy in W/h',
    )
    interval = models.IntegerField(verbose_name='Log interval in min.', )
    circle = models.ForeignKey(
        PlugwiseCircle,
        on_delete=models.CASCADE,
        related_name='energy',
        null=True,
    )
    machine = models.ForeignKey(
        Machine,
        on_delete=models.CASCADE,
        related_name='energy',
    )

    def __str__(self):
        return '%s-%s-%s' % (self.machine.name,
                             self.date.strftime("%Y-%m-%d %H:%M:%S"), str(self.power))

    def __unicode__(self):
        return u'%s-%s-%s' % (self.machine.name,
                              self.date.strftime("%Y-%m-%d %H:%M:%S"), str(self.power))


@python_2_unicode_compatible
class UserActivityMonitor(models.Model):
    user = models.ForeignKey(
        FabLabUser,
        on_delete=models.CASCADE,
        related_name='activities',
    )
    machine = models.ForeignKey(
        Machine,
        on_delete=models.CASCADE,
        related_name='activities',
    )
    datestart = models.DateTimeField(verbose_name='Work begin')
    datestop = models.DateTimeField(null=True, blank=True, verbose_name='Work end')
    description = models.TextField(null=True, blank=True, verbose_name='Description')

    def __str__(self):
        return '%s-%s-%s' % (self.machine.name,
                             self.datestart.strftime("%Y-%m-%d %H:%M:%S"), str(self.user))

    def __unicode__(self):
        return u'%s-%s-%s' % (self.machine.name,
                              self.datestart.strftime("%Y-%m-%d %H:%M:%S"), str(self.user))


def get_path_and_name_for_activity_doc(instance, filename):
    new_name = 'activity_images/%s/%s' % (instance.activity.id, filename)
    return new_name


@python_2_unicode_compatible
class ActivityDocument(models.Model):
    file = models.FileField(upload_to=get_path_and_name_for_activity_doc)
    activity = models.ForeignKey(
        UserActivityMonitor,
        on_delete=models.CASCADE,
        related_name='documents')

    def __str__(self):
        return '%s' % (self.file.url)

    def __unicode__(self):
        return u'%s' % (self.file.url)

    def delete(self):
        os.remove(settings.MEDIA_ROOT + 'activity_images/' + self.file.path)
        return super(ActivityDocument, self).delete()


@python_2_unicode_compatible
class Maintenance(models.Model):
    user = models.ForeignKey(
        FabLabUser,
        on_delete=models.CASCADE,
        related_name='maintenances',
        blank=True)
    machine = models.ForeignKey(
        Machine,
        on_delete=models.CASCADE,
        related_name='maintenances',
    )
    scheduled = models.DateTimeField(blank=True, null=True, verbose_name='Scheduled for')
    duration = models.TimeField(blank=True, null=True, verbose_name='Planned duration')
    start = models.DateTimeField(null=True, blank=True, verbose_name='Work begin')
    stop = models.DateTimeField(null=True, blank=True, verbose_name='Work end')
    todo = models.CharField(max_length=300, null=True, blank=True, verbose_name='ToDo')
    done = models.TextField(null=True, blank=True, verbose_name='Done')

    def __str__(self):
        return '%s-%s-%s' % (self.machine.name,
                             self.datestart.strftime("%Y-%m-%d %H:%M:%S"), str(self.user))

    def __unicode__(self):
        return u'%s-%s-%s' % (self.machine.name,
                              self.datestart.strftime("%Y-%m-%d %H:%M:%S"), str(self.user))


def get_path_and_name_for_maintenance_doc(instance, filename):
    new_name = 'maintenance/%s/%s' % (instance.maintenance.id, filename)
    return new_name


@python_2_unicode_compatible
class MaintenanceDocument(models.Model):
    file = models.FileField(upload_to=get_path_and_name_for_maintenance_doc)
    maintenance = models.ForeignKey(
        Maintenance,
        on_delete=models.CASCADE,
        related_name='documents')

    def __str__(self):
        return '%s' % (self.file.url)

    def __unicode__(self):
        return u'%s' % (self.file.url)
