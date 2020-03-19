# Generated by Django 2.2.10 on 2020-03-19 17:04

from django.db import migrations, models
import django.db.models.deletion
import django_extensions.db.fields.json


class Migration(migrations.Migration):

    dependencies = [
        ("library", "0004_node_rank"),
    ]

    operations = [
        migrations.CreateModel(
            name="VersionAlignment",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(blank=True, max_length=255, null=True)),
                ("slug", models.SlugField()),
                (
                    "metadata",
                    django_extensions.db.fields.json.JSONField(
                        blank=True, default=dict
                    ),
                ),
                (
                    "version",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="alignments",
                        to="library.Node",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="AlignmentChunk",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("citation", models.CharField(max_length=13)),
                (
                    "items",
                    django_extensions.db.fields.json.JSONField(
                        blank=True, default=list
                    ),
                ),
                (
                    "metadata",
                    django_extensions.db.fields.json.JSONField(
                        blank=True, default=dict
                    ),
                ),
                ("idx", models.IntegerField(help_text="0-based index")),
                (
                    "alignment",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="alignment_chunks",
                        to="library.VersionAlignment",
                    ),
                ),
                (
                    "end",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="+",
                        to="library.Node",
                    ),
                ),
                (
                    "start",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="+",
                        to="library.Node",
                    ),
                ),
                (
                    "version",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="alignment_chunks",
                        to="library.Node",
                    ),
                ),
            ],
            options={"ordering": ["idx"],},
        ),
    ]
