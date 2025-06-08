from django.db import migrations
import pgvector.django

class Migration(migrations.Migration):

    dependencies = [
        ('bp_backend', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='painting',
            name='caption_embedding',
            field=pgvector.django.VectorField(dimensions=512, null=True, blank=True),
        ),
    ]
