# -*- coding: utf-8 -*-
from datetime import datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models


class Migration(DataMigration):

    def forwards(self, orm):
        for user in orm.ServiceUser.objects.all():
            user.password = '%s$%s$%s' % (user.algorithm, user.salt, user.hash)
            user.save()

            if user.date_joined is not None:
                try:
                    raw = datetime.strftime(user.date_joined, "%Y-%m-%d %H:%M:%S")
                    user.property_set.create(key='date joined', value=raw)
                except:
                    pass
            if user.last_login is not None:
                try:
                    raw = datetime.strftime(user.last_login, "%Y-%m-%d %H:%M:%S")
                    user.property_set.create(key='last login', value=raw)
                except:
                    pass


    def backwards(self, orm):
        for user in orm.ServiceUser.objects.all():
            algo, salt, hash = user.password.split('$')
            user.algo = algo
            user.salt = salt
            user.hash = hash
            user.save()

    models = {
        'Users.property': {
            'Meta': {'unique_together': "(('user', 'key'),)", 'object_name': 'Property'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '128', 'db_index': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['Users.ServiceUser']"}),
            'value': ('django.db.models.fields.TextField', [], {})
        },
        'Users.serviceuser': {
            'Meta': {'object_name': 'ServiceUser'},
            'algorithm': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'}),
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'hash': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'salt': ('django.db.models.fields.CharField', [], {'max_length': '16', 'null': 'True', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '60'})
        }
    }

    complete_apps = ['Users']
    symmetrical = True
