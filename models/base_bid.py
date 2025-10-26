from typing import List, Dict, Union, Optional
from abc import ABC, abstractmethod

class BaseBid(ABC):
    def __init__(self, bid_id: str, price_schedule: Union[List[float], Dict[str, List[float]]], quantity: float, bid_type: str):
        self.bid_id = bid_id
        self.price_schedule = price_schedule
        self.quantity = quantity
        self.bid_type = bid_type

    def get_price_at_time(self, time: int) -> float:
        if isinstance(self.price_schedule, list):
            return self.price_schedule[time]
        else:
            raise ValueError("get_price_at_time requires a list price_schedule for non-dict types")

    @abstractmethod
    def validate_bid(self) -> bool:
        pass
