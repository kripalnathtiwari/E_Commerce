import django
import storages
import boto3
print(f"Django: {django.get_version()}")
print(f"Storages found: {storages.__name__}")
print(f"Boto3 found: {boto3.__name__}")
