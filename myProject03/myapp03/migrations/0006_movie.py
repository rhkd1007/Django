# Generated by Django 4.1.7 on 2023-03-06 13:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("myapp03", "0005_delete_melon"),
    ]

    operations = [
        migrations.CreateModel(
            name="movie",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("title", models.CharField(max_length=500)),
                ("content", models.TextField(null=True)),
                ("point", models.IntegerField(default=0)),
            ],
        ),
    ]
