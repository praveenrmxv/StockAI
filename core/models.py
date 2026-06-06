from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class Product(models.Model):
    name = models.CharField(max_length=100)
    quantity = models.IntegerField()
    price = models.FloatField()

    def __str__(self):
        return self.name
    
class Sale(models.Model):
    product_name = models.CharField(max_length=100)
    quantity = models.IntegerField()
    price = models.FloatField()
    date = models.DateField()

    def __str__(self):
        return self.product_name
    

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='profiles/', default='default.jpg')



@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)