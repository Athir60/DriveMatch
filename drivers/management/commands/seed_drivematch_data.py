from django.core.management.base import BaseCommand
from drivers.models import SubscriptionPlan, Route



RAW_NEIGHBORHOODS = [
    "Al Olaya", "Al Sulimaniyah", "Al Murabba", "Al Malaz", "Al Wizarat",
    "Al Futah", "Al Dirah", "Al Batha", "Al Mansourah", "Al Yamamah",
    "Al Marqab", "Al Amal", "Al Wisham", "Al Fakhiriyah", "Al Shumaisi",
    "Al Nasiriyah", "Umm Al Hamam", "Al Rahmaniyah", "Al Muhammadiyah",
    "Al Nakheel", "Al Mursalat", "Al Worood", "King Fahd District",
    "Al Masif", "Al Murooj", "Al Taawun", "Al Izdihar", "Al Mughrizat",
    "Al Nuzhah", "Al Waha", "Al Falah", "Al Yasmin", "Al Narjis",
    "Al Arid", "Al Qirawan", "Al Malqa", "Hittin", "Al Sahafah",
    "Al Aqiq", "Al Ghadeer", "Al Rabie", "Al Nada", "Al Nafal",
    "Al Wadi", "Al Yasmeen", "Al Munsiyah", "Qurtubah", "Al Yarmouk",
    "Al Hamra", "Ghirnatah", "Al Qadisiyah", "Al Shuhada",
    "King Faisal District", "Al Rawdah", "Al Andalus", "Al Nahdah",
    "Al Rayyan", "Al Rabwah", "Al Zahra", "Al Safa", "Al Salam",
    "Al Manar", "Al Khaleej", "Al Quds", "Al Janadriyah", "Al Rimal",
    "Al Nadhim", "Al Maizilah", "Al Bayan", "Al Saadah", "Ishbiliyah",
    "Al Rawabi", "Al Jazirah", "Al Fayha", "Al Naseem",
    "Al Naseem East", "Al Naseem West", "Al Manakh", "Al Sinaiyah",
    "Al Sulay", "Al Aziziyah", "Ad Dar Al Baida", "Al Mansuriyah",
    "Al Masani", "Al Iskan", "Tuwaiq", "Al Hazm", "Dhahrat Laban",
    "Laban", "Al Uraija", "Al Uraija Al Gharbiyah", "Al Shifa",
    "Badr", "Al Marwah", "Al Suwaidi", "Al Suwaidi Al Gharbi",
    "Sultanah", "Shubra", "Al Khalidiyah", "Al Faisaliyah",
    "Al Mahdiyah", "Al Hada", "Al Khuzama", "Al Safarat",
    "Diplomatic Quarter", "King Abdullah Financial District",
    "King Khalid Airport", "Princess Nourah University",
    "Imam Muhammad ibn Saud University", "King Saud University",
    "Riyadh Front", "Diriyah", "Irqah", "Al Ghadir", "Al Khair",
    "Al Awali", "Al Hair",
    "Al Ared", "Al Aarid", "Al Yasmin", "Al Yasmeen", "Al Qairawan",
    "Al Qayrawan", "Al Sahafa", "Al Rabi", "Al Nafel", "Al Nuzha",
    "Al Izdehar", "Al Muruj",
    "Al Remal", "Al Yarmuk", "Granada", "Al Zahraa", "Qurtuba",
    "Al Aziziyyah", "Al Dar Al Baida", "Al Mansouriyah",
    "Dhahrat Namar", "Namar", "Al Badi'ah", "Al Badiah",
    "Al Fouta", "Al Deerah", "Al Margab", "Al Oud",
    "Al Manfuhah", "Manfuhah", "Al Dhubbat", "Al Faruq",
    "Al Zahrah", "Al Jaradiyah", "Al Mansurah",
]


def deduplicate(names):
    """
    Remove exact duplicates while preserving order.
    Also strips whitespace and skips empty names.
    """
    seen = set()
    result = []
    for name in names:
        cleaned = name.strip()
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            result.append(cleaned)
    return result


class Command(BaseCommand):
    help = (
        'Seed SubscriptionPlan and Route data for DriveMatch. '
        'Idempotent — safe to run multiple times without duplicating data.'
    )

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('─' * 50))
        self.stdout.write(self.style.NOTICE('  DriveMatch Seed Data'))
        self.stdout.write(self.style.NOTICE('─' * 50))

        self.stdout.write('\nSeeding subscription plans...')

        plans_data = [
            {
                'name': '7-Day Free Trial',
                'price': 0,
                'duration_days': 7,
                'description': 'Free trial for new drivers.',
                'is_active': True,
            },
            {
                'name': 'Monthly Plan',
                'price': 149,
                'duration_days': 30,
                'description': 'Monthly subscription for active drivers.',
                'is_active': True,
            },
            {
                'name': 'Quarterly Plan',
                'price': 399,
                'duration_days': 90,
                'description': 'Three-month subscription with discounted price.',
                'is_active': True,
            },
            {
                'name': 'Yearly Plan',
                'price': 1499,
                'duration_days': 365,
                'description': 'Annual subscription for professional drivers.',
                'is_active': True,
            },
        ]

        plans_created = 0
        plans_updated = 0
        for plan_data in plans_data:
            name = plan_data.pop('name')
            _, created = SubscriptionPlan.objects.update_or_create(
                name=name,
                defaults=plan_data
            )
            plan_data['name'] = name   # restore for any future use
            if created:
                plans_created += 1
            else:
                plans_updated += 1

        self.stdout.write(
            f'  Plans created: {plans_created}, updated/already existed: {plans_updated}'
        )

        self.stdout.write('\nSeeding Riyadh routes...')

        neighborhoods = deduplicate(RAW_NEIGHBORHOODS)
        n = len(neighborhoods)
        expected = n * (n - 1)

        self.stdout.write(f'  Unique neighborhoods: {n}')
        self.stdout.write(f'  Expected routes (n × (n-1)): {expected}')
        self.stdout.write('  Creating routes... (this may take a moment)')

        routes_created = 0
        routes_existed = 0

        for from_area in neighborhoods:
            for to_area in neighborhoods:
                if from_area != to_area:
                    _, created = Route.objects.get_or_create(
                        from_area=from_area,
                        to_area=to_area,
                        city='Riyadh'
                    )
                    if created:
                        routes_created += 1
                    else:
                        routes_existed += 1

        self.stdout.write(f'  Routes created: {routes_created}')
        self.stdout.write(f'  Routes already existed: {routes_existed}')
        self.stdout.write(f'  Total routes in DB: {routes_created + routes_existed}')

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('─' * 50))
        self.stdout.write(self.style.SUCCESS('  Seeding complete!'))
        self.stdout.write(self.style.SUCCESS('─' * 50))
