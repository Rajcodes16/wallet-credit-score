import json
import argparse
import pandas as pd
from collections import defaultdict
from datetime import datetime, timezone
import numpy as np

# --- Feature Engineering Functions ---
def parse_timestamp(ts):
    try:
        return datetime.fromisoformat(ts)
    except Exception:
        try:
            return datetime.fromtimestamp(float(ts), tz=timezone.utc)
        except Exception:
            return None

def extract_features(transactions):
    wallets = defaultdict(list)
    for tx in transactions:
        wallet = tx.get('user') or tx.get('wallet') or tx.get('address')
        if wallet:
            wallets[wallet].append(tx)

    features = {}
    for wallet, txs in wallets.items():
        actions = [t.get('action') or t.get('type') for t in txs]
        timestamps = [parse_timestamp(t.get('timestamp') or t.get('time')) for t in txs if t.get('timestamp') or t.get('time')]
        timestamps = [t for t in timestamps if t is not None]
        amounts = [float(t.get('amount', 0)) for t in txs if t.get('amount') is not None]
        assets = set(t.get('asset') for t in txs if t.get('asset'))
        
        deposit_amt = sum(float(t.get('amount', 0)) for t in txs if (t.get('action') or t.get('type')) == 'deposit')
        borrow_amt = sum(float(t.get('amount', 0)) for t in txs if (t.get('action') or t.get('type')) == 'borrow')
        repay_amt = sum(float(t.get('amount', 0)) for t in txs if (t.get('action') or t.get('type')) == 'repay')
        withdraw_amt = sum(float(t.get('amount', 0)) for t in txs if (t.get('action') or t.get('type')) == 'redeemunderlying')
        liquidation_count = sum(1 for t in txs if (t.get('action') or t.get('type')) == 'liquidationcall')
        
        tx_count = len(txs)
        unique_actions = len(set(actions))
        unique_assets = len(assets)
        activity_span = (max(timestamps) - min(timestamps)).total_seconds() / 86400 if timestamps else 0
        avg_tx_size = np.mean(amounts) if amounts else 0
        freq = tx_count / activity_span if activity_span > 0 else tx_count
        
        # Repay/Borrow ratio
        repay_borrow_ratio = repay_amt / borrow_amt if borrow_amt > 0 else 0
        deposit_withdraw_ratio = deposit_amt / withdraw_amt if withdraw_amt > 0 else 0
        
        features[wallet] = {
            'tx_count': tx_count,
            'unique_actions': unique_actions,
            'unique_assets': unique_assets,
            'activity_span_days': activity_span,
            'avg_tx_size': avg_tx_size,
            'freq_per_day': freq,
            'deposit_amt': deposit_amt,
            'borrow_amt': borrow_amt,
            'repay_amt': repay_amt,
            'withdraw_amt': withdraw_amt,
            'liquidation_count': liquidation_count,
            'repay_borrow_ratio': repay_borrow_ratio,
            'deposit_withdraw_ratio': deposit_withdraw_ratio,
        }
    return features

# --- Scoring Function ---
def score_wallet(feat):
    score = 500  # base score
    # Positive signals
    score += min(feat['repay_borrow_ratio'], 1) * 200  # full repayment is good
    score += min(feat['deposit_withdraw_ratio'], 2) * 100  # more deposits than withdrawals
    score += min(feat['activity_span_days'] / 180, 1) * 50  # longevity
    score += min(feat['unique_assets'] / 5, 1) * 50  # asset diversity
    score += min(feat['unique_actions'] / 5, 1) * 50  # action diversity
    # Negative signals
    score -= min(feat['liquidation_count'], 3) * 100  # penalize liquidations
    if feat['borrow_amt'] > 0 and feat['repay_amt'] == 0:
        score -= 100  # borrowed but never repaid
    if feat['tx_count'] > 1000:
        score -= 100  # possible bot
    score = max(0, min(1000, int(score)))
    return score

# --- Main Script ---
def main():
    parser = argparse.ArgumentParser(description='Aave V2 Wallet Credit Scoring')
    parser.add_argument('input_json', help='Path to user-transactions JSON file')
    parser.add_argument('--output', default='wallet_scores.csv', help='Output CSV file')
    args = parser.parse_args()

    print('Loading data...')
    with open(args.input_json, 'r') as f:
        data = json.load(f)

    print('Extracting features...')
    features = extract_features(data)

    print('Scoring wallets...')
    results = []
    for wallet, feat in features.items():
        score = score_wallet(feat)
        results.append({'wallet': wallet, 'score': score, **feat})

    df = pd.DataFrame(results)
    df.to_csv(args.output, index=False)
    print(f'Saved scores to {args.output}')

if __name__ == '__main__':
    main() 