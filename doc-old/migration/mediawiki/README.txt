RestAuth can save hashes in a format compatible with MediaWiki. If you want to
*store* hashes in this format, you can set
	HASH_ALGORITHM = 'mediawiki'
in settings.py of your RestAuth installation. Always note that this only affects
new hashes, that is, when a new user is created or the user updates his/her
password.

=== Importing old hashes ===
RestAuth supports importing old MediaWiki hashes. A description of how to do
this manually is written below, you can find a script that creates INSERT
statements from a MediaWiki MySQL database to a RestAuth MySQL database in the
same directory as this file - execute it with --help for usage.

MediaWiki can store hashes in two different ways, either with a salt (default) 
or without a salt. The former start with :B:, the latter with :A:. In any case,
the 'algorithm' field becomes 'mediawiki'. 

For hashes with salt, the salt field becomes the value between the second and
third column, the hash field becomes the value after the third column. So given
a the following user_password field in the table user:
	:B:100:hash_value
you can add the user to RestAuth with (in MySQL syntax):
	INSERT INTO users_serviceuser (algorithm, salt, hash) VALUES ('mediawiki', '100', 'hash_value');

For hashes without salt, the field
	:A:hash_value
can be added with
	INSERT INTO users_serviceuser (algorithm, hash) VALUES ('mediawiki', 'hash_value');
