from fastapi import APIRouter
from backend.schemas.common import ApiResponse
from backend.engine import TYPOLOGY_RULES

router = APIRouter(prefix="/api/v1/intelligence", tags=["Intelligence"])


@router.get("/typologies", response_model=ApiResponse[list])
def get_typology_catalog():
    rules_data = []
    for code, info in TYPOLOGY_RULES.items():
        rules_data.append({
            "code": code,
            "name": info["name"],
            "severity": info["severity"],
            "description": info["description"],
            "weight": info["weight"],
            "regulatory_ref": "BFIU Master Circular 24 / BTRC Guidelines"
        })
    return ApiResponse(
        success=True,
        message="Active fraud typology rules retrieved",
        data=rules_data
    )


@router.get("/network-graph", response_model=ApiResponse[dict])
def get_network_mule_graph():
    """Returns network graph nodes and edges for money mule syndicate visualization."""
    nodes = [
        {"id": "MULE-HUB-01", "label": "Syndicate Cash-Out Hub", "type": "hub", "risk": "CRITICAL", "volume": "BDT 1,450,000", "degree": 8},
        {"id": "AGENT-DHK-401", "label": "Agent Mirpur-10 (Suspicious)", "type": "agent", "risk": "HIGH", "volume": "BDT 820,000", "degree": 5},
        {"id": "AGENT-CTG-102", "label": "Agent Agrabad CTG", "type": "agent", "risk": "MEDIUM", "volume": "BDT 340,000", "degree": 3},
        {"id": "CUST-9921", "label": "Account Compromised (CUST-9921)", "type": "victim", "risk": "HIGH", "volume": "BDT 49,500", "degree": 2},
        {"id": "CUST-4412", "label": "Victim CUST-4412", "type": "victim", "risk": "HIGH", "volume": "BDT 48,000", "degree": 1},
        {"id": "CUST-7731", "label": "Victim CUST-7731", "type": "victim", "risk": "MEDIUM", "volume": "BDT 35,000", "degree": 1},
        {"id": "RECP-01889922331", "label": "Layering Wallet (RECP-331)", "type": "mule", "risk": "CRITICAL", "volume": "BDT 390,000", "degree": 4},
        {"id": "RECP-01711002299", "label": "Smurfing Smuggler (RECP-299)", "type": "mule", "risk": "CRITICAL", "volume": "BDT 520,000", "degree": 5},
        {"id": "BENEFICIARY-EXT", "label": "Offshore Remittance Node", "type": "exit", "risk": "CRITICAL", "volume": "BDT 1,200,000", "degree": 3}
    ]

    edges = [
        {"source": "CUST-9921", "target": "RECP-01889922331", "amount": "BDT 49,500", "type": "FAST_TRANSFER", "time": "02:14 AM"},
        {"source": "CUST-4412", "target": "RECP-01889922331", "amount": "BDT 48,000", "type": "FAST_TRANSFER", "time": "02:30 AM"},
        {"source": "CUST-7731", "target": "RECP-01711002299", "amount": "BDT 35,000", "type": "FAST_TRANSFER", "time": "03:05 AM"},
        {"source": "RECP-01889922331", "target": "MULE-HUB-01", "amount": "BDT 95,000", "type": "AGGREGATION", "time": "03:45 AM"},
        {"source": "RECP-01711002299", "target": "MULE-HUB-01", "amount": "BDT 120,000", "type": "AGGREGATION", "time": "04:10 AM"},
        {"source": "MULE-HUB-01", "target": "AGENT-DHK-401", "amount": "BDT 250,000", "type": "BURST_CASH_OUT", "time": "06:15 AM"},
        {"source": "MULE-HUB-01", "target": "AGENT-CTG-102", "amount": "BDT 180,000", "type": "BURST_CASH_OUT", "time": "06:40 AM"},
        {"source": "MULE-HUB-01", "target": "BENEFICIARY-EXT", "amount": "BDT 800,000", "type": "CROSS_BORDER", "time": "07:20 AM"}
    ]

    return ApiResponse(
        success=True,
        message="Money mule network graph loaded",
        data={
            "syndicate_id": "SYN-DHK-2026-09",
            "threat_level": "CRITICAL",
            "nodes": nodes,
            "edges": edges,
            "summary": "Coordinated Account Takeover (ATO) smurfing ring channeling funds to Mirpur-10 agent network."
        }
    )
