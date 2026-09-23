from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('adminpanel', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='groups',
            field=models.ManyToManyField(
                blank=True,
                related_name='adminpanel_user_set',
                related_query_name='adminpanel_user',
                to='auth.group',
                verbose_name='groups',
            ),
        ),
        migrations.AlterField(
            model_name='user',
            name='user_permissions',
            field=models.ManyToManyField(
                blank=True,
                related_name='adminpanel_user_permissions_set',
                related_query_name='adminpanel_user_permission',
                to='auth.permission',
                verbose_name='user permissions',
            ),
        ),
    ]
