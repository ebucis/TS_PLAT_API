import rx3
from rx3.subject import Subject
from GlobalDictionary import create
import time
import threading
from collections import deque


from pythoncom import (CoInitializeEx, CoUninitialize,
                       COINIT_MULTITHREADED, PumpWaitingMessages)


def _init(name, subject, facade):
    #global GD

    CoInitializeEx(COINIT_MULTITHREADED)    

    def on_data(key, value, action):
        subject.on_next(
            {
                'key' : key,
                'value' : value,
                'action' : action
            }
        )


    # Define events for GlobalDictionary 
    # Note the different function signatures for each event
    def GD_add(self, key, value, size):
        #print(f'*Add event for {self.name}* Key {key} added with value {value} -> New size: {size}')
        on_data(key, value, 'add')

    def GD_remove(self, key, size):
        #print(f'*Remove event for {self.name}* Removed key {key}')
        on_data(key, None, 'remove')
        

    def GD_change(self, key, value, size):
        #print(f'*Change event for {self.name}* Key {key} changed to {value}')
        on_data(key, value, 'change')

    def GD_clear(self):
        for key in GD.keys:
            GD_remove(self, key, 0)
        #print(f'*Clear event for {self.name}*')

    # Create global dictionary with optional events
    GD = create(name, add=GD_add, remove=GD_remove, change=GD_change, clear=GD_clear)

    def pump():
        # Prevent application from exiting and allow for handling of GlobalDictionary events
        while True:
            for chg in facade.get_changes():
                GD[chg['key']] = chg['value']
            PumpWaitingMessages()
            time.sleep(0.01)  # Avoids high CPU usage by not checking constantly

    pump()

    CoUninitialize()


def create_connection(name):
    '''
        dictionary to coordinate access between calling thread and 
        GlobalDictionary thread owner
    '''
    class FacadeDictionary:
        def __init__(self):
            self._changes = []
            self._data = {}

        def __setitem__(self, key, val):
            self._changes.append({
                    'key': key,
                    'value': val,
                    'action': 'set'
                })    

        def get_changes(self):
            chnges = self._changes
            self._changes = []
            return chnges


    class Connection():
        def __init__(self, _name, subject, dictionary):
            self.name = _name
            self.subject = subject
            self.dictionary = dictionary

    gd = FacadeDictionary()
    proxy = Subject()
    thread = threading.Thread(target=_init, args=(name, proxy,gd,), daemon=True)
    thread.start()
    #GD = _init(name, None, False)

    return Connection(name, proxy, gd)


if __name__ == "__main__":
    connection = create_connection("TS_PLAT_API")

    connection.subject.subscribe(
        lambda x: print("The value is {0}".format(x))
    )

    while True:
        if connection.dictionary is not None:
            connection.dictionary["Test"] = 25
        time.sleep(5)

    input("Enter any key")