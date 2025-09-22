from dataclasses import dataclass
from typing import Optional
from datetime import datetime
from smp.smp_constant import SMPConstants

# Instantiate constants
smp = SMPConstants()

@dataclass
class SMPRow:
    service_id: str
    smp_name: str
    smp_id: str
    allow_multiple: str
    subscriber_group_name: str
    deployment_date: Optional[datetime] = None
    rpa_remarks: Optional[str] = None
    url: str = ""
    thread_count: str = ""
    frontier_url: str = ""
    frontier_api_url: str = ""
    access_code: str = ""


# Mapping function from raw dict to dataclass
def map_to_smp_row(row: dict) -> SMPRow:
    deployment_date = row.get("Deployment Date")
    if isinstance(deployment_date, str):
        # try parsing string to datetime
        try:
            deployment_date = datetime.strptime(deployment_date.split(" ")[0], "%Y-%m-%d").date()

        except Exception:
            deployment_date = None

    return SMPRow(
        service_id=row.get("ServiceID", ""),
        smp_name=row.get("SMP Name", ""),
        smp_id=row.get("SMP ID", ""),
        allow_multiple=row.get("Allow Multiple", ""),
        subscriber_group_name=row.get("Subscriber Group Name", ""),
        deployment_date=deployment_date,
        rpa_remarks=row.get("SMP RPA Remarks", "").strip() if row.get("SMP RPA Remarks") else None,
        url=smp.SMP_CONSTANT_VALUES["URL"],
        thread_count=smp.SMP_CONSTANT_VALUES["Thread Count"],
        frontier_url=smp.SMP_CONSTANT_VALUES["Frontier URL"],
        frontier_api_url=smp.SMP_CONSTANT_VALUES["Frontier API URL"],
        access_code=smp.SMP_CONSTANT_VALUES["Access Code"]
    )