from dataclasses import dataclass

import pandas as pd


@dataclass()
class ProfileMetaData:
    """
    Single instance of Metadata associated with a profile
    """
    id: str
    date_time: pd.Timestamp
    latitude: float
    longitude: float
    utm_epsg: str = None  # the EPSG for the utm zone
    site_id: str = None
    site_name: str = None
    flags: str = None
    comments: str = None
