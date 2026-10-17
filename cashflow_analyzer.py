#!/usr/bin/env python3
"""
MSME AI Cashflow Analyzer - Starter Script
=========================================

A practical demonstration tool for Indian MSMEs.
Reconciles sample UPI transactions with invoices,
estimates working capital needs, and flags GST-related insights.

No external dependencies required.
Extend with real data sources, pandas, or AI models.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional

# Sample data representing a typical MSME (e.g., a small manufacturer or trader)
# Invoices issued to customers
SAMPLE_INVOICES = [
    {
        "invoice_id": "INV-2026-001",
        "customer": "Sharma Traders",
        "amount": 45000.00,
        "gst_rate": 18,
        "issue_date": "2026-10-01",
        "due_date": "2026-10-31",
        "description": "Steel components supply",
        "status": "unpaid"
    },
    {
        "invoice_id": "INV-2026-002",
        "customer": "Patel Industries",
        "amount": 28500.00,
        "gst_rate": 12,
        "issue_date": "2026-10-05",
        "due_date": "2026-10-20",
        "description": "Packaging materials",
        "status": "partial"
    },
    {
        "invoice_id": "INV-2026-003",
        "customer": "Kumar Retail",
        "amount": 12000.00,
        "gst_rate": 5,
        "issue_date": "2026-10-10",
        "due_date": "2026-10-25",
        "description": "Raw material order",
        "status": "paid"
    },
    {
        "invoice_id": "INV-2026-004",
        "customer": "Singh Exports",
        "amount": 87500.00,
        "gst_rate": 18,
        "issue_date": "2026-10-12",
        "due_date": "2026-11-12",
        "description": "Finished goods",
        "status": "unpaid"
    }
]

# Sample UPI / bank incoming transactions
SAMPLE_TRANSACTIONS = [
    {
        "txn_id": "UPI-2026-1001",
        "date": "2026-10-08",
        "amount": 12000.00,
        "reference": "INV-2026-003",
        "payer": "Kumar Retail",
        "type": "UPI"
    },
    {
        "txn_id": "UPI-2026-1002",
        "date": "2026-10-15",
        "amount": 15000.00,
        "reference": "Partial payment INV-2026-002",
        "payer": "Patel Industries",
        "type": "UPI"
    },
    {
        "txn_id": "NEFT-2026-1003",
        "date": "2026-10-16",
        "amount": 20000.00,
        "reference": "Advance against INV-2026-001",
        "payer": "Sharma Traders",
        "type": "NEFT"
    }
]


def calculate_gst(amount: float, rate: float) -> float:
    """Calculate GST amount for an invoice."""
    return round(amount * rate / 100, 2)


def match_transactions_to_invoices(
    invoices: List[Dict], transactions: List[Dict]
) -> List[Dict]:
    """
    Simple reconciliation logic.
    Matches transactions to invoices by reference or amount + payer name.
    Returns enriched invoice list with payment status and remaining balance.
    """
    results = []
    used_txns = set()

    for inv in invoices:
        inv_copy = inv.copy()
        matched_amount = 0.0
        matched_txns = []

        for txn in transactions:
            if txn["txn_id"] in used_txns:
                continue

            # Match by explicit reference or by amount + payer similarity
            ref_match = (
                txn.get("reference", "").upper().find(inv["invoice_id"]) != -1
            )
            amount_match = abs(txn["amount"] - inv["amount"]) < 1.0
            payer_match = txn.get("payer", "").lower() in inv["customer"].lower()

            if ref_match or (amount_match and payer_match):
                matched_amount += txn["amount"]
                matched_txns.append(txn["txn_id"])
                used_txns.add(txn["txn_id"])

        remaining = max(0.0, inv["amount"] - matched_amount)
        inv_copy["matched_amount"] = matched_amount
        inv_copy["remaining"] = remaining
        inv_copy["matched_txns"] = matched_txns
        inv_copy["gst_amount"] = calculate_gst(inv["amount"], inv["gst_rate"])

        # Simple status update
        if remaining == 0:
            inv_copy["reconciled_status"] = "Fully Paid"
        elif matched_amount > 0:
            inv_copy["reconciled_status"] = "Partially Paid"
        else:
            inv_copy["reconciled_status"] = "Unpaid"

        results.append(inv_copy)

    return results


def estimate_working_capital(reconciled: List[Dict]) -> Dict:
    """
    Estimate working capital needs.
    Outstanding receivables + suggested buffer.
    """
    total_outstanding = sum(r["remaining"] for r in reconciled)
    total_invoiced = sum(r["amount"] for r in reconciled)
    total_received = sum(r["matched_amount"] for r in reconciled)

    # Simple buffer: 15% of outstanding or minimum 10,000
    buffer = max(10000.0, total_outstanding * 0.15)

    return {
        "total_invoiced": round(total_invoiced, 2),
        "total_received": round(total_received, 2),
        "total_outstanding": round(total_outstanding, 2),
        "suggested_working_capital_buffer": round(buffer, 2),
        "recommended_wc_need": round(total_outstanding + buffer, 2),
    }


def generate_gst_insights(reconciled: List[Dict]) -> List[str]:
    """Generate simple GST-related flags and insights."""
    insights = []
    high_value_unpaid = [
        r for r in reconciled if r["remaining"] > 20000 and r["gst_rate"] >= 12
    ]
    if high_value_unpaid:
        insights.append(
            f"{len(high_value_unpaid)} high-value invoice(s) with significant GST "
            f"are still unpaid. Consider follow-up to protect input credit timing."
        )

    total_gst_outstanding = sum(
        calculate_gst(r["remaining"], r["gst_rate"]) for r in reconciled
    )
    insights.append(
        f"Estimated GST component in outstanding receivables: ₹{total_gst_outstanding:,.2f}"
    )

    return insights


def print_report(reconciled: List[Dict], wc: Dict, insights: List[str]) -> None:
    """Print a clean console report."""
    print("=" * 60)
    print("MSME AI CASHFLOW ANALYZER — RECONCILIATION REPORT")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)

    print("\nINVOICE RECONCILIATION")
    print("-" * 60)
    for r in reconciled:
        print(f"Invoice: {r['invoice_id']} | Customer: {r['customer']}")
        print(f"  Amount: ₹{r['amount']:,.2f} | GST: {r['gst_rate']}% (₹{r['gst_amount']:,.2f})")
        print(f"  Matched: ₹{r['matched_amount']:,.2f} | Remaining: ₹{r['remaining']:,.2f}")
        print(f"  Status: {r['reconciled_status']}")
        if r["matched_txns"]:
            print(f"  Matched Txns: {', '.join(r['matched_txns'])}")
        print()

    print("WORKING CAPITAL ESTIMATE")
    print("-" * 60)
    print(f"Total Invoiced:     ₹{wc['total_invoiced']:,.2f}")
    print(f"Total Received:     ₹{wc['total_received']:,.2f}")
    print(f"Outstanding:        ₹{wc['total_outstanding']:,.2f}")
    print(f"Suggested Buffer:   ₹{wc['suggested_working_capital_buffer']:,.2f}")
    print(f"Recommended WC Need:₹{wc['recommended_wc_need']:,.2f}")

    print("\nGST & CASHFLOW INSIGHTS")
    print("-" * 60)
    for insight in insights:
        print(f"• {insight}")

    print("\n" + "=" * 60)
    print("This is a starter demo. Connect real UPI/bank data and invoice exports")
    print("to turn this into a production cash-flow tool for Indian MSMEs.")
    print("=" * 60)


def main():
    print("Running MSME AI Cashflow Analyzer...\n")

    reconciled = match_transactions_to_invoices(SAMPLE_INVOICES, SAMPLE_TRANSACTIONS)
    wc_estimate = estimate_working_capital(reconciled)
    gst_insights = generate_gst_insights(reconciled)

    print_report(reconciled, wc_estimate, gst_insights)


if __name__ == "__main__":
    main()
