# Generated by Django 5.2.3 on 2025-06-17 14:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        (
            "ideas_app",
            "0003_remove_repoidea_ideas_alter_ideadetail_detailed_info_and_more",
        ),
    ]

    operations = [
        migrations.AlterField(
            model_name="ideadetail",
            name="groq_score",
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="ideadetail",
            name="user_feedback",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="ideadetail",
            name="user_score",
            field=models.FloatField(blank=True, null=True),
        ),
    ]
