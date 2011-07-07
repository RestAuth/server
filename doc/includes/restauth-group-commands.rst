.. only:: not man
   
   add
   ^^^

   
.. example:: **add** [**-h**] [**--service** *SERVICE*] *group*
   
   Add a new group.
   
   .. program:: restauth-group-add

   .. option:: --service SERVICE
      
      Act as if restauth-group was the service named SERVICE. If ommitted, act on groups that are not associated with any service.
      
   .. option:: group
      
      The name of the group.
      
.. only:: not man
   
   add-group
   ^^^^^^^^^

   
.. example:: **add-group** [**-h**] [**--service** *SERVICE*] [**--sub-service** *SERVICE*] *group* *subgroup*
   
   Make a group a subgroup of another group. The subgroup will inherit all memberships from the parent group.
   
   .. program:: restauth-group-add-group

   .. option:: --service SERVICE
      
      Act as if restauth-group was the service named SERVICE. If ommitted, act on groups that are not associated with any service.
      
   .. option:: --sub-service SERVICE
      
      Assume that the named subgroup is from SERVICE.
      
   .. option:: group
      
      The name of the group.
      
   .. option:: subgroup
      
      The name of the subgroup.
      
.. only:: not man
   
   add-user
   ^^^^^^^^

   
.. example:: **add-user** [**-h**] [**--service** *SERVICE*] *group* *username*
   
   Add a user to a group.
   
   .. program:: restauth-group-add-user

   .. option:: --service SERVICE
      
      Act as if restauth-group was the service named SERVICE. If ommitted, act on groups that are not associated with any service.
      
   .. option:: group
      
      The name of the group.
      
   .. option:: username
      
      The name of the user.
      
.. only:: not man
   
   list
   ^^^^

   
.. example:: **list** [**-h**]
   
   List all groups.
   
.. only:: not man
   
   rm
   ^^

   
.. example:: **rm** [**-h**] [**--service** *SERVICE*] *group*
   
   Remove a group.
   
   .. program:: restauth-group-rm

   .. option:: --service SERVICE
      
      Act as if restauth-group was the service named SERVICE. If ommitted, act on groups that are not associated with any service.
      
   .. option:: group
      
      The name of the group.
      
.. only:: not man
   
   rm-group
   ^^^^^^^^

   
.. example:: **rm-group** [**-h**] [**--service** *SERVICE*] [**--sub-service** *SERVICE*] *group* *subgroup*
   
   Remove a subgroup from a group. The subgroup will no longer inherit all memberships from a parent group.
   
   .. program:: restauth-group-rm-group

   .. option:: --service SERVICE
      
      Act as if restauth-group was the service named SERVICE. If ommitted, act on groups that are not associated with any service.
      
   .. option:: --sub-service SERVICE
      
      Assume that the named subgroup is from SERVICE.
      
   .. option:: group
      
      The name of the group.
      
   .. option:: subgroup
      
      The name of the subgroup.
      
.. only:: not man
   
   rm-user
   ^^^^^^^

   
.. example:: **rm-user** [**-h**] [**--service** *SERVICE*] *group* *username*
   
   Remove a user from a group.
   
   .. program:: restauth-group-rm-user

   .. option:: --service SERVICE
      
      Act as if restauth-group was the service named SERVICE. If ommitted, act on groups that are not associated with any service.
      
   .. option:: group
      
      The name of the group.
      
   .. option:: username
      
      The name of the user.
      
.. only:: not man
   
   view
   ^^^^

   
.. example:: **view** [**-h**] [**--service** *SERVICE*] *group*
   
   View details of a group.
   
   .. program:: restauth-group-view

   .. option:: --service SERVICE
      
      Act as if restauth-group was the service named SERVICE. If ommitted, act on groups that are not associated with any service.
      
   .. option:: group
      
      The name of the group.
      
