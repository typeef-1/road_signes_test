from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):
    dependencies = [
        ("main", "0001_initial"),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="useranswer",
            unique_together=set(),
        ),
        migrations.AddConstraint(
            model_name="useranswer",
            constraint=models.UniqueConstraint(
                fields=["user", "question"],
                condition=Q(selected_answer__isnull=True),
                name="uniq_user_question_for_text",
            ),
        ),
        migrations.AddConstraint(
            model_name="useranswer",
            constraint=models.UniqueConstraint(
                fields=["user", "question", "selected_answer"],
                condition=Q(selected_answer__isnull=False),
                name="uniq_user_question_selected_answer",
            ),
        ),
    ]

