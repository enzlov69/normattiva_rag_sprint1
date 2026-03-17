from dataclasses import dataclass
from typing import Dict, List

@dataclass
class ProbeAttempt:
    params: Dict
    description: str

def build_probe_matrix(base_params: Dict) -> List[ProbeAttempt]:

    attempts = []

    attempts.append(
        ProbeAttempt(
            params={**base_params},
            description="base_params",
        )
    )

    attempts.append(
        ProbeAttempt(
            params={**base_params, "sottoArticolo": 1},
            description="sottoArticolo_1",
        )
    )

    attempts.append(
        ProbeAttempt(
            params={**base_params, "sottoArticolo": 2},
            description="sottoArticolo_2",
        )
    )

    return attempts
