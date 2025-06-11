import random
from django.core.management.base import BaseCommand
from faker import Faker
from core.models import School
from admission.models import StudentAdmission, StudentAcademicRecord, AcademicYear, Class

fake = Faker()

class Command(BaseCommand):
    help = 'Seed dummy student data'

    def handle(self, *args, **kwargs):
        school = School.objects.first()
        year = AcademicYear.objects.filter(is_current=True, school=school).first()
        all_classes = list(Class.objects.filter(school=school))

        if not (school and year and all_classes):
            self.stdout.write(self.style.ERROR("Make sure at least one school, year, and class exists."))
            return

        for i in range(20):  # Create 20 dummy students
            full_name = fake.name()
            admission_no = f"ADM{1000 + i}"
            student = StudentAdmission.objects.create(
                admission_no=admission_no,
                ssr_no=f"SSR{i+1:03d}",
                full_name=full_name,
                gender=random.choice(['M', 'F']),
                date_of_birth=fake.date_of_birth(minimum_age=5, maximum_age=17),
                admission_date=fake.date_this_year(),
                father_name=fake.name_male(),
                mother_name=fake.name_female(),
                father_profession=random.choice(['Teacher', 'Engineer', 'Farmer', 'Clerk']),
                category=random.choice(['GEN', 'OBC', 'SC', 'ST']),
                religion=random.choice(['Hindu', 'Muslim', 'Christian', 'Sikh']),
                aadhar_no=str(fake.random_number(digits=12, fix_len=True)),
                apaar_id=str(fake.random_number(digits=12, fix_len=True)),
                mobile_no=str(fake.random_number(digits=10, fix_len=True)),
                whatsapp_no=str(fake.random_number(digits=10, fix_len=True)),
                email=fake.email(),
                address=fake.address(),
                school=school,
            )

            StudentAcademicRecord.objects.create(
                student=student,
                academic_year=year,
                class_enrolled=random.choice(all_classes),
                section=random.choice(['A', 'B', 'C']),
                school=school,
            )

        self.stdout.write(self.style.SUCCESS('✅ Successfully created 20 dummy students'))
