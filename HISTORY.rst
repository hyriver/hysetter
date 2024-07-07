=======
History
=======

0.2.0 (2024-XX-XX)
------------------

New features
~~~~~~~~~~~~
- Add two new AOI sources: ``mainstem_main`` and ``mainstem_tributaries``.
  The ``mainstem_main`` source gets the catchments of the main flowlines belonging
  to the given mainstem ID, whereas the ``mainstem_tributaries`` source gets the
  catchments of the tributaries of the main flowlines belonging to the given mainstem ID.


Internal Changes
~~~~~~~~~~~~~~~~
- Add the ``exceptions`` module to the high-level API.
- Switch to using the ``src`` layout instead of the ``flat`` layout
  for the package structure. This is to make the package more
  maintainable and to avoid any potential conflicts with other
  packages.
- Add artifact attestations to the release workflow.

0.1.1 (2024-05-30)
------------------

New features
~~~~~~~~~~~~
- Add support for getting StreamCat and NLDI catchment-level attributes.
  Target attributes can passed through ``streamcat_attrs`` and ``nldi_attrs``
  fields in the config file. Check out the
  `demo config file <https://github.com/hyriver/hysetter/blob/main/config_demo.yml>`__
  for more details.

Enhancements
~~~~~~~~~~~~
- Add a new method to the ``Config`` class called ``get_data`` to get the
  data efficiently by lazy loading functions and their dependencies.
- Refactored the CLI to use the new ``get_data`` method.

0.1.0 (2024-05-20)
------------------

- Initial release.
