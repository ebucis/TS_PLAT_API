# TS_PLAT_API

This project allows to access Tradestation Data through the GlobalDictionary. Thank you to JohnR@TS for providing the Global dictionary example used to create this. 

The python code must be run together with an EasyLanguage indicator that acts as a proxy.

Please use at your own risk. It is still work in progress and relies heavily in COM objects where improper shutdown can lead to TS platform uninteded consequences.

![Alt text](images/ts_plat_api.png?raw=true "TS PLAT API in action")

## Configuration

### Tradestation

1. Create an indicator using the code from ts_plat_api.el

2. Apply this indicator to any chart. In order to avoid work duplication or conflicts make sure to run it only once. It will throw an exception if it is used more than once.

### Python

In order to run the project the following external packages are used:

1. GlobalDictionary:
    This file requires that win32com (pywin32) be installed in your environment.

    Steps to install pywin32:

    1. Start a command line with administrator rights
    2. python -m pip install pywin32
    3. python pywin32_postinstall.py -install

    The location of pywin32_postinstall.py in my environment for example was:
    
    ~\AppData\Local\Programs\Python\Python38-32\Scripts\pywin32_postinstall.py 

    Python 3.8.0 (tags/v3.8.0:fa919fd, Oct 14 2019, 19:21:23)    

2. Reactive Extensions (RxPy3)
    * pip install RxPy3

3. FinPlot (for the chart):
    * pip install finplot

4. Debugpy (to create code breakpoints in multiple threads):
    * pip install debugpy

5. Other python packages
    * pip install pandas


## Take it for a spin

1. run ts_plat_api indicator in a chart in Tradestation first (any symbol, any timeframe)

2. run main.py in python

## main.py code
```python
from plotter import Plotter
from datahost import DataHost
import time

if __name__ == "__main__":
    dh = DataHost('BTCUSD', "BARS", "MINUTES", 1, "BARS", 1000)

    #we wait for history to be deployed...
    # TODO: create a more elegant way
    while dh.data is not None:
        print(f'receiving data....({len(dh.data)})')	
        time.sleep(2)

    #once history has been loaded, create chart
    plotter = Plotter(dh)

    #finplot blocks the main thread...no need to wait
```
