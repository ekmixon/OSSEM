#!/usr/bin/env python3

# Project: OSSEM Common Data Model
# Author: Roberto Rodriguez (@Cyb3rWard0g)
# License: GPLv3

import yaml
import glob
from os import path
from jinja2 import Template
import copy
import json

# ***********************************************
# ******** Processing OSSEM CDM Entities ********
# ***********************************************

print("[+] Processing entity files inside ../../OSSEM-CDM/schemas/entities directory")
# Open OSSEM CDM entity YML file
print("[+] Opening entity YML files..")
entity_files = glob.glob(path.join(path.dirname(__file__), '../../OSSEM-CDM/schemas/entities', "*.yml"))
entities_loaded = [yaml.safe_load(open(yf).read()) for yf in entity_files]

# Initializing Standard Entities Objects
all_standard_entities = {}

# ***** Process Initial Entity Attributes *****
for entity in entities_loaded:
    print(f"  [>] Processing {entity['name']}")
    # Initialize entity object to add initial standard fields
    entity_object = {
        "name": entity['name'],
        "prefix": entity['prefix'],
        "id": entity['id'],
        "extends_entities": entity['extends_entities'] if 'extends_entities' in entity.keys() else [],
        "description": entity['description'],
        "attributes": []
    }
    # Process entity attributes for each prefix assigned to an entity (Default snake_case format)
    if entity['attributes']: 
        for prefix in entity['prefix']:    
            for attribute in entity['attributes']:
                if prefix == attribute['name']:
                    field_name = attribute['name']
                else:
                    field_name = prefix + '_' + attribute['name']
                attribute_object = {
                    "name": field_name,
                    "type": attribute['type'],
                    "description": attribute['description'],
                    "sample_value": attribute['sample_value']
                }
                entity_object['attributes'].append(attribute_object)
    all_standard_entities[entity['name']] = entity_object

# ***** Process Extended Entities *****
# Loop through the dictionary with the initial standard objects
print("[+] Processing Entity Extensions..")
for k,v in all_standard_entities.items():
    # If the entity extends other entities
    if v['extends_entities']:
        print(f"  [>] Processing {k} extensions")
        # Loop through entity names that the current entity extends
        for entity in v['extends_entities']:
            print(f"  [>>] {entity}")
            # Make sure you process every prefix assigned to the entity being extended
            for prefix in all_standard_entities[entity]['prefix']:
                # Loop through every attribute of the current standardized entity
                for attribute in v['attributes']:
                    attribute_object = {
                        "name": prefix + '_' + attribute['name'],
                        "type": attribute['type'],
                        "description": attribute['description'],
                        "sample_value": attribute['sample_value']
                    }
                    # append extended standardized attributes to the extended entity
                    if attribute_object not in all_standard_entities[entity]['attributes']:
                        all_standard_entities[entity]['attributes'].append(attribute_object)
                    # Loop through extended entities -> extending other entities
                    for extentity in all_standard_entities[entity]['extends_entities']:
                        # Loop through every prefix also if the extended -> extended entities
                        for extprefix in all_standard_entities[extentity]['prefix']:
                            attribute_object = {
                                "name": extprefix + '_' + prefix + '_' + attribute['name'],
                                "type": attribute['type'],
                                "description": attribute['description'],
                                "sample_value": attribute['sample_value']
                            }
                            if attribute_object not in all_standard_entities[extentity]['attributes']:
                                all_standard_entities[extentity]['attributes'].append(attribute_object)

# ***** Creating Entity Files (snake_case) *****
#  Entity Jinja Template
entity_template = Template(open('templates/entity.md').read())
for k,v in all_standard_entities.items():
    # ******** Process Entities for DOCS ********
    entity_for_render = copy.deepcopy(v)
    entity_md = entity_template.render(entidad=entity_for_render)
    open(f"../../docs/cdm/entities/{v['name']}.md", 'w').write(entity_md)

# ***********************************************
# ******** Processing OSSEM CDM Tables **********
# ***********************************************

print("[+] Processing table files inside ../../OSSEM-CDM/schemas/tables directory")
# Open OSSEM CDM Table YML file
print("[+] Opening table YML files..")
table_files = glob.glob(path.join(path.dirname(__file__), '../../OSSEM-CDM/schemas/tables', "*.yml"))
tables_loaded = [yaml.safe_load(open(yf).read()) for yf in table_files]

# Initializing Standard Table Objects
all_standard_tables = {}

# Loop through every single table (Dictionary)
for table in tables_loaded:
    print(f"  [>] Processing Table {table['name']}")
    table_object = {
        "name": table['name'],
        "id": table['id'],
        "description": table['description'],
        "attributes": []
    }
    # Looping through every entity defined for the table
    for entity in table['entities']:
        # If the entity value is just a name, then take all the attributes associated with the entity
        if not isinstance(entity, dict):
            # Entity label for every entity attribute are added to table
            entity_field = {"entity": entity}
            print(f"  [>>] Processing Entity {entity}")
            for att in all_standard_entities[entity]['attributes']:
                if "entity" not in att:
                    att.update(entity_field)
                # Append attribute to table object
                table_object['attributes'].append(att)
        # if the entity value is a dictionary, that means that the table is selecting specific attributes
        # from entities or adding custom ones to it
        else:
            print(f"  [>>] Processing Entity {entity['name']}")
            # If the entity name is custom, then we are adding custom entities and attributes
            # that do not exist in OSSEM
            if entity['name'] == 'custom':
                for subentity in entity['entities']:
                    # Entity label for every entity attribute are added to table
                    entity_field = {"entity": subentity['name']}
                    for subprefix in subentity['prefix']:
                        for eattribute in subentity['attributes']:
                            eattribute['name'] = subprefix + '_' + eattribute['name']
                            # Entity label applied to attribute
                            # We do an if in case the label has been applied already by other means
                            eattribute.update(entity_field)
                            # Append attribute to table object
                            table_object['attributes'].append(eattribute)
            # Process the rest of the entities in dictionary format
            else:
                entity_field = {"entity": entity['name']}
                for satt in all_standard_entities[entity['name']]['attributes']:
                    for att in entity['attributes']:
                        # Check prefix for each dictionary
                        for prefix in entity['prefix']:
                            # simply create field by taking prefix and attribute
                            field_name = prefix + '_' + att
                            # check if field names match
                            if field_name == satt['name']:
                                # Entity label applied to attribute
                                # We do an if in case the label has been applied already by other means
                                satt.update(entity_field)
                                # Append attribute to table object
                                table_object['attributes'].append(satt)
    all_standard_tables[table['name']] = table_object
# ***** Creating Table Files (snake_case) *****
# Entity Jinja Template
table_template = Template(open('templates/table.md').read())
for k,v in all_standard_tables.items():
    # ******** Process Entities for DOCS ********
    table_for_render = copy.deepcopy(v)
    table_md = table_template.render(table_metadata=table_for_render)
    open(f"../../docs/cdm/tables/{v['name']}.md", 'w').write(table_md)

# ***********************************************
# ********** Updating TOC File ******************
# ***********************************************

# ******* Initial TOC Template ********
print("[+] Updating Jupyter Book TOC file..")
with open('templates/toc_template.json') as json_file:
    toc_template = json.load(json_file)

# ******* Process Entities *******
print("  [>] Updating Entities sections..")
for d in toc_template:
    if 'part' in d and d['part'] == 'Common Data Model':
        for k,v in sorted(all_standard_entities.items()):
            # ******** Process Entities for TOC ********
            entity_dict = {"file" : f"cdm/entities/{v['name']}"}
            d['chapters'][2]['sections'].append(entity_dict)

# ******* Process Tables *******
print("  [>] Updating Tables sections..")
for d in toc_template:
    if 'part' in d and d['part'] == 'Common Data Model':
        for k,v in all_standard_tables.items():
            # ******** Process Entities for TOC ********
            entity_dict = {"file" : f"cdm/tables/{v['name']}"}
            d['chapters'][3]['sections'].append(entity_dict)

print("[+] Writing final TOC file for Jupyter book..")
with open(r'../../docs/_toc.yml', 'w') as file:
    yaml.dump(toc_template, file, sort_keys=False)


# ***********************************************
# ******** Processing OSSEM DM ******************
# ***********************************************

# Author: Jose Rodriguez (@Cyb3rPandaH)
# License: GNU General Public License v3 (GPLv3)
from attackcti import attack_client
import pandas as pd
from pandas import json_normalize
pd.set_option("max_colwidth", None)
yaml.Dumper.ignore_aliases = lambda *args : True

# ******** Process Relationships yaml Files ****************
# Aggregating relationships yaml files (all relationships and ATT&CK)
print("[+] Opening relationships yaml files..")
relationships_files = glob.glob(path.join(path.dirname(__file__), "../../OSSEM-DM/relationships", "[!_]*.yml"))
all_relationships_files = []
attack_relationships_files = []

print("[+] Creating python lists (all relationships and ATT&CK) with yaml files content..")
for relationship_file in relationships_files:
    relationship_yaml = yaml.safe_load(open(relationship_file).read())
    all_relationships_files.append(relationship_yaml)
    if relationship_yaml['attack'] != None:
        attack_relationships_files.append(relationship_yaml)

# Creating ATT&CK data sources to event mappings readme file
print("[+] Creating ATT&CK data sources to event mappings readme file..")
data_sources_event_mappings_template = Template(open('templates/attack_ds_event_mappings.md').read())
data_sources_event_mappings_render = copy.deepcopy(attack_relationships_files)
data_sources_event_mappings_markdown = data_sources_event_mappings_template.render(ds_event_mappings=data_sources_event_mappings_render)
open('../../docs/dm/mitre_attack/attack_ds_events_mappings.md', 'w').write(data_sources_event_mappings_markdown)

# Creating OSSEM relationships to events readme file
print("[+] Creating OSSEM relationships to events readme file..")
ossem_event_mappings_template = Template(open('templates/ossem_relationships_to_events.md').read())
ossem_event_mappings_render = copy.deepcopy(all_relationships_files)
ossem_event_mappings_markdown = ossem_event_mappings_template.render(ds_event_mappings=ossem_event_mappings_render)
open('../../docs/dm/ossem_relationships_to_events.md', 'w').write(ossem_event_mappings_markdown)