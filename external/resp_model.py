from dataclasses import dataclass
from typing import List, Dict


@dataclass
class AnalyzedDayModel:
    temp_avg: float
    relevant_cond_hours: int


@dataclass
class AnalyzedApiRespModel:
    days: List[AnalyzedDayModel]

    @classmethod
    def from_dict(cls, data: Dict):
        return AnalyzedApiRespModel(
            days=[
                AnalyzedDayModel(
                    temp_avg=day["temp_avg"],
                    relevant_cond_hours=day["relevant_cond_hours"],
                )
                for day in data["days"]
            ]
        )
