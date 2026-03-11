import datetime
import configparser
import mappings as timezone_mappings

config = configparser.ConfigParser()
config.read('config.cfg')
default_timezone = config.get('DEFAULT', 'timezone').strip('"')
timezone_offsets = timezone_mappings.tzs


def _to_timezone(offset):
    """
        Converts a UTC offset string (e.g. "+05:30") to datetime.timezone.
    """
    hours, minutes = offset.split(":")
    delta = datetime.timedelta(hours=int(hours), minutes=int(minutes))
    return datetime.timezone(delta)


# Precompute timezone objects to avoid repeated parsing for each request.
timezone_objects = {abbr: _to_timezone(offset) for abbr, offset in timezone_offsets.items()}


def timezone_offset(timezone_name):
    """
        Returns the UTC offset string (e.g. "+05:30") for a timezone abbreviation.
    """
    if not timezone_name:
        return False

    return timezone_offsets.get(timezone_name.upper(), False)


def timezone(timezone_name):
    """
        Returns a datetime.timezone object for the given timezone abbreviation.
    """
    if not timezone_name:
        return False

    return timezone_objects.get(timezone_name.upper(), False)