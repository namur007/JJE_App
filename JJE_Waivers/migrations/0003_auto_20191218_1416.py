# Generated by Django 2.2.6 on 2019-12-18 19:16

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('JJE_Waivers', '0002_auto_20191024_2324'),
    ]

    operations = [
        migrations.AlterField(
            model_name='waiverclaim',
            name='yahoo_team',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='waiver_team', to='JJE_Main.YahooTeam'),
        ),
    ]