from netCDF4 import Dataset,num2date, date2num, stringtoarr
import json

class NetCDFJSON(object):
    """
    Classe para converter entre netCDF e JSON, para facilitar criação e manipulação
    """
    def __init__(self):
        self.rootgrp = None
        self.json_data = None
        
    def write(self, file):
        self.rootgrp = Dataset(file, "w", format="NETCDF4")
    
    def close(self):
        self.rootgrp.close()
        
    def load_json(self, file):
        with open(file, 'r') as fp:
            self.json_data = json.load(fp)
       
    def create_from_json(self, data=None):
        if data is None:
            data = self.json_data

        self.create_dimensions(data['dimensions'])
        self.create_variables(data['variables'])
        self.create_global_attributes(data['global_attributes'])

    def create_variables(self, vars_cfg):
        for var_cfg in vars_cfg:
            self.create_variable(var_cfg)

    def create_variable(self, var_cfg):
        var = None
        for key, value in var_cfg.items(): 
            if key == 'createVariable':
                var = getattr(self.rootgrp, key)(**value)
            else:
                setattr(var, key, value)
        return var

    def create_dimensions(self, dims_cfg):
        for dim_cfg in dims_cfg:
            self.create_dimension(dim_cfg)

    def create_dimension(self, dim_cfg):
        dim = None
        for key, value in dim_cfg.items():
            if key == 'createDimension':
                dim = getattr(self.rootgrp, key)(**value)

    def create_global_attributes(self, attributes):
        for attribute in attributes:
            for key, value in attribute.items(): 
                setattr(self.rootgrp, key,value)

    def get_variable(self, var_name):
        return self.rootgrp.variables[var_name]

    def get_dimension(self, dim_name):
        return self.rootgrp.dimensions[dim_name]
