import uuid

from django.db import migrations, models


def populate_share_uuid(apps, schema_editor):
    Test = apps.get_model("main", "Test")
    for t in Test.objects.filter(share_uuid__isnull=True):
        t.share_uuid = uuid.uuid4()
        t.save(update_fields=["share_uuid"])


class Migration(migrations.Migration):
    dependencies = [
        ("main", "0002_useranswer_constraints"),
    ]

    operations = [
        migrations.AddField(
            model_name="test",
            name="visibility",
            field=models.CharField(
                choices=[
                    ("public", "Публичное (видно всем)"),
                    ("unlisted", "По ссылке (не показывать в списке)"),
                    ("restricted", "Только выбранным пользователям"),
                ],
                default="public",
                max_length=12,
                verbose_name="Доступ",
            ),
        ),
        migrations.AddField(
            model_name="test",
            name="share_uuid",
            field=models.UUIDField(blank=True, editable=False, null=True),
        ),
        migrations.AddField(
            model_name="test",
            name="allowed_users",
            field=models.ManyToManyField(
                blank=True,
                related_name="allowed_tests",
                to="auth.user",
                verbose_name="Разрешённые пользователи",
            ),
        ),
        migrations.RunPython(populate_share_uuid, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="test",
            name="share_uuid",
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
    ]

