# Generated by Django 3.1.12 on 2021-06-22 14:03

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('messaging', '0006_auto_20210622_0714'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='message',
            name='sent_from_bot',
        ),
    ]
