# Generated by Django 4.2.7 on 2024-04-13 19:20

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0005_room_room_picture'),
    ]

    operations = [
        migrations.CreateModel(
            name='KeyPair',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('public_key', models.TextField()),
                ('private_key', models.TextField()),
                ('room', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='chat.room')),
            ],
        ),
    ]