# -*- coding: utf-8 -*-

from django import forms
from .models import FabLabUser, Machine, Briefing
from .models import PlugwiseCircle, Maintenance
from .models import ESP, UserActivityMonitor


# erzeugt das formular für die erstellung und bearbeitung von fablab benutzern
# wird eine user id übergeben werden die felder vorausgefüllt

class UserForm(forms.Form):

    def __init__(self, *args, **kwargs):
        if 'user_id' in kwargs:
            fablabuser = FabLabUser.objects.get(pk=kwargs.pop('user_id'))
        else:
            fablabuser = None

        super(UserForm, self).__init__(*args, **kwargs)

        if fablabuser:
            self.fields['username'] = forms.CharField(
                label='Username', required=True, initial=fablabuser.user.username)
            self.fields['first_name'] = forms.CharField(
                label='First name', required=True, initial=fablabuser.user.first_name)
            self.fields['last_name'] = forms.CharField(
                label='Last name', required=True, initial=fablabuser.user.last_name)
            self.fields['email'] = forms.EmailField(
                label='Email address', required=True, initial=fablabuser.user.email)
            self.fields['rfid_uuid'] = forms.CharField(
                label='RFID UUID', required=True, initial=fablabuser.rfid_uuid, max_length=16)
            self.fields['image'] = forms.ImageField(
                label='Image', required=False, initial=fablabuser.image)
            if fablabuser.user.groups.filter(name='UserActivityGroup').exists():
                self.fields['activity_group'] = forms.BooleanField(
                    label='Track user activity', required=False, initial=True)
            else:
                self.fields['activity_group'] = forms.BooleanField(
                    label='Track user activity', required=False, initial=False)
        else:
            self.fields['username'] = forms.CharField(label='Username', required=True)
            self.fields['first_name'] = forms.CharField(label='First name', required=True)
            self.fields['last_name'] = forms.CharField(label='Last name', required=True)
            self.fields['email'] = forms.EmailField(label='Email address', required=True)
            self.fields['rfid_uuid'] = forms.CharField(
                label='RFID UUID', required=True, max_length=16)
            self.fields['image'] = forms.ImageField(label='Image', required=False)
            self.fields['activity_group'] = forms.BooleanField(
                label='Track user activity', required=False, initial=False)

        self.fields['machine_field'] = forms.MultipleChoiceField(
            required=False,
            widget=forms.SelectMultiple,
            choices=Machine.objects.all().values_list(
                'id',
                'name'),
            label='Assigned to')
        if fablabuser:
            self.fields['machine_field'].initial = (
                fablabuser.machines.all().values_list('id', flat=True))

        self.fields['briefing_field'] = forms.MultipleChoiceField(
            required=False,
            widget=forms.SelectMultiple,
            choices=Briefing.objects.all().values_list(
                'id',
                'name'),
            label='Briefings')
        if fablabuser:
            self.fields['briefing_field'].initial = (
                fablabuser.briefings.all().values_list('id', flat=True))


class PlugwiseCircleForm(forms.ModelForm):

    class Meta:
        model = PlugwiseCircle
        fields = '__all__'


class MaintenanceForm(forms.ModelForm):
    file_field = forms.FileField(
        widget=forms.ClearableFileInput(
            attrs={
                'multiple': True,
            }),
        required=False)

    class Meta:
        model = Maintenance
        fields = '__all__'


class UserActivityForm(forms.ModelForm):
    file_field = forms.FileField(
        widget=forms.ClearableFileInput(
            attrs={
                'multiple': True,
            }),
        required=False, label='Attach Files')

    class Meta:
        model = UserActivityMonitor
        fields = '__all__'


class ESPForm(forms.ModelForm):

    class Meta:
        model = ESP
        fields = '__all__'


class BriefingForm(forms.ModelForm):
    file_field = forms.FileField(
        widget=forms.ClearableFileInput(
            attrs={
                'multiple': True,
            }),
        required=False)

    class Meta:
        model = Briefing
        fields = '__all__'


class MachineForm(forms.ModelForm):

    class Meta:
        model = Machine
        fields = '__all__'
