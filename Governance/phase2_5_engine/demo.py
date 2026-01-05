from __future__ import annotations

from governance.phase2_5_engine.cash_ledger import CashLedger
from governance.phase2_5_engine.pipeline_manager import PipelineManager
from governance.phase2_5_engine.report_generator import generate_daily_report


def main() -> None:
    pm = PipelineManager()
    cl = CashLedger()

    lead_id = pm.add_lead("Client Name", "email@domain.com", "LinkedIn")
    pm.log_outreach(lead_id, "A1_Audit", "email", "Sent proposal")

    txn_id = cl.record_transaction(1500.00, "A1_Client", lead_id)

    report_path = generate_daily_report()
    print(f"lead_id={lead_id}")
    print(f"txn_id={txn_id}")
    print(f"report={report_path}")


if __name__ == "__main__":
    main()
