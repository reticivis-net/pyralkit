================
pyralkit package
================

Client
=============

.. autoclass:: pyralkit.client.PKClient

    .. automethod:: close

Systems
-------
    .. automethod:: pyralkit.client.PKClient.get_system
    .. automethod:: pyralkit.client.PKClient.update_system
    .. automethod:: pyralkit.client.PKClient.get_system_settings
    .. automethod:: pyralkit.client.PKClient.update_system_settings
    .. automethod:: pyralkit.client.PKClient.get_system_guild_settings
    .. automethod:: pyralkit.client.PKClient.update_system_guild_settings

Members
-------
    .. automethod:: pyralkit.client.PKClient.get_system_members
    .. automethod:: pyralkit.client.PKClient.create_member
    .. automethod:: pyralkit.client.PKClient.get_member
    .. automethod:: pyralkit.client.PKClient.update_member
    .. automethod:: pyralkit.client.PKClient.delete_member
    .. automethod:: pyralkit.client.PKClient.get_member_groups
    .. automethod:: pyralkit.client.PKClient.add_member_to_groups
    .. automethod:: pyralkit.client.PKClient.remove_member_from_groups
    .. automethod:: pyralkit.client.PKClient.overwrite_member_groups
    .. automethod:: pyralkit.client.PKClient.get_member_guild_settings
    .. automethod:: pyralkit.client.PKClient.update_member_guild_settings

Groups
------
    .. automethod:: pyralkit.client.PKClient.get_system_groups
    .. automethod:: pyralkit.client.PKClient.create_group
    .. automethod:: pyralkit.client.PKClient.get_group
    .. automethod:: pyralkit.client.PKClient.update_group
    .. automethod:: pyralkit.client.PKClient.delete_group
    .. automethod:: pyralkit.client.PKClient.get_group_members
    .. automethod:: pyralkit.client.PKClient.add_members_to_groups
    .. automethod:: pyralkit.client.PKClient.remove_members_from_groups
    .. automethod:: pyralkit.client.PKClient.overwrite_group_members

Switches
--------
    .. automethod:: pyralkit.client.PKClient.get_system_switches
    .. automethod:: pyralkit.client.PKClient.get_current_system_fronters
    .. automethod:: pyralkit.client.PKClient.create_switch
    .. automethod:: pyralkit.client.PKClient.get_switch
    .. automethod:: pyralkit.client.PKClient.update_switch
    .. automethod:: pyralkit.client.PKClient.update_switch_members
    .. automethod:: pyralkit.client.PKClient.delete_switch

Misc
----
    .. automethod:: pyralkit.client.PKClient.get_proxied_message_information

Models
=============

.. automodule:: pyralkit.models
   :members:
   :undoc-members:
   :show-inheritance:

Errors
=============

.. automodule:: pyralkit.errors
   :members:
   :undoc-members:
   :show-inheritance:


