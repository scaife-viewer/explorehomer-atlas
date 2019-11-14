# Generated by Django 2.2.7 on 2019-11-14 22:49

from django.db import migrations, models
import django.db.models.deletion
import django_extensions.db.fields.json


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Book",
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
                ("position", models.IntegerField()),
                ("idx", models.IntegerField(help_text="0-based index")),
            ],
            options={"ordering": ["idx"]},
        ),
        migrations.CreateModel(
            name="Version",
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
                ("urn", models.CharField(max_length=255)),
                ("name", models.CharField(blank=True, max_length=255, null=True)),
                (
                    "metadata",
                    django_extensions.db.fields.json.JSONField(
                        blank=True, default=dict
                    ),
                ),
            ],
            options={"ordering": ["urn"]},
        ),
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
                        to="library.Version",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Line",
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
                ("text_content", models.TextField()),
                ("position", models.IntegerField()),
                ("book_position", models.IntegerField()),
                ("idx", models.IntegerField(help_text="0-based index")),
                (
                    "book",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="lines",
                        to="library.Book",
                    ),
                ),
                (
                    "version",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="lines",
                        to="library.Version",
                    ),
                ),
            ],
            options={"ordering": ["idx"]},
        ),
        migrations.AddField(
            model_name="book",
            name="version",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="books",
                to="library.Version",
            ),
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
                        to="library.Line",
                    ),
                ),
                (
                    "start",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="+",
                        to="library.Line",
                    ),
                ),
                (
                    "version",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="alignment_chunks",
                        to="library.Version",
                    ),
                ),
            ],
            options={"ordering": ["idx"]},
        ),
    ]
