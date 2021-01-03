"""
    GlobalDictionary.py: A module for interfacing with a TradeStation
    Easylanguage GlobalDictionary through a COM object.

    This file requires that win32com (pywin32) be installed in your environment.

    Steps to install pywin32:

    1. Start a command line with administrator rights
    2. python -m pip install pywin32
    3. python pywin32_postinstall.py -install

    The location of pywin32_postinstall.py in my environment for example was:
    
    ~\AppData\Local\Programs\Python\Python38-32\Scripts\pywin32_postinstall.py 

    Python 3.8.0 (tags/v3.8.0:fa919fd, Oct 14 2019, 19:21:23)

"""

__author__ = "JohnR"
__date__ = "01/02/2021" #by ebucis
__version__ = "00.00.06" #by ebucis

'''
moved the COM dispatch to run in the calling thread context    
'''

from win32com import client
import pythoncom
import re
import signal
import time
import signal
import sys
import xml.etree.ElementTree as ET
import threading

# Constants used for encoding and decoding values in a GlobalDictionary
_PREFIX = 'v'

_TYPE_BOOL = _PREFIX + '\x02'
_TYPE_STRING = _PREFIX + '\x03'
_TYPE_INT = _PREFIX + '\x04'
_TYPE_DOUBLE = _PREFIX + '\x07'

_TYPE_BOOL_C = _PREFIX + 'B'
_TYPE_STRING_C = _PREFIX + 'S'
_TYPE_INT_C = _PREFIX + 'I'
_TYPE_DOUBLE_C = _PREFIX + 'D'


_storage = {}



class GlobalDictionary:
    """Use the factory function "create" listed below to create a GlobalDictionary instance"""

    _instances = set() # Store GlobalDictionary instances to help with graceful shutdown

    def __init__(self, name, events):

        thid = threading.current_thread().ident
        if thid in _storage:
            _GlobalDictionaries = _storage[thid]
        else:
            _GlobalDictionaries = client.gencache.EnsureDispatch("GSD.ELDictionaries")
            _storage[thid] = _GlobalDictionaries

        self.name = name
        self._GD = _GlobalDictionaries.GetDictionary(name)
        self._handler = client.WithEvents(self._GD, events)
        type(self)._instances.add(self) # Store this instance in the class set _instances

    def __contains__(self, key):
        return self.contains(key)

    def __del__(self):
        try:
            self._handler.close() 
            type(self)._instances.remove(self)
        except:
            pass

    def __getitem__(self, key):
        return self.get(key)
    
    def __len__(self):
        return self.size

    def __setitem__(self, key, val):
        if self.contains(key):
            self.set(key, val)
        else: 
            self.add(key, val) 

    def add(self, key, val):
        return self._GD.Add(key, _encode_value(val))

    def clear(self):
        self._GD.Clear()

    def contains(self, key):
        return _decode_value(self._GD.GetValue(key, "", 0)) != None 

    def get(self, key):
        return _decode_value(self._GD.GetValue(key, "", 0))

    def remove(self, key):
        self._GD.Remove(key)

    def set(self, key, val):
        self._GD.SetValue(key, _encode_value(val)) 
    
    @property
    def keys(self):
        keys = []
        for i in range(self.size):
            key = self._GD.GetKeyByIndex(i, key="")
            if key != "":
                keys.append(key)
        return keys 
    
    @property
    def size(self):
        return self._GD.size
    
    @property
    def values(self):
        vals = []
        for i in range(self.size):
            val = self._GD.GetValueByIndex(i, value="")
            decoded_value = _decode_value(val)
            if decoded_value != None:
                vals.append(decoded_value)
        return vals

    # Property aliases
    count = size

    # Method aliases
    add_value = add
    get_value = get
    set_value = set 


def create(name, add=None, remove=None, change=None, clear=None):
    """Factory function used to create a GlobalDictionary instance
       All event handlers are optional
    """

    class GDEvents:
        """Defines events for GlobalDictionary"""

        def __init__(self):
            self.name = name

        def OnAdd(self, key, value, size):
            if add:
                add(self, key, _decode_value(value), size)

        def OnRemove(self, key, size):
            if remove:
                remove(self, key, size)

        def OnChange(self, key, value, size):
            if change:
                change(self, key, _decode_value(value), size)

        def OnClear(self):
            if clear:
                clear(self)

    return GlobalDictionary(name, GDEvents)

def XML_Fix(data):
    """Replaces special characters, used to identify value types, in XML string.
    Without replacing these special characters, the XML string is not valid XML.
    """ 
    data = data.replace(f'Value="{_TYPE_BOOL}', f'Value="{_TYPE_BOOL_C}')
    data = data.replace(f'Value="{_TYPE_STRING}', f'Value="{_TYPE_STRING_C}')
    data = data.replace(f'Value="{_TYPE_INT}', f'Value="{_TYPE_INT_C}')
    data = data.replace(f'Value="{_TYPE_DOUBLE}', f'Value="{_TYPE_DOUBLE_C}')

    return data

def _encode_value(data):
    """Encodes data to be used as a GlobalDictionary value"""

    if type(data) is bool:
        return f'{_TYPE_BOOL}{str(data).lower()}'
    elif type(data) is float:
        return f'{_TYPE_DOUBLE}{str(data)}'
    elif type(data) is int:
        return f'{_TYPE_INT}{str(data)}'
    elif type(data) is str:
        return f'{_TYPE_STRING}{data}'
    elif type(data) is list:
        return _encode_list(data)
    elif type(data) is dict:
        return _encode_dictionary(data)
    else:
        raise Exception(
            f'Data to encode should be of type bool, float, int, str, list, or dict.')


def _decode_value(data):
    """Decodes a GlobalDictionary value to a Python data type. Since the method
       GetValue returns a 2-element tuple (value, size), if the data supplied is a 
       tuple, index 0 is decoded. 
    """

    if type(data) is tuple:
        data = data[0]

    # Key does not exist
    if data == '0' or data == "":
        return None
    
    elif data[0] == _PREFIX:

        encoding = data[:2]
        value = data[2:]

        if encoding == _TYPE_DOUBLE or encoding == _TYPE_DOUBLE_C:
            return float(value)
        elif encoding == _TYPE_STRING or encoding == _TYPE_STRING_C:
            return value
        elif encoding == _TYPE_INT or encoding == _TYPE_INT_C:
            return int(value)
        elif encoding == _TYPE_BOOL or encoding == _TYPE_BOOL_C:
            return value == "true"
        else:
            return data

    elif data.startswith("<elsystem.collections.vector>"):
        return _decode_vector(data)
    elif data.startswith("<elsystem.collections.dictionary>"):
        return _decode_dictionary(data)
    else:
        return data

def _decode_dictionary(data, sub=False):
    """Decodes a GlobalDictionary dictionary (XML like string) to a Python dictionary.
       Note: The returned dictionary keys may contain varying nested lists/dictionaries.
    """

    main_dict = {}

    if sub:
        # We are decoding a sub-dictionary, XML is assumed compliant
        tree = data
    else:
        fixed_data = XML_Fix(data)
        tree = ET.fromstring(fixed_data) 

    for child in tree:
        for pair in child:
            if len(pair) == 2:
                key = _decode_value(pair[0].attrib['Value'])
                val = None
                if 'Type' in pair[1].attrib: 
                    collection_type = pair[1].attrib['Type']
                    if collection_type == 'elsystem.collections.dictionary': # Handle sub-dictionary
                        val = _decode_dictionary(data=pair[1], sub=True)
                    elif collection_type == 'elsystem.collections.vector': # Handle sub-vector
                        val = _decode_vector(data=pair[1], sub=True)
                else: # Handle normal pair
                    val = _decode_value( pair[1].attrib['Value'] )
                main_dict[key] = val

    return main_dict

def _decode_vector(data, sub=False):
    """Decodes a GlobalDictionary vector (XML like string) into a Python list.
       Note: The returned list could be a list with varying nested lists/dictionaries.
    """
    
    main_list = []

    if sub: 
        # We are decoding a sub-vector, XML is assumed compliant
        tree = data
    else:
        fixed_data = XML_Fix(data)
        tree = ET.fromstring(fixed_data)

    for child in tree:
        if 'Value' in child.attrib and child.attrib['Name'] != 'count': # There will never be 'Value' without a 'Name'
            decoded_value = _decode_value(child.attrib['Value'])
            main_list.append(decoded_value)
        elif 'Type' in child.attrib:
            collection_type = child.attrib['Type'] 
            if collection_type == 'elsystem.collections.vector':
                sub_list = _decode_vector(data=child, sub=True)
                main_list.append(sub_list)
            elif collection_type == 'elsystem.collections.dictionary':
                sub_dict = _decode_dictionary(child, sub=True)
                main_list.append(sub_dict) 

    return main_list

def _encode_dictionary(data, name="Second", sub=False):
    """Encodes a Python dictionary to be used as an EasyLanguage dictionary.
    If sub is True, a sub-dictionary is returned as an XML element.
    If sub is False, a string representing the entire XML structure is returned. 

    Example when sub = True: 

        <Field Name="Second" Type="elsystem.collections.dictionary">
            <Field Name="Items" Type="elsystem.collections.vector">
                <Field Name="E0" Type="elsystem.collections.pair">
                    <Field Name="First" Value="v\x03a" />
                    <Field Name="Second" Value="v\x041" />
                </Field>
                <Field Name="E1" Type="elsystem.collections.pair">
                    <Field Name="First" Value="v\x03b" />
                    <Field Name="Second" Value="v\x042" />
                </Field>
                <Field Name="E2" Type="elsystem.collections.pair">
                    <Field Name="First" Value="v\x03c" />
                    <Field Name="Second" Value="v\x043" />
                </Field>
                <Field Name="count" Value="v\x043" />
            </Field>
        </Field>
    
    Example when sub = False: 

        <elsystem.collections.dictionary>
            <Field Name="Items" Type="elsystem.collections.vector">
                <Field Name="E0" Type="elsystem.collections.pair">
                        <Field Name="First" Value="v\x03DOUBLE"/>
                        <Field Name="Second" Value="v\x073.141"/>
                </Field>
                <Field Name="E1" Type="elsystem.collections.pair">
                    <Field Name="First" Value="v\x03INT"/>
                    <Field Name="Second" Value="v\x048"/>
                </Field>
                <Field Name="E2" Type="elsystem.collections.pair">
                    <Field Name="First" Value="v\x03STRING"/>
                    <Field Name="Second" Value="v\x03test"/>
                </Field>
                <Field Name="count" Value="v\x043"/>
            </Field>
        </elsystem.collections.dictionary>

    """

    if sub:
        root = ET.Element("Field", {"Name": f'{name}', "Type": "elsystem.collections.dictionary"})
    else: 
        root = ET.Element("elsystem.collections.dictionary")

    items = ET.SubElement(root, 'Field', {'Name': 'Items', 'Type': 'elsystem.collections.vector'})

    index = 0

    for key, val in data.items():

        pair = ET.SubElement(items, 'Field', {'Name': f'E{index}', 'Type': 'elsystem.collections.pair'})
       
        if type(val) == dict:
            ET.SubElement(pair, 'Field', {'Name': 'First', 'Value': _encode_value(key)}) 
            sub_dict = _encode_dictionary(data=val, name="Second", sub=True)
            pair.append(sub_dict)
        elif type(val) == list:
            ET.SubElement(pair, 'Field', {'Name': 'First', 'Value': _encode_value(key)}) 
            sub_vec = _encode_list(data=val, name=F'E{index}', sub=True)
            pair.append(sub_vec)
        else:
            ET.SubElement(pair, 'Field', {'Name': 'First', 'Value': _encode_value(key)}) 
            ET.SubElement(pair, 'Field', {'Name': 'Second', 'Value': _encode_value(val)}) 

        index += 1

    ET.SubElement(items, 'Field', {'Name': 'count', 'Value': _encode_value(index)})

    if sub:
        return root 
    else:
        return ET.tostring(root)


def _encode_list(data, name="", sub=False):
    """Encodes a Python list be used as an EasyLanguage Vector. 
    If sub is True, a sub-dictionary is returned as an XML element.
    If sub is False, a string representing the entire XML structure is returned. 
    
    Example when sub = True: 

        <Field Name="E2" Type="elsystem.collections.vector">
            <Field Name="E0" Value="v\x03Test1"" />
            <Field Name="E1" Value="v\x03Test2"" />
            <Field Name="count" Value="v\x042" />
        </Field>
    
    Example when sub = False: 

        <elsystem.collections.vector>
            <Field Name="E0" Value="v\x041" />
            <Field Name="E1" Value="v\x042" />
            <Field Name="E2" Value="v\x043" />
            <Field Name="E3" Type="elsystem.collections.vector">
                <Field Name="E0" Value="v\x041" />
                <Field Name="E1" Value="v\x042" />
                <Field Name="E2" Type="elsystem.collections.vector">
                    <Field Name="E0" Value="v\x03Test1"" />
                    <Field Name="E1" Value="v\x03Test2"" />
                    <Field Name="count" Value="v\x042" />
                </Field>
                <Field Name="count" Value="v\x043" />
            </Field>
            <Field Name="count" Value="v\x044" />
        </elsystem.collections.vector>

    """

    if sub:
        root = ET.Element("Field", {"Name": f'{name}', "Type": "elsystem.collections.vector"})
    else:
        root = ET.Element("elsystem.collections.vector")

    index = 0

    for val in data:

        if type(val) == dict:
            sub_vec = _encode_dictionary(data=val, name=f'E{index}', sub=True)
            root.append(sub_vec)
        elif type(val) == list:
            sub_vec = _encode_list(data=val, name=F'E{index}', sub=True)
            root.append(sub_vec)
        else:
            ET.SubElement(root, 'Field', {'Name': f'E{index}', 'Value': _encode_value(val)})

        index += 1
    
    ET.SubElement(root, 'Field', {'Name': 'count', 'Value': _encode_value(index)})

    if sub:
        return root
    else:
        return ET.tostring(root)

def _shutdown():
    """Gracefully deletes all GlobalDictionary instances and shuts down event handlers"""    
    for GD in GlobalDictionary._instances:
        print("\nCleaning up:", GD.name)
        GD._handler.close()
        del GD

    print("Shutting down")
  
    sys.exit(0)

def _signal_handler(sign, frame):
    """Handle closing signals"""
    _shutdown()

signal.signal(signal.SIGINT, _signal_handler)
signal.signal(signal.SIGTERM, _signal_handler)