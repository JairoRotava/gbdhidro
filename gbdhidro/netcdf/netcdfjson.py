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
       
    def create_from_json(self, data=None, handler=None):
        if data is None:
            data = self.json_data

        if 'dimensions' in data:
            self.create_dimensions(data['dimensions'], handler=handler)
        if 'variables' in data:
            self.create_variables(data['variables'], handler=handler)
        if 'attributes' in data:
            self.create_attributes(data['attributes'], handler=handler)
        if 'groups' in data:
            self.create_groups(data['groups'], handler=handler)

    def create_variables(self, vars_cfg, handler=None):
        for var_cfg in vars_cfg:
            self.create_variable(var_cfg, handler=handler)

    def create_variable(self, var_cfg, handler=None):
        var = None
        for key, value in var_cfg.items(): 
            if key == 'createVariable':
                var = getattr(self.get_handler(handler), key)(**value)
            else:
                setattr(var, key, value)
        return var

    def create_dimensions(self, dims_cfg, handler=None):
        for dim_cfg in dims_cfg:
            self.create_dimension(dim_cfg, handler=handler)

    def create_dimension(self, dim_cfg, handler=None):
        dim = None
        for key, value in dim_cfg.items():
            if key == 'createDimension':
                dim = getattr(self.get_handler(handler), key)(**value)

    def create_groups(self, groups_cfg, handler=None):
        for grp in groups_cfg:
            self.create_group(grp, handler=handler)

    def create_group(self, group_cfg, handler=None):
        grp = None
        for key, value in group_cfg.items():
            if key == 'createGroup':
                grp = getattr(self.get_handler(handler), key)(value['groupname'])
            else:
                self.create_from_json({key: value}, grp)
        return grp

    def create_attributes(self, attributes, handler=None):
        for attribute in attributes:
            for key, value in attribute.items(): 
                setattr(self.get_handler(handler), key, value)

    def get_variable(self, var_name):
        return self.rootgrp.variables[var_name]

    def get_dimension(self, dim_name):
        return self.rootgrp.dimensions[dim_name]

    def get_group(self, group_name):
        return self.rootgrp.groups[group_name]

    def get_handler(self, handler=None):
        if handler:
            return handler
        else:
            return self.rootgrp
