
import math

from collections import defaultdict

#sigmoid = lambda x: 2/math.pi*math.atan(math.pi*x/2)
sigmoid = lambda x: math.tanh(x)

class NormalizedFeature(object):
    names = set()
    sum = defaultdict(lambda:defaultdict(float))
    sum2 = defaultdict(lambda:defaultdict(float))
    count = defaultdict(lambda:defaultdict(float))
    global_counter = defaultdict(float)
    global_sum_min = defaultdict(float)
    global_sum_max = defaultdict(float)
    global_sum_range = defaultdict(float)
    global_avg_min = defaultdict(float)
    global_avg_max = defaultdict(float)
    global_avg_range = defaultdict(float)
    global_sum = defaultdict(float)
    global_sum2 = defaultdict(float)
    global_avg_sum = defaultdict(float)
    global_avg_sum2 = defaultdict(float)
    global_avg = defaultdict(float)
    global_avg_avg = defaultdict(float)
    global_avg_var = defaultdict(float)
    global_var_sum = defaultdict(float)
    global_var_min = defaultdict(float)
    global_var_max = defaultdict(float)
    global_var_avg = defaultdict(float)
    global_var = defaultdict(float)
    suffix_map = {'id':'', 'tanh':'', 'range':'_range', 'std':'_std'}

    def __init__(self, name):
        self.name = name
        self.names.add(name)
    
    @classmethod
    def set_norm(cls, norm_alg):
        if norm_alg=='id':
            cls.norm=staticmethod(lambda i: i)
        elif norm_alg=='tanh': cls.norm=staticmethod(math.tanh)
        elif norm_alg=='range': cls.norm=staticmethod(math.tanh)
        elif norm_alg=='std': pass
        else: raise ValueError("norm_alg should be either id or tanh")
        
        # TODO: add range
        cls.get_norm_count = getattr(cls, '_get_norm_count'+cls.suffix_map[norm_alg])
        cls.get_norm_avg = getattr(cls, '_get_norm_avg'+cls.suffix_map[norm_alg])
        cls.get_norm_var = getattr(cls, '_get_norm_var'+cls.suffix_map[norm_alg])

    @classmethod
    def calculate(cls):
        get_avg_by_name = cls.get_avg_by_name
        get_var_by_name = cls.get_var_by_name
        for name in cls.names:
            keys = cls.count.keys()
            n = len(keys)
            for key in keys:
                sumi = cls.sum[key][name]
                avgi = cls.get_avg_by_name(name, key)
                vari = cls.get_var_by_name(name, key)
                cls.global_avg_min[name]=min(cls.global_avg_min[name], avgi)
                cls.global_avg_max[name]=max(cls.global_avg_max[name], avgi)
                cls.global_sum_min[name]=min(cls.global_sum_min[name], sumi)
                cls.global_sum_max[name]=max(cls.global_sum_max[name], sumi)
                cls.global_avg_sum[name]+=avgi
                cls.global_avg_sum2[name]+=avgi*avgi
                cls.global_var_sum[name]+=vari
                cls.global_var_min[name]=min(cls.global_var_min[name], vari)
                cls.global_var_max[name]=max(cls.global_var_max[name], vari)
            cls.global_avg_range[name]=cls.global_avg_max[name]-cls.global_avg_min[name]
            cls.global_sum_range[name]=cls.global_sum_max[name]-cls.global_sum_min[name]
            cls.global_avg[name] = cls.global_sum[name] / cls.global_counter[name]
            cls.global_var[name] = cls.global_sum2[name] / cls.global_counter[name] - cls.global_avg[name]*cls.global_avg[name]
            cls.global_avg_avg[name] = cls.global_avg_sum[name] / n
            cls.global_var_avg[name] = cls.global_var_sum[name] / n
            cls.global_var[name] = cls.global_sum2[name] / n - cls.global_avg[name]*cls.global_avg[name]

    def _get_norm_count(self, key):
        return self.norm(self.sum[key][self.name]-self.global_avg[self.name])

    def _get_norm_avg(self, key):
        if self.count[key][self.name]==0: return 0.0
        return self.norm(self.get_avg(key) - self.global_avg_avg[self.name])
        
    def _get_norm_var(self, key):
        return self.norm(self.get_var(key)-self.global_var_avg[self.name])

    def _get_norm_count_range(self, key):
        if self.global_sum_range[self.name]>0:
            return (self.sum[key][self.name] - self.global_sum_min[self.name]) / self.global_sum_range[self.name]
        else:
            return self.sum[key][self.name]

    def _get_norm_avg_range(self, key):
        if self.global_avg_range[self.name]>0:
            return (self.get_avg(key) - self.global_avg_min[self.name]) / self.global_avg_range[self.name]
        else:
            return self.get_avg(key)

    def _get_norm_var_range(self, key):
        var_range = self.global_var_max[self.name] - self.global_var_min[self.name]
        if var_range>0.0:
            return (self.get_var(key)-self.global_var_min[self.name]) / var_range
        else:
            return self.get_var(key)-self.global_var_min[self.name]

    def _get_norm_count_std(self, key):
        return self.sum[key][self.name]-self.global_avg[self.name]

    def _get_norm_avg_std(self, key):
        if self.count[key][self.name]==0: return 0.0
        var = self.global_var[self.name]
        if var>0:
            sd = math.sqrt(var)
            return (self.get_avg(key) - self.global_avg[self.name]) / sd
        else:
            return (self.get_avg(key) - self.global_avg[self.name])

    def _get_norm_var_std(self, key):
        var = self.global_var[self.name]
        if var>0:
            sd = math.sqrt(var)
            return (self.get_var(key)-self.global_var_avg[self.name]) / sd
        else:
            return self.get_var(key)-self.global_var_avg[self.name]

    def add_value(self, key, value):
        self.sum[key][self.name]+=value
        self.sum2[key][self.name]+=value*value
        self.count[key][self.name]+=1
        self.global_sum[self.name]+=value
        self.global_sum2[self.name]+=value*value
        self.global_counter[self.name]+=1


    @classmethod
    def get_avg_by_name(cls, name, key):
        return cls.sum[key][name] / cls.count[key][name] if cls.count[key][name]>0 else 0.0
    
    @classmethod
    def get_var_by_name(cls, name, key):
        if cls.count[key][name] == 0: return 0.0
        avg = cls.get_avg_by_name(name, key)
        return cls.sum2[key][name] / cls.count[key][name] - avg*avg

    def get_avg(self, key):
        return self.get_avg_by_name(self.name, key)

    def get_var(self, key):
        return self.get_var_by_name(self.name, key)
