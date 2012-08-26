# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'ServiceUser.hash'
        db.delete_column('Users_serviceuser', 'hash')

        # Deleting field 'ServiceUser.algorithm'
        db.delete_column('Users_serviceuser', 'algorithm')

        # Deleting field 'ServiceUser.salt'
        db.delete_column('Users_serviceuser', 'salt')


    def backwards(self, orm):
        # Adding field 'ServiceUser.hash'
        db.add_column('Users_serviceuser', 'hash',
                      self.gf('django.db.models.fields.CharField')(max_length=128, null=True, blank=True),
                      keep_default=False)

        # Adding field 'ServiceUser.algorithm'
        db.add_column('Users_serviceuser', 'algorithm',
                      self.gf('django.db.models.fields.CharField')(max_length=20, null=True, blank=True),
                      keep_default=False)

        # Adding field 'ServiceUser.salt'
        db.add_column('Users_serviceuser', 'salt',
                      self.gf('django.db.models.fields.CharField')(max_length=16, null=True, blank=True),
                      keep_default=False)


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
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '60'})
        }
    }

    complete_apps = ['Users']