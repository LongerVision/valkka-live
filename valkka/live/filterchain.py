"""
filterchain.py : Manage and group Valkka filterchains

Copyright 2018 Sampsa Riikonen

Authors: Sampsa Riikonen

This file is part of the Valkka Live video surveillance program

Valkka Live is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License along with this program.  If not, see <https://www.gnu.org/licenses/> 

@file    filterchain.py
@author  Sampsa Riikonen
@date    2018
@version 0.8.0 
@brief   Manage and group Valkka filterchains
"""

from PySide2 import QtWidgets, QtCore, QtGui # Qt5
import sys
from valkka.live.datamodel import DataModel
from valkka.live.gpuhandler import GPUHandler
from valkka.live import constant
from valkka.api2.chains import ManagedFilterchain, ManagedFilterchain2, LiveManagedFilterchain, USBManagedFilterchain
from valkka.api2.threads import LiveThread, USBDeviceThread
from valkka.api2.tools import parameterInitCheck


class FilterChainGroup:
    """Manage a group of filterchains
    """
    
    parameter_defs = {
        "datamodel"        : DataModel,
        "livethread"       : LiveThread,
        "usbthread"        : USBDeviceThread,
        "gpu_handler"      : GPUHandler,
        "verbose"          : (bool, False),
        "cpu_scheme"       : None
        }
    
    
    def __init__(self, **kwargs):
        parameterInitCheck(FilterChainGroup.parameter_defs, kwargs, self)
        self.pre = self.__class__.__name__ + " : "
        self.chains = []
        self.closed = False
        
        
    def __del__(self):
        if not self.closed:
            self.close()
        
        
    def close(self):
        self.closed = True
        self.reset()
        
        
    def reset(self):
        # start closing all threads simultaneously
        for chain in self.chains:
            chain.requestClose()
        # wait until all threads closed
        for chain in self.chains:
            chain.waitClose()
        self.chains = []
        
        
    def read(self):
        """Reads all devices from the database and creates filterchains
        
        TODO: we can, of course, just modify the added / removed cameras
        """
        self.reset()
        for dic in self.datamodel.camera_collection.get(): # TODO: search directly for RTSPCameraRow
            if (self.verbose): print(self.pre, "read : dic", dic)
            
            if (dic["classname"] == DataModel.RTSPCameraRow.__name__):
                affinity = -1
                if self.cpu_scheme:
                    affinity = self.cpu_scheme.getAV()
                
                dic.pop("classname")
                device = DataModel.RTSPCameraDevice(**dic) # a neat object with useful methods
                
                print("FilterChainGroup : read : slot    =", device.getLiveMainSlot())
                print("FilterChainGroup : read : address =", device.getMainAddress())
                print("FilterChainGroup : read : _id     =", device._id)
                
                # chain = ManagedFilterchain( # decoding and branching the stream happens here
                # chain = ManagedFilterchain2( # decoding and branching the stream happens here
                chain = LiveManagedFilterchain( # decoding and branching the stream happens here
                    livethread  = self.livethread,
                    openglthreads
                                = self.gpu_handler.openglthreads,
                    address     = device.getMainAddress(),
                    slot        = device.getLiveMainSlot(),
                    _id         = device._id,
                    affinity    = affinity,
                    msreconnect = 10000,
                    # verbose     = True,
                    verbose     =False,
                    
                    shmem_image_dimensions = constant.shmem_image_dimensions,
                    shmem_n_buffer = constant.shmem_n_buffer,
                    shmem_image_interval = constant.shmem_image_interval
                )
                self.chains.append(chain) # important .. otherwise chain will go out of context and get garbage collected
                
            elif (dic["classname"] == DataModel.USBCameraRow.__name__):
                affinity = -1
                if self.cpu_scheme:
                    affinity = self.cpu_scheme.getAV()
                
                dic.pop("classname")
                device = DataModel.USBCameraDevice(**dic) # a neat object with useful methods
                
                print("FilterChainGroup : read : slot    =", device.getLiveMainSlot())
                print("FilterChainGroup : read : address =", device.getMainAddress())
                print("FilterChainGroup : read : _id     =", device._id)
                
                chain = USBManagedFilterchain( # decoding and branching the stream happens here
                    usbthread   = self.usbthread,
                    openglthreads
                                = self.gpu_handler.openglthreads,
                    address     = device.getMainAddress(),
                    slot        = device.getLiveMainSlot(),
                    _id         = device._id,
                    affinity    = affinity,
                    msreconnect = 10000,
                    # verbose     = True,
                    verbose     =False,
                    
                    shmem_image_dimensions = constant.shmem_image_dimensions,
                    shmem_n_buffer = constant.shmem_n_buffer,
                    shmem_image_interval = constant.shmem_image_interval
                )
                self.chains.append(chain) # important .. otherwise chain will go out of context and get garbage collected
                



    def update(self):
        """Reads all devices from the database.  Creates new filterchains and removes old ones
        
        TODO: currently this is broken: if user changes any other field than the ip address, the cameras don't get updated
        """
        raise(AssertionError("out of date"))
        
        new_ids = []
        old_ids = []
        
        # collect old ip addresses
        for chain in self.chains:
            if (self.verbose): print(self.pre, "old :", chain, chain.get__id(), chain.get_address(), chain._id)
            old_ids.append(chain.get__id())
            
        # collect devices
        devices = []
        for dic in self.datamodel.camera_collection.get():
            if (self.verbose): print(self.pre, "update : dic", dic)
            if (dic["classname"] == DataModel.RTSPCameraRow.__name__):
                devices.append(dic)
            
        devices_by_id={}
        for dic in devices: # DataModel.RTSPCameraRow instances
            _id = dic["_id"]
            new_ids.append(_id)
            devices_by_id[_id] = dic
        
        if (self.verbose):
            print(self.pre, "update : new_ids =", new_ids)
            print(self.pre, "update : old_ids =", old_ids)
        
        add_list = list(set(new_ids).difference(set(old_ids))) # cams to be added
        rem_list = list(set(old_ids).difference(set(new_ids))) # cams to be removed
        
        if (self.verbose):
            print(self.pre, "update : add_list =", add_list)
            print(self.pre, "update : rem_list =", rem_list)
        
        # purge removed chains
        for i, chain in enumerate(self.chains):
            if (chain.get__id() in rem_list):
                chain_ = self.chains.pop(i)
                if (self.verbose): print(self.pre, "closing chain", chain_)
                chain_.close()
        
        # add new chains
        for new_address in add_list:
            dic = devices_by_id[new_address]
            chain = ManagedFilterchain( # decoding and branching the stream happens here
                livethread  = self.livethread,
                openglthreads
                            = self.gpu_handler.openglthreads,
                address     = DataModel.RTSPCameraRow.getMainAddressFromDict(dic),
                slot        = dic["slot"],
                _id         = dic["_id"],
                # affinity    = a,
                msreconnect = 10000,
                verbose = True
            )
            if (self.verbose): print(self.pre, "adding chain", chain)
            self.chains.append(chain) # important .. otherwise chain will go out of context and get garbage collected

        # TODO: purge the views from removed cameras    
            
        
    def get(self, **kwargs):
        """Find correct filterchain based on generic variables
        """
        for chain in self.chains:
            for key in kwargs:
                getter_name = "get_"+key
                # scan all possible getters
                if (hasattr(chain, getter_name)):
                    getter = getattr(chain, getter_name) # e.g. "get_address"
                    if (getter() == kwargs[key]):
                        return chain
        return None
                    


    def getDevice(self, **kwargs): 
        """Like get, but returns a Device instance (RTSPCameraDevice, etc.)
        """
        filterchain = self.get(**kwargs)
        
        if not filterchain:
            return None
        
        # get filterchain init parameters that are compatible with RTSPCameraDevice input parameters
        pars = filterchain.getParDic(DataModel.RTSPCameraDevice.parameter_defs) 
        # .. and instantiate an RTSPCameraDevice with those parameters
        device = DataModel.RTSPCameraDevice(**pars)
        
        print(self.pre, "getDevice :", pars, device)
        
        return device



def test1():
    dm = DataModel()
    dm.clearAll()
    dm.saveAll()
    
    collection = dm.camera_collection
    
    collection.new(
        DataModel.RTSPCameraRow,
            {"slot": 1,
             "address": "192.168.1.41",
             "username": "admin",
             "password": "1234",
             "tail": ""}
            )
    
    collection.new(DataModel.RTSPCameraRow,
            {"slot": 2,
             "address": "192.168.1.42",
             "username": "admin",
             "password": "1234",
             "tail": ""}
            )
    
    for element in collection.get():
        print("test1 : 1", element)

    
    gpu_handler = GPUHandler(
            n_720p  = 5,
            n_1080p = 5,
            n_1440p = 0,
            n_4K    = 0,
            msbuftime = 300,
            verbose = False
        )
    
    livethread = LiveThread(
        name = "live_thread",
        # verbose = True,
        verbose = False,
        # affinity = self.pardic["live affinity"]
        )
    
    
    filterchain_group = FilterChainGroup(datamodel = dm, livethread = livethread, gpu_handler = gpu_handler, verbose = True)
    filterchain_group.update()
    
    print("\n ADDING ONE \n")
    
    collection.new(DataModel.RTSPCameraRow,
            {"slot": 3,
             "address": "192.168.1.43",
             "username": "admin",
             "password": "1234",
             "tail": ""}
            )
    
    filterchain_group.update()
    
    print("\n REMOVING ONE \n")
    
    entry = next(collection.get({"address":"192.168.1.41"}))
    collection.delete(entry["_id"])
    
    filterchain_group.update()
    
    print("\n BYE \n")
    
    filterchain_group.close()
    
    
if (__name__=="__main__"):
    test1()
    
    
    
 
 
 
