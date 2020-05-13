# Generated by Django 2.2.10 on 2020-05-13 15:21

from django.db import migrations, models
import django_extensions.db.fields.json


class Migration(migrations.Migration):

    dependencies = [
        ("library", "0011_add_place_named_entities"),
    ]

    operations = [
        migrations.AddField(
            model_name="namedentity",
            name="data",
            field=django_extensions.db.fields.json.JSONField(blank=True, default=dict),
        ),
        migrations.AlterField(
            model_name="metricalannotation",
            name="short_form",
            field=models.TextField(
                help_text='"|" indicates the start of a foot, ":" indicates a syllable boundary within a foot and "/" indicates a caesura.'
            ),
        ),
    ]
