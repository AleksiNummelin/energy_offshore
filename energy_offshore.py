
from gsv import GSVRetriever, __version__ as gsv_version
from one_pass.opa import Opa
import sys              # for sys.argv
import os.path          # isfile
import xarray as xr     # merge
import numpy as np
import datetime
import time             # sleep

import yaml             # configuration
import threading

grid = { "NBS": "66/16/56/30", "Nordic": "70/-12/48/31", "stLawrence": "53/-70/43/-52", "Bohai": "42/117/37/123" }



def myGSVRequest(startstep=-1, length=1, date="20200120", time="0000", area=grid["Nordic"],
        levtype="sfc", levelist="", param=["10u", "10v", "2t"]):
 """Construct a GSV request with sensible default settings and configurability through function parameters.
 """
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
 """Construct an OPA request with sensible default settings and configurability through function parameters.
 """
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



def requestGSV2file(gsvrequest, filename=None):
"""Run a GSV request and save the received data to a file.
"""
    gsv = GSVRetriever()
    data = gsv.request_data(gsvrequest)
    if (filename is not None):
        data.to_netcdf(filename)
    data.close()


def requestGSV2speed(gsvrequest, uname, vname, sname, filename=None, oparequest=None):
"""Run a GSV request containing a velocity vector in component forms, calculate speed and save

The velocity component names should be given using the uname and vname parameters. The speed
will be calculated and stored with the name given using the sname parameter.
The resulting speed data will be optionally stored to a file, or passed on to the one-pass
algorithms package (OPA) for further processing.
"""
    gsv = GSVRetriever()
    data = gsv.request_data(gsvrequest)
    speed = velocity(data[uname], data[vname])
    speed_xr = xr.merge( [ speed.to_dataset(name=sname) ] )
    if (filename is not None):
        speed_xr.to_netcdf(filename)
    if (oparequest is not None):
        oparequest.compute(speed_xr.compute())
    data.close()
    del speed, speed_xr



def requestGSV2OPA(gsvrequest, filename=None, oparequests={}):
"""Run a GSV request containing a velocity vector in component forms and save or process in OPA
"""

    gsv = GSVRetriever()
    data = gsv.request_data(gsvrequest)
    if (filename is not None):
        data.to_netcdf(filename)
    for opareq in oparequests:
        opareq.compute(data[oparequests[opareq]].compute())
    data.close()




def handledays(start, end, chunk, HPCROOTDIR=""):
"""Run the energy offhore app for some number of days from start to end

Parameters
----------
start : array of integers specifying YYYY, MM and DD respectively
end : array of integers specifying YYYY, MM and DD respectively
chunk : The chunk number of this run (1, 2, 3 etc.)
"""
    print ("Beginning energy_offshore.handledays() from " +''.join(start)+" to "+''.join(end))
    print ("GSV version: " + gsv_version)
    print ("Chunk: "+chunk)
    date = datetime.datetime(int(start[0]), int(start[1]), int(start[2]))
    day_end = datetime.datetime(int(end[0]), int(end[1]), int(end[2]))
    gsv = GSVRetriever()

    OUT_PATH = HPCROOTDIR + "/tmp"
    CFG_PATH = HPCROOTDIR + "/git_project/conf/applications/energy_offshore"

    mygrid = grid["Nordic"]     ## Choose the grid for data requests that the app may run

    ## Set up OPA requests to calculate chosen data reductions using the one pass algorithms package
    opa_thresh10ws = Opa(myOPARequest("10ws", stat="thresh_exceed", thresh_exceed=[10, 18, 21, 25],
            stat_freq = "daily", output_freq = "monthly", path = OUT_PATH))
    opa_thresh100ws = Opa(myOPARequest("100ws", stat="thresh_exceed", thresh_exceed=[10, 18, 21, 25],
            stat_freq = "daily", output_freq = "monthly", path = OUT_PATH))
    opa_thresh_sithick = Opa(myOPARequest("avg_sithick", stat="thresh_exceed", thresh_exceed=[0.05, 0.4, 0.6],
            stat_freq = "daily", output_freq = "monthly", path = OUT_PATH, time_step = 60*24))
    opa_thresh_siconc = Opa(myOPARequest("avg_siconc", stat="thresh_exceed", thresh_exceed=[0.15, 0.9],
            stat_freq = "daily", output_freq = "monthly", path = OUT_PATH, time_step = 60*24))


    ## Take care that this app waits if a previous invocation is still running
    if (int(chunk) == 1):       # If first invocation of this run, set up
        with open(OUT_PATH + "/APP_last_chunk_finished.txt", 'w') as ffile:
            ffile.write(str(0))
    else:                       # Else check if the previous run is finished before continuing
        wait = True
        while (wait):
            with open(OUT_PATH + "/APP_last_chunk_finished.txt", 'r') as ffile:
                lastFinished = int(ffile.read())
            if (int(chunk) == lastFinished + 1):
                wait = False
            else:
                print ("WAITING - trying to start chunk "+str(chunk)+" but last finished is "+str(lastFinished))
                time.sleep(15)
    with open(OUT_PATH + "/APP_last_chunk_started.txt", 'w') as sfile:
        sfile.write(str(chunk))


    ## Loop over some number of days (often just one) and process data
    while date <= day_end:
        daystr = date.strftime("%Y_%m_%d")

        FILEPREFIX = daystr + "_T00_00_to_" + daystr + "_T23_00_"

        ## Handle 100 m winds from GSV in thread
        thread_100m = threading.Thread(target=requestGSV2speed, kwargs = {
                'gsvrequest' : myGSVRequest(date=date.strftime("%Y%m%d"), area=mygrid, time="0000/to/2300/by/0100",
                levtype="hl", levelist="100", param=["100u", "100v"]), 'uname' : "100u", 'vname' : "100v", 'sname' : "100ws",
                'filename' : OUT_PATH+"/"+daystr+"_T00_00_to_"+daystr+"_T23_00_100ws.nc",
                'oparequest' : opa_thresh100ws } )
        thread_100m.start()

        ## Handle ocean surface parameters from GSV in thread
        thread_oce = threading.Thread(target=requestGSV2OPA, kwargs = {
                'gsvrequest' : myGSVRequest(date=date.strftime("%Y%m%d"), area=mygrid, time="0000", levtype="o2d",
                param=["avg_sithick", "avg_siconc", "avg_siue", "avg_sivn", "avg_tos", "avg_sos", "avg_zos"]),
                'oparequests' : { opa_thresh_sithick: "avg_sithick", opa_thresh_siconc: "avg_siconc" },
                'filename' : OUT_PATH+"/"+daystr+"_T00_00_to_"+daystr+"_T23_00_oce.nc" } )
        thread_oce.start()

        ## Handle pressure level 1000 hPa parameters from GSV in thread
        thread_pl1000 = threading.Thread(target=requestGSV2file, kwargs = {
                'gsvrequest' : myGSVRequest(date=date.strftime("%Y%m%d"), area=grid["Nordic"],
                 time="0000/to/2300/by/0100", levtype="pl", levelist="1000", param=["t", "q", "clwc", "z"]),
                 'filename' : OUT_PATH+"/"+daystr+"_T00_00_to_"+daystr+"_T23_00_pl1000.nc" } )
        thread_pl1000.start()

        ## Handle surface winds from files in main thread
        u = xr.open_dataset(OUT_PATH + "/" + FILEPREFIX + "10u_raw_data.nc")['10u']
        v = xr.open_dataset(OUT_PATH + "/" + FILEPREFIX + "10v_raw_data.nc")['10v']
        ws = velocity(u, v)
        ws_out = xr.merge( [ ws.to_dataset(name="10ws") ] )
        ws_out.to_netcdf(OUT_PATH + "/" + FILEPREFIX + "10ws_raw_data.nc")
        opa_thresh10ws.compute(ws_out)
        u.close()
        v.close()
        ws_out.close()

        thread_100m.join()          ###
        thread_oce.join()           #
        thread_pl1000.join()        # Wait for all threads to finish

        date += datetime.timedelta(days=1)

    with open(OUT_PATH + "/APP_last_chunk_finished.txt", 'w') as ffile:
        ffile.write(str(chunk))


if __name__ == '__main__':
    energy_offshore(locals())
