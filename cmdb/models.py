from django.db import models


class Device(models.Model):
    ip = models.GenericIPAddressField(verbose_name='ip', unique=True)
    name = models.CharField(verbose_name='name', max_length=32, unique=True)
    version = models.CharField(verbose_name='version', max_length=32, blank=True)
    cpu = models.CharField(verbose_name='cpu', max_length=16, blank=True)
    model = models.CharField(verbose_name='model', max_length=32, blank=True)
    sn = models.CharField(verbose_name='sn', max_length=12, blank=True)
    created_time = models.DateTimeField('created_time', auto_now_add=True)
    update_time = models.DateTimeField('update_time', auto_now=True)

    def __str__(self):
        return '{} {}'.format(self.name, self.ip)

    def __iter__(self):
        return next(self)

    def __next__(self):
        yield ('ip', self.ip)
        yield ('name', self.name)
        yield ('version', self.version)
        yield ('cpu', self.cpu)
        yield ('model', self.model)
        yield ('sn', self.sn)
        yield ('created_time', self.created_time)
        yield ('update_time', self.update_time)