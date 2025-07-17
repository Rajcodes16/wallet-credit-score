# Aave V2 Wallet Credit Scoring

This project provides a robust, transparent script to assign a **credit score (0-1000)** to each wallet based on historical transaction behavior in the Aave V2 protocol. Higher scores indicate responsible, reliable usage; lower scores reflect risky, bot-like, or exploitative behavior.

## Features Engineered
For each wallet, the following features are computed from raw transaction data:

- **tx_count**: Total number of transactions
- **unique_actions**: Number of unique action types (e.g., deposit, borrow, repay, etc.)
- **unique_assets**: Number of unique assets interacted with
- **activity_span_days**: Days between first and last transaction (wallet longevity)
- **avg_tx_size**: Average transaction size
- **freq_per_day**: Average number of transactions per day
- **deposit_amt**: Total deposited amount
- **borrow_amt**: Total borrowed amount
- **repay_amt**: Total repaid amount
- **withdraw_amt**: Total withdrawn amount
- **liquidation_count**: Number of times liquidated
- **repay_borrow_ratio**: Ratio of repaid to borrowed amount
- **deposit_withdraw_ratio**: Ratio of deposits to withdrawals

## Scoring Logic
The score for each wallet is calculated as follows:

- **Base score:** 500
- **Positive signals:**
  - +200 × (repay_borrow_ratio, capped at 1)
  - +100 × (deposit_withdraw_ratio, capped at 2)
  - +50 × (activity_span_days / 180, capped at 1)
  - +50 × (unique_assets / 5, capped at 1)
  - +50 × (unique_actions / 5, capped at 1)
- **Negative signals:**
  - −100 × (liquidation_count, capped at 3)
  - −100 if borrowed but never repaid
  - −100 if tx_count > 1000 (possible bot)
- **Score is clamped between 0 and 1000.**

## How to Run

1. **Install dependencies:**
   ```bash
   pip install pandas numpy
   ```

2. **Run the script:**
   ```bash
   python wallet_credit_score.py path/to/user-transactions.json --output wallet_scores.csv
   ```
   - Replace `path/to/user-transactions.json` with your JSON file path.
   - The output CSV will contain wallet addresses, scores, and features.

## Extensibility
- The script is modular: add new features or adjust scoring in `wallet_credit_score.py`.
- Feature extraction and scoring are transparent and easy to modify.

## Data Requirements
- Input JSON should be a list of transaction objects, each with at least:
  - `user` or `wallet` or `address` (wallet address)
  - `action` or `type` (transaction type)
  - `amount` (numeric, can be string or number)
  - `timestamp` or `time` (ISO8601 or UNIX timestamp)
  - `asset` (optional, for asset diversity)

## Example Output
| wallet         | score | tx_count | ... |
|---------------|-------|----------|-----|
| 0x123...abcd  |  850  |   42     | ... |
| 0x456...ef01  |  320  |   12     | ... |

---

**For questions or improvements, edit the script or open an issue!** 