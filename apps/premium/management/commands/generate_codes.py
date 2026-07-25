import csv
import secrets
import string
import hashlib
from django.core.management.base import BaseCommand
from premium.models import PremiumCode


class Command(BaseCommand):
    help = 'Generates unguessable alphanumeric Premium codes, stores SHA-256 hashes in DB, and exports raw codes to a CSV file.'

    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=10, help='Number of codes to generate')
        parser.add_argument('--output', type=str, default='generated_codes.csv', help='CSV output file path')

    def handle(self, *args, **options):
        count = options['count']
        output_file = options['output']

        generated_data = []  # List of (raw_code, hash) tuples
        db_instances = []

        characters = string.ascii_uppercase + string.digits

        for _ in range(count):
            # Generate unguessable 12-character code (e.g. "X7K9-M2P4-Q8R1")
            raw_code = '-'.join([
                ''.join(secrets.choice(characters) for _ in range(4))
                for _ in range(3)
            ])
            
            code_hash = hashlib.sha256(raw_code.encode('utf-8')).hexdigest()
            generated_data.append((raw_code, code_hash))
            db_instances.append(PremiumCode(code_hash=code_hash))

        # Bulk insert hashes into PostgreSQL
        PremiumCode.objects.bulk_create(db_instances)

        # Write raw codes to local CSV file
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Raw Code (Give to Student)', 'SHA256 Hash'])
            for raw, code_hash in generated_data:
                writer.writerow([raw, code_hash])

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully created {count} Premium codes. Raw codes exported to '{output_file}'."
            )
        )