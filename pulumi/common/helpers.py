import pulumi
from datetime import datetime
import pytz

class Helpers():

    @staticmethod
    def get_current_timestamp():
        UTC = pytz.utc
        datetime_utc = datetime.now(UTC)
        current_timestamp = f"{datetime_utc.strftime('%Y-%m-%d %H:%M:%S %Z %z')}"
        return current_timestamp

    @staticmethod
    def get_region_alias(region):
        region_alias = f"{region[0]}{region[1]}{region[3]}{region[len(region)-1:]}"
        return region_alias

    @staticmethod
    def get_az_alias(availability_zone):
        l = len(availability_zone)
        az_alias = f"{availability_zone[0]}{availability_zone[1]}{availability_zone[3]}{availability_zone[l-2:]}"
        return az_alias
    
    @staticmethod
    def key_in_dict(_dict: dict, key_lookup: str, encrypted: bool=False, separator='.'):
        keys = key_lookup.split(separator)
        subdict = _dict

        for k in keys:
            if k in subdict:
                subdict = subdict[k]
            else:
                subdict = None

            if subdict is None: break

        return subdict