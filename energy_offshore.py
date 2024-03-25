
from gsv import GSVRetriever, __version__ as gsv_version
from one_pass.opa import Opa
import sys              # for sys.argv
import os.path          # isfile
import xarray as xr     # merge
import numpy as np
import datetime

import yaml             # configuration


grid = { "NBS": "66/16/56/30", "Nordic": "70/-12/48/31", "stLawrence": "53/-70/43/-52", "Bohai": "42/117/37/123" }



def myGSVRequest(startstep=-1, length=1, date="20200120", time="0000", area=grid["Nordic"],
        levtype="sfc", levelist="", param=["10u", "10v", "2t"]):
    request = {
      "dataset": "climate-dt",
      "class": "d1",
      "type": "fc",
      "expver": "a0h3",     ## 30 year high-res historical run
      "stream": "clte",
      "activity": "CMIP6",
      "resolution": "high",
      "generation": "1",
      "realization": "1",
      "experiment": "hist",
      "model": "IFS-NEMO",
      "date": date,         ## This refers to when the run was started, must be 20200120 for FDB-long
      "time": time,         ## ditto
      "area": area,          # 56N, 16E to 66N, 30E
      "levtype": levtype,
      "param": param,
      "grid": ["0.1", "0.1"],    ### MAX RESOLUTION OF THIS GRID at equator is 0.225 x 0.225
      "method": "nn"               ### Options: nn, con (1st order conservative)
    }
    if (startstep != -1):
        request['step'] = str(startstep)+ "/to/" + str(startstep+length - 1)
    if (levelist != ""):
        request['levelist'] = levelist
    return request



## https://earth.bsc.es/gitlab/digital-twins/de_340/one_pass/-/blob/main/docs/source/the_data_request.rst
def myOPARequest(var, checkpoint_path="", save_path="", path="", stat_freq="daily", output_freq="daily",
        stat = "mean", percentile_list = None, thresh_exceed = None, time_step=60 ):

    save_checkpoints = save_saves = False
    if (path != ""):
        if (checkpoint_path == ""):
            checkpoint_path = path
        if (save_path == ""):
            save_path = path
    if (checkpoint_path != ""):
        save_checkpoints = True
    if (save_path != ""):
        save_saves = True

    oparequest = {
        "stat" : stat,
        "percentile_list" : percentile_list,
        "thresh_exceed" : thresh_exceed,
        "stat_freq": stat_freq,         ### "continuous", #daily",
        "output_freq": output_freq,     ## "daily",
        "time_step": time_step,
        "variable": var,                # "windspd",  # "2t",
        "save": save_saves,
        "checkpoint": save_checkpoints,
        "checkpoint_filepath": checkpoint_path,
        "save_filepath": save_path}
    return oparequest



def velocity(uvar, vvar):
    return np.sqrt(uvar**2 + vvar**2)

def thresh_exceed(var, thresh):
    result = var.where(var > thresh).notnull().astype(float).max('time')
    result_with_time = result.assign_coords(time = var.time[0])
    return result_with_time

def mean(var):
    result = var.mean(dim='time')
    result_with_time = result.assign_coords(time = var.time[0])
    return result_with_time

def max(var):
    result = var.max(dim='time')
    result_with_time = result.assign_coords(time = var.time[0])
    return result_with_time

def loadConfig(file, PATH=""):
    if isinstance(file, str):
        config = yaml.safe_load(open(PATH + "/" + file))
    elif isinstance(file, list):
        for f in file:
            config[f] = yaml.safe_load(open(PATH + "/" + file))
    return config



def handledays(start, end, chunk, HPCROOTDIR=""):

    print ("Beginning energy_offshore.handledays() from " +''.join(start)+" to "+''.join(end))
    print ("GSV version: " + gsv_version) ## gsv.__version__)
    print ("Chunk: "+chunk)
    date = datetime.datetime(int(start[0]), int(start[1]), int(start[2]))
    day_end = datetime.datetime(int(end[0]), int(end[1]), int(end[2]))
    gsv = GSVRetriever()

    OUT_PATH = HPCROOTDIR + "/tmp"
    CFG_PATH = HPCROOTDIR + "/git_project/conf/applications/energy_offshore"

    mygrid = grid["Nordic"]

    opa_thresh10ws = Opa(myOPARequest("10ws", stat="thresh_exceed", thresh_exceed=[10, 18, 21, 25],
            stat_freq = "daily", output_freq = "monthly", path = OUT_PATH))
    opa_thresh100ws = Opa(myOPARequest("100ws", stat="thresh_exceed", thresh_exceed=[10, 18, 21, 25],
            stat_freq = "daily", output_freq = "monthly", path = OUT_PATH))
    opa_thresh_sithick = Opa(myOPARequest("avg_sithick", stat="thresh_exceed", thresh_exceed=[0.05, 0.4, 0.6],
            stat_freq = "daily", output_freq = "monthly", path = OUT_PATH, time_step = 60*24))
    opa_thresh_siconc = Opa(myOPARequest("avg_siconc", stat="thresh_exceed", thresh_exceed=[0.15, 0.9],
            stat_freq = "daily", output_freq = "monthly", path = OUT_PATH, time_step = 60*24))


    while date <= day_end:
        daystr = date.strftime("%Y_%m_%d")

        FILEPREFIX = daystr + "_T00_00_to_" + daystr + "_T23_00_"

        ## Handle surface winds from files
        u = xr.open_dataset(OUT_PATH + "/" + FILEPREFIX + "10u_raw_data.nc")['10u']
        v = xr.open_dataset(OUT_PATH + "/" + FILEPREFIX + "10v_raw_data.nc")['10v']
        ws = velocity(u, v)
        ws_out = xr.merge( [ ws.to_dataset(name="10ws") ] )
        ws_out.to_netcdf(OUT_PATH + "/" + FILEPREFIX + "10ws_raw_data.nc")
        opa_thresh10ws.compute(ws_out)
        u.close()
        v.close()
        ws_out.close()

        ## Handle 100 m winds from GSV
        data100m = gsv.request_data(myGSVRequest(date=date.strftime("%Y%m%d"), area=mygrid,
                time="0000/to/2300/by/0100", levtype="hl", levelist="100", param=["100u", "100v"]))
        ws100tmp = velocity(data100m['100u'], data100m['100v'])
#        ws100 = ws100tmp.rename('100ws').to_dataset()
        ws100 = xr.merge( [ ws100tmp.to_dataset(name="100ws") ] )
        ws100.to_netcdf(OUT_PATH + "/" + daystr + "_T00_00_to_" + daystr + "_T23_00_100ws.nc")
        opa_thresh100ws.compute(ws100.compute())    ## .compute() added 20240323
        data100m.close()
        del ws100, ws100tmp

        ## Handle ocean surface parameters from GSV
        dataoce = gsv.request_data(myGSVRequest(date=date.strftime("%Y%m%d"), area=mygrid, time="0000",
                levtype="o2d", param=["avg_sithick", "avg_siconc", "avg_siue", "avg_sivn", "avg_tos", "avg_sos", "avg_zos"]))
        dataoce.to_netcdf(OUT_PATH + "/" + daystr + "_T00_00_to_" + daystr + "_T23_00_oce.nc")
        opa_thresh_sithick.compute(dataoce["avg_sithick"].compute())    ## This line threw error 25.3. 14:22
        opa_thresh_siconc.compute(dataoce["avg_siconc"].compute())
        dataoce.close()


        ## Handle pressure level 1000 hPa parameters from GSV
        data1000 = gsv.request_data(myGSVRequest(date=date.strftime("%Y%m%d"), area=grid["Nordic"],
                 time="0000/to/2300/by/0100", levtype="pl", levelist="1000", param=["t", "q", "clwc", "z"]))
#                time="0000/to/2300/by/0100", levtype="pl", levelist="1000", param=["u", "v", "t", "pv", "q", "r", "clwc"]))
        data1000.to_netcdf(OUT_PATH + "/" + daystr + "_T00_00_to_" + daystr + "_T23_00_pl1000.nc")
        data1000.close()

        date += datetime.timedelta(days=1)

if __name__ == '__main__':
    energy_offshore(locals())
