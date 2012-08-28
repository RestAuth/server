# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'ServiceUser.last_login'
        db.delete_column('Users_serviceuser', 'last_login')

        # Deleting field 'ServiceUser.date_joined'
        db.delete_column('Users_serviceuser', 'date_joined')


    def backwards(self, orm):

        # User chose to not deal with backwards NULL issues for 'ServiceUser.last_login'
        raise RuntimeError("Cannot reverse this migration. 'ServiceUser.last_login' and its values cannot be restored.")

        # User chose to not deal with backwards NULL issues for 'ServiceUser.date_joined'
        raise RuntimeError("Cannot reverse this migration. 'ServiceUser.date_joined' and its values cannot be restored.")

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
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '60'})
        }
    }

    complete_apps = ['Users']