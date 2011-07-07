.. only:: not man
   
   add
   ^^^

   
.. example:: **add** [**-h**] [**--password** *PWD* | **--gen-password**] *username*
   
   Add a new user.
   
   .. program:: restauth-user-add

   .. option:: --password PWD
      
      The password to use.
      
   .. option:: --gen-password
      
      Generate a password and print it to stdout.
      
   .. option:: username
      
      The name of the user.
      
.. only:: not man
   
   list
   ^^^^

   
.. example:: **list** [**-h**]
   
   List all users.
   
.. only:: not man
   
   rm
   ^^

   
.. example:: **rm** [**-h**] *username*
   
   Remove a user.
   
   .. program:: restauth-user-rm

   .. option:: username
      
      The name of the user.
      
.. only:: not man
   
   set-password
   ^^^^^^^^^^^^

   
.. example:: **set-password** [**-h**] [**--password** *PWD* | **--gen-password**] *username*
   
   Set the password of a user.
   
   .. program:: restauth-user-set-password

   .. option:: --password PWD
      
      The password to use.
      
   .. option:: --gen-password
      
      Generate a password and print it to stdout.
      
   .. option:: username
      
      The name of the user.
      
.. only:: not man
   
   verify
   ^^^^^^

   
.. example:: **verify** [**-h**] [**--password** *PWD* | **--gen-password**] *username*
   
   Verify the password of a user.
   
   .. program:: restauth-user-verify

   .. option:: --password PWD
      
      The password to use.
      
   .. option:: --gen-password
      
      Generate a password and print it to stdout.
      
   .. option:: username
      
      The name of the user.
      
.. only:: not man
   
   view
   ^^^^

   
.. example:: **view** [**-h**] [**--service** *SERVICE*] *username*
   
   View details of a user.
   
   .. program:: restauth-user-view

   .. option:: --service SERVICE
      
      View information as SERVICE would see it.
      
   .. option:: username
      
      The name of the user.
      
