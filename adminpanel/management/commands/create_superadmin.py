from getpass import getpass
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.hashers import make_password
from adminpanel.models import Admin

class Command(BaseCommand):
    help = 'Create or update a FoodLoop Super Admin account.'

    def add_arguments(self, parser):
        parser.add_argument('--email')
        parser.add_argument('--first-name')
        parser.add_argument('--last-name', default='')
        parser.add_argument('--contact')
        parser.add_argument('--password')

    def handle(self, *args, **options):
        email = options['email'] or input('Super Admin email: ').strip().lower()
        first_name = options['first_name'] or input('First name: ').strip()
        last_name = options['last_name'] or input('Last name (optional): ').strip() or None
        contact = options['contact'] or input('Contact number: ').strip()
        password = options['password'] or getpass('Password (min 8 characters): ')
        if len(password) < 8:
            raise CommandError('Password must be at least 8 characters.')
        obj, created = Admin.objects.get_or_create(email=email, defaults={'first_name': first_name, 'last_name': last_name, 'contact': contact})
        obj.first_name = first_name
        obj.last_name = last_name
        obj.contact = contact
        obj.role = 'SUPER_ADMIN'
        obj.is_active = True
        obj.password = make_password(password)
        obj.save()
        self.stdout.write(self.style.SUCCESS(('Created' if created else 'Updated') + f' Super Admin: {email}'))
