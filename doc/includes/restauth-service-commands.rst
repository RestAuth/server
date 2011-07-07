.. only:: not man
   
   add
   ^^^

   
.. example:: **add** [**-h**] [**--password** *PWD* | **--gen-password**] *service* [*host* [*host* ...]]
   
   Add a new service.
   
   .. program:: restauth-service-add

   .. option:: --password PWD
      
      The password to use.
      
   .. option:: --gen-password
      
      Generate a password and print it to stdout.
      
   .. option:: service
      
      The name of the service.
      
   .. option:: hosts
      
      A host that the service is able to connect from. You can name multiple hosts as additional positional arguments. If ommitted, this service cannot be used from anywhere.
      
.. only:: not man
   
   ls
   ^^

   
.. example:: **ls** [**-h**]
   
   List all available services.
   
.. only:: not man
   
   rm
   ^^

   
.. example:: **rm** [**-h**] *service*
   
   Completely remove a service. This will also remove any groups associated with that service.
   
   .. program:: restauth-service-rm

   .. option:: service
      
      The name of the service.
      
.. only:: not man
   
   set-hosts
   ^^^^^^^^^

   
.. example:: **set-hosts** [**-h**] *service* [*host* [*host* ...]]
   
   Set hosts that a service can connect from.
   
   .. program:: restauth-service-set-hosts

   .. option:: service
      
      The name of the service.
      
   .. option:: hosts
      
      A host that the service is able to connect from. You can name multiple hosts as additional positional arguments. If ommitted, this service cannot be used from anywhere.
      
.. only:: not man
   
   set-password
   ^^^^^^^^^^^^

   
.. example:: **set-password** [**-h**] [**--password** *PWD* | **--gen-password**] *service*
   
   Set the password for a service.
   
   .. program:: restauth-service-set-password

   .. option:: --password PWD
      
      The password to use.
      
   .. option:: --gen-password
      
      Generate a password and print it to stdout.
      
   .. option:: service
      
      The name of the service.
      
.. only:: not man
   
   view
   ^^^^

   
.. example:: **view** [**-h**] *service*
   
   View details of a service.
   
   .. program:: restauth-service-view

   .. option:: service
      
      The name of the service.
      
