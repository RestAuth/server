# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'ServiceUser'
        db.create_table('Users_serviceuser', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('username', self.gf('django.db.models.fields.CharField')(unique=True, max_length=60)),
            ('algorithm', self.gf('django.db.models.fields.CharField')(max_length=20, null=True, blank=True)),
            ('salt', self.gf('django.db.models.fields.CharField')(max_length=16, null=True, blank=True)),
            ('hash', self.gf('django.db.models.fields.CharField')(max_length=128, null=True, blank=True)),
            ('last_login', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, auto_now_add=True, blank=True)),
            ('date_joined', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('Users', ['ServiceUser'])

        # Adding model 'Property'
        db.create_table('Users_property', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['Users.ServiceUser'])),
            ('key', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('value', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('Users', ['Property'])

        # Adding unique constraint on 'Property', fields ['user', 'key']
        db.create_unique('Users_property', ['user_id', 'key'])


    def backwards(self, orm):
        # Removing unique constraint on 'Property', fields ['user', 'key']
        db.delete_unique('Users_property', ['user_id', 'key'])

        # Deleting model 'ServiceUser'
        db.delete_table('Users_serviceuser')

        # Deleting model 'Property'
        db.delete_table('Users_property')


    models = {
        'Users.property': {
            'Meta': {'unique_together': "(('user', 'key'),)", 'object_name': 'Property'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
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
            'salt': ('django.db.models.fields.CharField', [], {'max_length': '16', 'null': 'True', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '60'})
        }
    }

    complete_apps = ['Users']