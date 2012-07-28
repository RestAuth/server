# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        old = 'Services_service_hosts'
        new = 'Services_serviceaddress_services'
        db.delete_foreign_key(old, 'service_id')
        db.delete_index(old, ['service_id'])
        db.delete_index(old, ['serviceaddress_id'])
        db.delete_unique(old, ['service_id', 'serviceaddress_id'])

        # switch sides of the many2many column:
        db.rename_table(old, new)

        db.create_index(new, ['service_id'])
        db.create_index(new, ['serviceaddress_id'])
        db.create_unique(new, ['service_id', 'serviceaddress_id'])

        db.delete_table('Services_service')
        
        # Adding M2M table for field services on 'ServiceAddress'
#        db.create_table('Services_serviceaddress_services', (
#            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
#                    ('serviceaddress', models.ForeignKey(orm['Services.serviceaddress'], null=False)),
#            ('service', models.ForeignKey(orm['Services.service'], null=False))
#        ))
#        db.create_unique('Services_serviceaddress_services', ['serviceaddress_id', 'service_id'])

        # Deleting field 'Service.user_ptr'
#        db.delete_column('Services_service', 'user_ptr_id')

        # Removing M2M table for field hosts on 'Service'
#        db.delete_table('Services_service_hosts')


    def backwards(self, orm):
        return
        raise RuntimeError("Cannot reverse this migration. 'Service.user_ptr' and its values cannot be restored.")
        
        # Removing M2M table for field services on 'ServiceAddress'
        db.delete_table('Services_serviceaddress_services')

        # User chose to not deal with backwards NULL issues for 'Service.user_ptr'

        # Adding M2M table for field hosts on 'Service'
        db.create_table('Services_service_hosts', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('service', models.ForeignKey(orm['Services.service'], null=False)),
            ('serviceaddress', models.ForeignKey(orm['Services.serviceaddress'], null=False))
        ))
        db.create_unique('Services_service_hosts', ['service_id', 'serviceaddress_id'])


    models = {
        'Services.service': {
            'Meta': {'object_name': 'Service', 'db_table': "'auth_user'", '_ormbases': ['auth.User'], 'proxy': 'True'}
        },
        'Services.serviceaddress': {
            'Meta': {'object_name': 'ServiceAddress'},
            'address': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '39'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'services': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'hosts'", 'symmetrical': 'False', 'to': "orm['auth.User']"})
        },
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2012, 7, 27, 18, 22, 58, 645314)'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2012, 7, 27, 18, 22, 58, 645146)'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['Services']
