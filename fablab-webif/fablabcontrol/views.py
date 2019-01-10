# -*- coding: utf-8 -*-
from django.shortcuts import get_object_or_404, render, redirect
from django.core.urlresolvers import reverse
from .forms import UserForm, PlugwiseCircleForm, ESPForm, MaintenanceForm
from .forms import UserActivityForm, BriefingForm, MachineForm
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User, Group
import simplejson as json
from .models import FabLabUser, Machine, UserActivityMonitor, ActivityDocument, EnergyMonitor, Briefing
from .models import BriefingDocument, Maintenance, MaintenanceDocument, PlugwiseCircle, ESP

from django import forms
from django.utils.html import format_html_join
import logging

logger = logging.getLogger('fablab-webif')


def index(request):
    machines = Machine.objects.order_by('-name')[:5]
    users = FabLabUser.objects.order_by('-rfid_uuid')[:5]
    return render(request, 'fablabcontrol/index.html',
                  {'machines': machines, 'users': users, })


def log_in(request):
    form = AuthenticationForm()
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect(reverse('fablabcontrol:index'))
        else:
            render(request, 'fablabcontrol/log_in.html',
                   {'form': form, 'error_message': form.errors})
    return render(request, 'fablabcontrol/log_in.html', {'form': form})


@login_required(login_url='/fablabcontrol/log_in/')
def log_out(request):
    logout(request)
    return redirect(reverse('fablabcontrol:index'))


def circle(request, circle_id):
    circle = get_object_or_404(PlugwiseCircle, pk=circle_id)
    return render(request, 'fablabcontrol/circle.html',
                  {'circle': circle, 'nav_position': "circles"})


def circles(request):
    circles = PlugwiseCircle.objects.all()
    return render(request, 'fablabcontrol/circle.html',
                  {'circles': circles, 'nav_position': "circles"})


@login_required(login_url='/fablabcontrol/log_in/')
def mod_circle(request, circle_id):
    circle = get_object_or_404(PlugwiseCircle, pk=circle_id)
    form = PlugwiseCircleForm(request.POST or None, instance=circle)
    if request.method == "POST":
        if form.is_valid():
            try:
                form.save()
            except Exception as e:
                return render(request, 'fablabcontrol/circle.html', {
                              'circle': circle, 'form': form, 'error_message': str(e), 'nav_position': "circles"})
            return redirect(reverse('fablabcontrol:circles'))
        else:
            return render(request, 'fablabcontrol/circle.html', {
                          'circle': circle, 'form': form, 'error_message': form.errors, 'nav_position': "circles"})
    return render(request, 'fablabcontrol/circle.html',
                  {'circle': circle, 'form': form, 'nav_position': "circles"})


@login_required(login_url='/fablabcontrol/log_in/')
def new_circle(request):
    form = PlugwiseCircleForm(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            try:
                new_circle = form.save()
                new_circle.save()
            except Exception as e:
                return render(request, 'fablabcontrol/circle.html',
                              {'form': form, 'error_message': str(e), 'nav_position': "circles"})
            return redirect(reverse('fablabcontrol:circles'))
        else:
            return render(request, 'fablabcontrol/circle.html',
                          {'form': form, 'error_message': form.errors, 'nav_position': "circles"})
    return render(request, 'fablabcontrol/circle.html',
                  {'form': form, 'nav_position': "circles"})


def esp(request, esp_id):
    esp = get_object_or_404(ESP, pk=esp_id)
    return render(request, 'fablabcontrol/esp.html', {'esp': esp, 'nav_position': "esps"})


def esps(request):
    esps = ESP.objects.all()
    return render(request, 'fablabcontrol/esp.html',
                  {'esps': esps, 'nav_position': "esps"})


@login_required(login_url='/fablabcontrol/log_in/')
def mod_esp(request, esp_id):
    esp = get_object_or_404(ESP, pk=esp_id)
    form = ESPForm(request.POST or None, instance=esp)
    if request.method == "POST":
        if form.is_valid():
            try:
                form.save()
            except Exception as e:
                return render(request, 'fablabcontrol/esp.html',
                              {'esp': esp, 'form': form, 'error_message': str(e), 'nav_position': "esps"})
            return redirect(reverse('fablabcontrol:esps'))
        else:
            return render(request, 'fablabcontrol/esp.html',
                          {'esp': esp, 'form': form, 'error_message': form.errors})
    return render(request, 'fablabcontrol/esp.html',
                  {'esp': esp, 'form': form, 'nav_position': "esps"})


@login_required(login_url='/fablabcontrol/log_in/')
def new_esp(request):
    form = ESPForm(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            try:
                new_esp = form.save()
                new_esp.status = 'Idle'
                new_esp.save()
            except Exception as e:
                return render(request, 'fablabcontrol/esp.html',
                              {'form': form, 'error_message': str(e), 'nav_position': "esps"})
            return redirect(reverse('fablabcontrol:esps'))
        else:
            return render(request, 'fablabcontrol/esp.html',
                          {'form': form, 'error_message': form.errors})
    return render(request, 'fablabcontrol/esp.html',
                  {'form': form, 'nav_position': "esps"})


def machine(request, machine_id):
    machine = get_object_or_404(Machine, pk=machine_id)

    return render(request, 'fablabcontrol/machine.html',
                  {'machine': machine, 'nav_position': "machines"})


def machines(request):
    machines = Machine.objects.order_by('name')

    return render(request, 'fablabcontrol/machine.html',
                  {'machines': machines, 'nav_position': "machines"})


@login_required(login_url='/fablabcontrol/log_in/')
def mod_machine(request, machine_id):
    machine = get_object_or_404(Machine, pk=machine_id)
    form = MachineForm(request.POST or None, instance=machine)

    if request.method == "POST":
        if form.is_valid():
            try:
                form.save()
            except Exception as e:
                return render(request, 'fablabcontrol/machine.html',
                              {'machine': machine, 'form': form, 'error_message': str(e)})
            return redirect(reverse('fablabcontrol:machines'))
        else:
            return render(request, 'fablabcontrol/machine.html', {
                          'machine': machine, 'form': form, 'error_message': form.errors, 'nav_position': "machines"})
    return render(request, 'fablabcontrol/machine.html',
                  {'machine': machine, 'form': form, 'nav_position': "machines"})


@login_required(login_url='/fablabcontrol/log_in/')
def new_machine(request):
    form = MachineForm(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            try:
                new_machine = form.save()
                new_machine.save()
            except Exception as e:
                return render(request, 'fablabcontrol/machine.html',
                              {'form': form, 'error_message': str(e), })
            return redirect(reverse('fablabcontrol:machines'))
        else:
            return render(request, 'fablabcontrol/machine.html',
                          {'form': form, 'error_message': form.errors, 'nav_position': "machines"})
    return render(request, 'fablabcontrol/machine.html',
                  {'form': form, 'nav_position': "machines"})


def user(request, fablabuser_id):
    fablabuser = get_object_or_404(FabLabUser, pk=fablabuser_id)
    return render(request, 'fablabcontrol/user.html',
                  {'fablabuser': fablabuser, 'nav_position': "users"})


def users(request):
    fablabuser = FabLabUser.objects.order_by('rfid_uuid')
    return render(request, 'fablabcontrol/user.html',
                  {'fablabusers': fablabuser, 'nav_position': "users"})


@login_required(login_url='/fablabcontrol/log_in/')
def mod_user(request, fablabuser_id):
    fablabuser = get_object_or_404(FabLabUser, pk=fablabuser_id)

    form = UserForm(request.POST or None, request.FILES or None, user_id=fablabuser.id)
    if request.method == "POST":
        if form.is_valid():
            fablabuser.user.username = request.POST['username']
            fablabuser.user.first_name = request.POST['first_name']
            fablabuser.user.last_name = request.POST['last_name']
            fablabuser.user.email = request.POST['email']
            fablabuser.rfid_uuid = request.POST['rfid_uuid']
            fablabuser.image = form.cleaned_data['image']
            post_machines = form.cleaned_data['machine_field']
            post_briefings = form.cleaned_data['briefing_field']

            try:
                fablabuser.user.save()
                fablabuser.save()

                for machine in Machine.objects.all():
                    if str(
                            machine.id) in post_machines and not machine in fablabuser.machines.all():
                        machine.users.add(fablabuser)
                        machine.save()
                    elif str(machine.id) not in post_machines and machine in fablabuser.machines.all():
                        machine.users.remove(fablabuser)
                        machine.save()

                for briefing in Briefing.objects.all():
                    if str(
                            briefing.id) in post_briefings and not briefing in fablabuser.briefings.all():
                        fablabuser.briefings.add(briefing)
                        fablabuser.save()

                    elif str(briefing.id) not in post_briefings and briefing in fablabuser.briefings.all():
                        fablabuser.briefings.remove(briefing)
                        fablabuser.save()

                if form.cleaned_data['activity_group'] and not fablabuser.user.groups.filter(
                        name='UserActivityGroup').exists():
                    fablabuser.user.groups.add(
                        Group.objects.get(name='UserActivityGroup'))
                elif not form.cleaned_data['activity_group'] and fablabuser.user.groups.filter(name='UserActivityGroup').exists():
                    fablabuser.user.groups.remove(
                        Group.objects.get(name='UserActivityGroup'))

            except Exception as e:
                return render(request, 'fablabcontrol/user.html',
                              {'form': form, 'error_message': str(e), 'nav_position': "users"})
            return redirect(reverse('fablabcontrol:users'))
        else:
            return render(request, 'fablabcontrol/user.html',
                          {'form': form, 'error_message': form.errors, 'nav_position': "users"})
    return render(request, 'fablabcontrol/user.html',
                  {'fablabuser': fablabuser, 'form': form, 'nav_position': "users"})


@login_required(login_url='/fablabcontrol/log_in/')
def new_user(request):
    form = UserForm(request.POST or None, request.FILES or None)
    if request.method == "POST":
        if form.is_valid():
            post_machines = form.cleaned_data['machine_field']
            post_briefings = form.cleaned_data['briefing_field']

            try:
                user = User(
                    username=request.POST['username'],
                    first_name=request.POST['first_name'],
                    last_name=request.POST['last_name'],
                    email=request.POST['email'])
                user.save()
                fablabuser = FabLabUser(rfid_uuid=request.POST['rfid_uuid'], user=user)
                if 'image' in request.POST:
                    fablabuser.image = form.cleaned_data['image']
                fablabuser.save()

                for machine in Machine.objects.all():
                    if str(
                            machine.id) in post_machines and not machine in fablabuser.machines.all():
                        machine.users.add(fablabuser)
                        machine.save()
                    elif str(machine.id) not in post_machines and machine in fablabuser.machines.all():
                        machine.users.remove(fablabuser)
                        machine.save()

                for briefing in Briefing.objects.all():
                    if str(
                            briefing.id) in post_briefings and not briefing in fablabuser.briefings.all():
                        fablabuser.briefings.add(briefing)
                        fablabuser.save()

                    elif str(briefing.id) not in post_briefings and briefing in fablabuser.briefings.all():
                        fablabuser.briefings.remove(briefing)
                        fablabuser.save()

                if form.cleaned_data['activity_group'] and not fablabuser.user.groups.filter(
                        name='UserActivityGroup').exists():
                    fablabuser.user.groups.add(
                        Group.objects.get(name='UserActivityGroup'))
                elif not form.cleaned_data['activity_group'] and fablabuser.user.groups.filter(name='UserActivityGroup').exists():
                    fablabuser.user.groups.remove(
                        Group.objects.get(name='UserActivityGroup'))

            except Exception as e:
                return render(request, 'fablabcontrol/user.html',
                              {'form': form, 'error_message': str(e), 'nav_position': "users"})
            return redirect(reverse('fablabcontrol:users'))
        else:
            return render(request, 'fablabcontrol/user.html',
                          {'form': form, 'error_message': form.errors})
    return render(request, 'fablabcontrol/user.html',
                  {'form': form, 'nav_position': "users"})


@login_required(login_url='/fablabcontrol/log_in/')
def machine_activity(request, machine_id):
    machine = get_object_or_404(Machine, pk=machine_id)
    return render(request, 'fablabcontrol/activity.html',
                  {'machine': machine, 'nav_position': "activities"})


@login_required(login_url='/fablabcontrol/log_in/')
def user_activity(request, fablabuser_id):
    fablabuser = get_object_or_404(FabLabUser, pk=fablabuser_id)
    return render(request, 'fablabcontrol/activity.html',
                  {'fablabuser': fablabuser, 'nav_position': "activities"})


@login_required(login_url='/fablabcontrol/log_in/')
def activities(request):
    try:
        activities = UserActivityMonitor.objects.all().order_by('-datestart')
    except Exception as e:
        return render(request, 'fablabcontrol/activity.html', {'error_message': str(e), })
    return render(request, 'fablabcontrol/activity.html',
                  {'activities': activities, 'nav_position': "activities"})


@login_required(login_url='/fablabcontrol/log_in/')
def activity(request, activity_id):
    activity = get_object_or_404(UserActivityMonitor, pk=activity_id)
    return render(request, 'fablabcontrol/activity.html',
                  {'activity': activity, 'nav_position': "activities"})


@login_required(login_url='/fablabcontrol/log_in/')
def mod_activity(request, activity_id):
    activity = get_object_or_404(UserActivityMonitor, pk=activity_id)
    form = UserActivityForm(
        request.POST or None,
        request.FILES or None,
        instance=activity)

    # the machine field should not be changed by the user, but it is not bad
    # if it happens. So we just hide the field
    form.fields['machine'].widget = forms.HiddenInput()

    if request.method == "POST":
        if form.is_valid():
            try:
                activity = form.save()
                files = request.FILES.getlist('file_field')
                for file in files:
                    doc = ActivityDocument(activity=activity, file=file)
                    doc.save()
            except Exception as e:
                return render(request, 'fablabcontrol/activity.html', {
                              'activity': activity, 'form': form, 'error_message': str(e), 'nav_position': "activities"})
            return redirect(reverse('fablabcontrol:activities'))
        else:
            return render(request, 'fablabcontrol/activity.html',
                          {'activity': activity, 'form': form, 'error_message': form.errors})
    return render(request, 'fablabcontrol/activity.html',
                  {'activity': activity, 'form': form, 'nav_position': "activities"})


@login_required(login_url='/fablabcontrol/log_in/')
def new_activity(request):
    form = UserActivityForm(request.POST or None, request.FILES or None)
    if request.method == "POST":
        if form.is_valid():
            try:
                activity = form.save()
                files = request.FILES.getlist('file_field')
                for file in files:
                    doc = ActivityDocument(activity=activity, file=file)
                    doc.save()
            except Exception as e:
                return render(request, 'fablabcontrol/activity.html',
                              {'form': form, 'error_message': str(e), })
            return redirect(reverse('fablabcontrol:activities'))
        else:
            return render(request, 'fablabcontrol/activity.html',
                          {'form': form, 'error_message': form.errors})
    return render(request, 'fablabcontrol/activity.html',
                  {'form': form, 'nav_position': "activities"})


def briefing(request, briefing_id):
    briefing = get_object_or_404(Briefing, pk=briefing_id)
    return render(request, 'fablabcontrol/briefings.html',
                  {'briefing': briefing, 'nav_position': "briefings"})


def briefings(request):
    try:
        briefings = Briefing.objects.all()
    except Exception as e:
        return render(request, 'fablabcontrol/briefings.html',
                      {'error_message': str(e), })
    return render(request, 'fablabcontrol/briefings.html',
                  {'briefings': briefings, 'nav_position': "briefings"})


@login_required(login_url='/fablabcontrol/log_in/')
def mod_briefing(request, briefing_id):
    briefing = get_object_or_404(Briefing, pk=briefing_id)
    form = BriefingForm(request.POST or None, request.FILES or None, instance=briefing)
    if request.method == "POST":
        if form.is_valid():
            try:
                briefing = form.save()
                files = request.FILES.getlist('file_field')
                for file in files:
                    doc = BriefingDocument(briefing=briefing, file=file)
                    doc.save()
            except Exception as e:
                return render(request, 'fablabcontrol/briefings.html',
                              {'briefing': briefing, 'form': form, 'error_message': str(e), })
            return redirect(reverse('fablabcontrol:briefings'))
        else:
            return render(request, 'fablabcontrol/briefings.html',
                          {'briefing': briefing, 'form': form, 'error_message': form.errors})
    return render(request, 'fablabcontrol/briefings.html',
                  {'briefing': briefing, 'form': form, 'nav_position': "briefings"})


@login_required(login_url='/fablabcontrol/log_in/')
def new_briefing(request):
    form = BriefingForm(request.POST or None, request.FILES or None)
    if request.method == "POST":
        if form.is_valid():
            try:
                briefing = form.save()
                files = request.FILES.getlist('file_field')
                for file in files:
                    doc = BriefingDocument(briefing=briefing, file=file)
                    doc.save()
            except Exception as e:
                return render(request, 'fablabcontrol/briefings.html',
                              {'form': form, 'error_message': str(e), })
            return redirect(reverse('fablabcontrol:briefings'))
        else:
            return render(request, 'fablabcontrol/briefings.html',
                          {'form': form, 'error_message': form.errors})
    return render(request, 'fablabcontrol/briefings.html',
                  {'form': form, 'nav_position': "briefings"})


@login_required(login_url='/fablabcontrol/log_in/')
def user_maintenance(request, fablabuser_id):
    fablabuser = get_object_or_404(FabLabUser, pk=fablabuser_id)
    return render(request, 'fablabcontrol/maintenance.html',
                  {'fablabuser': fablabuser, 'nav_position': "maintenances"})


@login_required(login_url='/fablabcontrol/log_in/')
def machine_maintenance(request, machine_id):
    machine = get_object_or_404(Machine, pk=machine_id)
    return render(request, 'fablabcontrol/maintenance.html',
                  {'machine': machine, 'nav_position': "maintenances"})


@login_required(login_url='/fablabcontrol/log_in/')
def maintenances(request):
    try:
        maintenances = Maintenance.objects.all().order_by('-start')
    except Exception as e:
        return render(request, 'fablabcontrol/maintenance.html',
                      {'error_message': str(e), })
    return render(request, 'fablabcontrol/maintenance.html',
                  {'maintenances': maintenances, 'nav_position': "maintenances"})


@login_required(login_url='/fablabcontrol/log_in/')
def maintenance(request, maintenance_id):
    maintenance = get_object_or_404(Maintenance, pk=maintenance_id)
    return render(request, 'fablabcontrol/maintenance.html',
                  {'maintenance': maintenance, 'nav_position': "maintenances"})


@login_required(login_url='/fablabcontrol/log_in/')
def mod_maintenance(request, maintenance_id):
    maintenance = get_object_or_404(Maintenance, pk=maintenance_id)
    form = MaintenanceForm(
        request.POST or None,
        request.FILES or None,
        instance=maintenance)
    if request.method == "POST":
        if form.is_valid():
            try:
                maintenance = form.save()
                files = request.FILES.getlist('file_field')
                for file in files:
                    doc = MaintenanceDocument(maintenance=maintenance, file=file)
                    doc.save()
            except Exception as e:
                return render(request, 'fablabcontrol/maintenance.html',
                              {'maintenance': maintenance, 'form': form, 'error_message': str(e), })
            return redirect(reverse('fablabcontrol:maintenances'))
        else:
            return render(request, 'fablabcontrol/maintenance.html',
                          {'maintenance': maintenance, 'form': form, 'error_message': form.errors})
    return render(request, 'fablabcontrol/maintenance.html',
                  {'maintenance': maintenance, 'form': form, 'nav_position': "maintenances"})


@login_required(login_url='/fablabcontrol/log_in/')
def new_maintenance(request):
    form = MaintenanceForm(request.POST or None, request.FILES or None)
    if request.method == "POST":
        if form.is_valid():
            try:
                maintenance = form.save()
                files = request.FILES.getlist('file_field')
                for file in files:
                    doc = MaintenanceDocument(maintenance=maintenance, file=file)
                    doc.save()
            except Exception as e:
                return render(request, 'fablabcontrol/maintenance.html',
                              {'form': form, 'error_message': str(e), })
            return redirect(reverse('fablabcontrol:maintenances'))
        else:
            return render(request, 'fablabcontrol/maintenance.html',
                          {'form': form, 'error_message': form.errors})
    return render(request, 'fablabcontrol/maintenance.html',
                  {'form': form, 'nav_position': "maintenances"})


@login_required(login_url='/fablabcontrol/log_in/')
def circle_energy(request, circle_id):
    pass


@login_required(login_url='/fablabcontrol/log_in/')
def machine_energy(request, machine_id):
    machine = get_object_or_404(Machine, pk=machine_id)
    try:
        energy = EnergyMonitor.objects.filter(machine__in=[machine]).order_by('date')
    except Exception as e:
        return render(request, 'fablabcontrol/energy.html',
                      {'machine': machine, 'error_message': str(e), })

    hourvalues = {}
    lastvalue = energy[0].date
    for value in energy:
        # werte werden manchmal doppelt in db gespeichert, nur ein mal addieren...
        if lastvalue and not lastvalue == value.date:
            lastvalue = value.date
            hourdate = value.date.replace(minute=0, second=0)
            hourdate = int(hourdate.strftime('%s')) * 1000
            # nur stundenwerte anzeigen, also alles was nicht volle stunde ist zum
            # nächsten stundenwert dazu
            if value.date.minute > 0:
                hourdate = hourdate + 3600000

            if hourdate in hourvalues:
                hourvalues[hourdate] = hourvalues[hourdate] + value.power
            else:
                hourvalues[hourdate] = value.power

    data = [
        {'label': 'Energy in W/h',
         'color': '#000',
         'data': sorted(hourvalues.items()),
         'points': {'fillColor': '#fff'},
         'lines': {'fillColor': 'rgba(8,146,205,.2)'}
         }
    ]
    return render(request, 'fablabcontrol/energy.html', {'data': json.dumps(data), })


@login_required(login_url='/fablabcontrol/log_in/')
def machines_energy(request):
    import random

    machines = Machine.objects.all()

    data = []
    for machine in machines:
        try:
            energy = EnergyMonitor.objects.filter(machine__in=[machine]).order_by('date')
        except Exception as e:
            return render(request, 'fablabcontrol/energy.html',
                          {'machine': machine, 'error_message': str(e), })

        hourvalues = {}
        if len(energy) > 0:
            lastvalue = energy[0].date
            for value in energy:
                # werte werden manchmal doppelt in db gespeichert, nur ein mal addieren...
                if lastvalue and not lastvalue == value.date:
                    lastvalue = value.date
                    hourdate = value.date.replace(minute=0, second=0)
                    hourdate = int(hourdate.strftime('%s')) * 1000
                    # nur stundenwerte anzeigen, also alles was nicht volle stunde ist zum
                    # nächsten stundenwert dazu
                    if value.date.minute > 0:
                        hourdate = hourdate + 3600000

                    if hourdate in hourvalues:
                        hourvalues[hourdate] = hourvalues[hourdate] + value.power
                    else:
                        hourvalues[hourdate] = value.power

        r = lambda: random.randint(0, 255)
        data.append({'label': machine.name,
                     'data': sorted(hourvalues.items()),
                     'color': '#%02X%02X%02X' % (r(), r(), r()),
                     'points': {'fillColor': '#fff'},
                     'lines': {'fillColor': 'rgba(8,146,205,0)'}})

    return render(request, 'fablabcontrol/energy.html', {'data': json.dumps(data), })


@login_required(login_url='/fablabcontrol/log_in/')
def check_plugwise_config(request):
    plugwise_machines = None

    with open('/root/Plugwise-2-py/config/pw-conf.json') as plugwise_config:
        plugwise_machines = json.load(plugwise_config)
        plugwise_config.close()

    if plugwise_machines:
        for obj in plugwise_machines["static"]:
            if Machine.objects.filter(circle_mac=obj["mac"]).exists():
                print('Objekt gefunden: ')
                print(obj)
                print('\n')
            else:
                print('Objekt NICHT gefunden: ')
                print(obj)
                print('\n')

        for machine in Machine.objects.all():
            pass

    return redirect(reverse('fablabcontrol:index'))
