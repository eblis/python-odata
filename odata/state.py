# -*- coding: utf-8 -*-

from __future__ import print_function

import inspect
import itertools
from collections import OrderedDict
from typing import Optional

import rich
import rich.panel
import rich.table

from odata.property import PropertyBase, NavigationProperty


class EntityState(object):

    def __init__(self, entity):
        """:type entity: EntityBase """
        self.entity: "EntityBase" = entity
        self.dirty = []
        self.nav_cache = {}
        self.data = {}
        self.connection = None
        # does this object exist serverside
        self.persisted = False
        self.parent_navigation_url: Optional[str] = None  # for chaining objects, like OrderDetails.Order.Employee

    # dictionary access
    def __getitem__(self, item):
        return self.data[item]

    def __setitem__(self, key, value):
        self.data[key] = value

    def __contains__(self, item):
        return item in self.data

    def get(self, key, default):
        return self.data.get(key, default=default)

    def update(self, other):
        self.data.update(other)
    # /dictionary access

    def __repr__(self):
        return self.data.__repr__()

    def values(self):
        title = f"{self.entity.__odata_type__}"
        table = rich.table.Table(
            rich.table.Column("Properties", header_style="bold"),
            rich.table.Column("Values", header_style="bold"),
            row_styles=["dim", "none"],
            min_width=len(title),
            title=title)

        show_properties = []
        values = []
        for key, prop in self.properties:
            name = prop.name
            if prop.is_collection:
                name += "[]"
            if prop.primary_key:
                name += '*'
            if prop.name in self.dirty:
                name += ' (dirty)'
            show_properties.append(name)
            values.append(str(self.data[key]))
        for items in itertools.zip_longest(show_properties, values, fillvalue=""):
            table.add_row(*items)

        rich.print(table)

    def describe(self):
        table = rich.table.Table(
            rich.table.Column("Properties", header_style="bold"),
            # rich.table.Column(header="Property type", header_style="bold blue", style="dim blue"),
            rich.table.Column("Navigation properties", header_style="bold"),
            # rich.table.Column(header="Navigation property type", header_style="bold blue", style="dim blue"),
            row_styles=["dim", "none"],
            title='EntitySet: [red]{0}[/red]'.format(self.entity.__odata_collection__))

        panel = rich.panel.Panel(table,
            title=f"[green]{self.entity.__odata_type__}",
            subtitle=f"URL={self.instance_url or self.entity.__odata_url__()}", expand=False)

        show_properties = []
        # show_types = []
        for _, prop in self.properties:
            name = prop.name
            if prop.is_collection:
                name += "[]"
            if prop.primary_key:
                name += '*'
            if prop.name in self.dirty:
                name += ' (dirty)'

            show_properties.append(
                rich.console.Text.assemble(rich.console.Text(name), ": ", rich.console.Text(type(prop).__name__, style="dim blue", overflow="ellipsis"))
            )
            # show_types.append(type(prop).__name__)

        show_nav_properties = []
        # show_nav_types = []
        for _, prop in self.navigation_properties:
            name = prop.name
            if prop.is_collection:
                name += "[]"
            show_nav_properties.append(
                rich.console.Text.assemble(name, ": ", rich.console.Text(prop.entitycls.__name__, style="dim blue"), overflow="ellipsis"))

            # show_nav_types.append(prop.entitycls.__name__)

        for items in itertools.zip_longest(show_properties, show_nav_properties, fillvalue=""):
        # for items in itertools.zip_longest(show_properties, show_types, show_nav_properties, show_nav_types, fillvalue=""):
            table.add_row(*items)

        rich.print(panel)
        return table

    def reset(self):
        self.dirty = []
        self.nav_cache = {}

    @property
    def id(self):
        ids = []
        entity_name = self.entity.__odata_collection__
        if entity_name is None:
            return

        for prop_name, prop in self.primary_key_properties:
            value = self.data.get(prop.name)
            if value:
                ids.append((prop, str(prop.escape_value(value))))
        if len(ids) == 1:
            key_value = ids[0][1]
            return u'{0}({1})'.format(entity_name,
                                      key_value)
        if len(ids) > 1:
            key_ids = []
            for prop, key_value in ids:
                key_ids.append('{0}={1}'.format(prop.name, key_value))
            return u'{0}({1})'.format(entity_name, ','.join(key_ids))

    @property
    def instance_url(self):
        if self.id:
            return self.entity.__odata_url_base__ + self.id

    @property
    def properties(self):
        props = []
        cls = self.entity.__class__
        for key, value in inspect.getmembers(cls):
            if isinstance(value, PropertyBase):
                props.append((key, value))
        return props

    @property
    def primary_key_properties(self):
        pks = []
        for prop_name, prop in self.properties:
            if prop.primary_key is True:
                pks.append((prop_name, prop))
        return pks

    @property
    def navigation_properties(self):
        props = []
        cls = self.entity.__class__
        for key, value in inspect.getmembers(cls):
            if isinstance(value, NavigationProperty):
                props.append((key, value))
        return props

    @property
    def dirty_properties(self):
        rv = []
        for prop_name, prop in self.properties:
            if prop.name in self.dirty:
                rv.append((prop_name, prop))
        return rv

    def set_property_dirty(self, prop):
        if prop.name not in self.dirty:
            self.dirty.append(prop.name)

    def data_for_insert(self, omit_null_props=[]):
        return self._clean_new_entity(self.entity, omit_null_props)

    def data_for_update(self, omit_null_props=[]):
        update_data = OrderedDict()
        update_data['@odata.type'] = self.entity.__odata_type__

        for _, prop in self.dirty_properties:
            if prop.is_computed_value:
                continue

            update_data[prop.name] = self.data[prop.name]

        for prop_name, prop in self.navigation_properties:
            if prop.name in self.dirty:
                value = getattr(self.entity, prop_name, None)  # get the related object
                """:type : None | odata.entity.EntityBase | list[odata.entity.EntityBase]"""
                if value is not None:
                    key = '{0}@odata.bind'.format(prop.name)
                    if prop.is_collection:
                        update_data[key] = [i.__odata__.id for i in value]
                    else:
                        update_data[key] = value.__odata__.id
        
        update_data_filtered = {}
        for prop_name, prop in update_data.items():
            if omit_null_props is True or prop_name in omit_null_props:
                # Should omit unless not None
                if prop is None:
                    # Omit from request
                    continue
                update_data_filtered[prop_name] = prop

        return update_data_filtered

    def _clean_new_entity(self, entity, omit_null_props=[]):
        """:type entity: odata.entity.EntityBase """
        insert_data = OrderedDict()
        insert_data['@odata.type'] = entity.__odata_type__

        es = entity.__odata__
        for _, prop in es.properties:
            if prop.is_computed_value:
                continue

            insert_data[prop.name] = es[prop.name]

        # Allow pk properties only if they have values
        for _, pk_prop in es.primary_key_properties:
            if insert_data[pk_prop.name] is None:
                insert_data.pop(pk_prop.name)

        # Deep insert from nav properties
        for prop_name, prop in es.navigation_properties:
            if prop.foreign_key:
                insert_data.pop(prop.foreign_key, None)

            value = getattr(entity, prop_name, None)
            """:type : None | odata.entity.EntityBase | list[odata.entity.EntityBase]"""
            if value is not None:

                if prop.is_collection:
                    binds = []

                    # binds must be added first
                    for i in [i for i in value if i.__odata__.id]:
                        binds.append(i.__odata__.id)

                    if len(binds):
                        insert_data['{0}@odata.bind'.format(prop.name)] = binds

                    new_entities = []
                    for i in [i for i in value if i.__odata__.id is None]:
                        new_entities.append(self._clean_new_entity(i))

                    if len(new_entities):
                        insert_data[prop.name] = new_entities

                else:
                    if value.__odata__.id:
                        insert_data['{0}@odata.bind'.format(prop.name)] = value.__odata__.id
                        
                        # Put the foreign key back into the request for compatibility with 
                        #   systems that don't handle {entity} odata.bind correctly
                        try:
                            insert_data[prop.foreign_key] = getattr(value, prop.foreign_key)
                        except:
                           pass

                    else:
                        insert_data[prop.name] = self._clean_new_entity(value)

        insert_data_filtered = {}
        for prop_name, prop in insert_data.items():
            if omit_null_props is True or prop_name in omit_null_props:
                # Should omit unless not None
                if prop is None:
                    # Omit from request
                    continue
                insert_data_filtered[prop_name] = prop

        return insert_data_filtered
