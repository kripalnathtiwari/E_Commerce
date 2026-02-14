from django.db import models

# Create your models here.
class Category(models.Model):
    cateogry_name=models.CharField(max_length=300, unique=True)
    slug=models.CharField(max_length=50, unique=True)
    description=models.TextField(max_length=255, blank=True)
    cat_image=models.ImageField(upload_to='photo/caegory', blank=True)

    class Meta:
        verbose_name='category'
        verbose_name_plural='categories'
    def __str__(self):
        return self.cateogry_name


    
