from dataclasses import dataclass
from typing import List

import pandas as pd


@dataclass()
class ProfileMetaData:
    """
    Single instance of Metadata associated with a profile
    """
    site_name: str
    date_time: pd.Timestamp
    latitude: float
    longitude: float
    utm_epsg: str = None  # the EPSG for the utm zone
    campaign_name: str = None
    flags: str = None
    comments: str = None
    observers: List[str] = None
