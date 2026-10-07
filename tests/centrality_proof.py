"""
Reproducible Graph Centrality Proof Script (AI Dev Fest Track 01)
Calculates and compares Network Centrality metrics for:
- Normal Peer-to-Peer Customer Nodes
- Injected / Empirical Money-Mule Nodes (Hubs, Aggregators, Rogue Devices)

Calculates:
- Total Degree
- In-Degree (Fan-In concentration)
- Out-Degree (Dispersal)
- Degree Centrality
- Betweenness Centrality (sample-based for scalability)
- PageRank Score
"""

import os
import sys
import json
import pandas as pd
import numpy as np
import networkx as nx

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")
CSV_PATH = os.path.join(BASE_DIR, "data", "upay_ai_shield_20000_transactions.csv")

def compute_centrality_proof():
    print("=" * 80)
    print("  GRAPH CENTRALITY PROOF: SUSPICIOUS / MULE NODES VS NORMAL NODES")
    print("=" * 80)

    df = pd.read_csv(CSV_PATH)
    G = nx.DiGraph()

    for _, row in df.iterrows():
        c = str(row['customer_id'])
        r = str(row['receiver_id'])
        amt = float(row['amount'])
        if G.has_edge(c, r):
            G[c][r]['weight'] += amt
            G[c][r]['count'] += 1
        else:
            G.add_edge(c, r, weight=amt, count=1)

    print(f"Constructed Multi-Entity Graph: {G.number_of_nodes():,} nodes, {G.number_of_edges():,} directed edges.")

    # Calculate Degree Centrality
    deg_centrality = nx.degree_centrality(G)
    in_deg_centrality = nx.in_degree_centrality(G)
    
    # Calculate PageRank
    pagerank = nx.pagerank(G, alpha=0.85, max_iter=200)

    # Calculate Betweenness on top subgraph nodes for high performance
    top_candidates = sorted(deg_centrality.keys(), key=lambda k: deg_centrality[k], reverse=True)[:250]
    subG = G.subgraph(top_candidates)
    betweenness = nx.betweenness_centrality(subG, normalized=True)

    # Known Mule Hubs from calibrated dataset
    mule_nodes = ["REC09901", "REC09903", "REC09905", "REC09907", "REC09909", "REC09911"]
    
    # Sample 50 normal customers with low risk
    normal_candidates = [n for n in G.nodes() if n.startswith("CUST") and G.in_degree(n) <= 1 and G.out_degree(n) <= 3][:50]

    # Gather stats for mule nodes
    mule_stats = []
    for m in mule_nodes:
        if m in G:
            mule_stats.append({
                "node_id": m,
                "type": "Mule Aggregator Hub",
                "in_degree": G.in_degree(m),
                "out_degree": G.out_degree(m),
                "total_degree": G.degree(m),
                "degree_centrality": round(deg_centrality.get(m, 0.0), 6),
                "in_degree_centrality": round(in_deg_centrality.get(m, 0.0), 6),
                "pagerank": round(pagerank.get(m, 0.0), 6),
                "betweenness": round(betweenness.get(m, 0.0), 6)
            })

    # Gather stats for normal nodes
    normal_stats = []
    for n in normal_candidates:
        normal_stats.append({
            "in_degree": G.in_degree(n),
            "out_degree": G.out_degree(n),
            "total_degree": G.degree(n),
            "degree_centrality": deg_centrality.get(n, 0.0),
            "in_degree_centrality": in_deg_centrality.get(n, 0.0),
            "pagerank": pagerank.get(n, 0.0),
            "betweenness": betweenness.get(n, 0.0)
        })

    mule_df = pd.DataFrame(mule_stats)
    norm_df = pd.DataFrame(normal_stats)

    summary = {
        "mule_nodes_average": {
            "in_degree": round(float(mule_df["in_degree"].mean()), 2),
            "out_degree": round(float(mule_df["out_degree"].mean()), 2),
            "total_degree": round(float(mule_df["total_degree"].mean()), 2),
            "degree_centrality": round(float(mule_df["degree_centrality"].mean()), 6),
            "in_degree_centrality": round(float(mule_df["in_degree_centrality"].mean()), 6),
            "pagerank": round(float(mule_df["pagerank"].mean()), 6),
            "betweenness_centrality": round(float(mule_df["betweenness"].mean()), 6)
        },
        "normal_nodes_average": {
            "in_degree": round(float(norm_df["in_degree"].mean()), 2),
            "out_degree": round(float(norm_df["out_degree"].mean()), 2),
            "total_degree": round(float(norm_df["total_degree"].mean()), 2),
            "degree_centrality": round(float(norm_df["degree_centrality"].mean()), 6),
            "in_degree_centrality": round(float(norm_df["in_degree_centrality"].mean()), 6),
            "pagerank": round(float(norm_df["pagerank"].mean()), 6),
            "betweenness_centrality": round(float(norm_df["betweenness"].mean()), 6)
        },
        "centrality_ratios_mule_vs_normal": {
            "in_degree_ratio": round(float(mule_df["in_degree"].mean() / max(norm_df["in_degree"].mean(), 0.01)), 2),
            "degree_centrality_ratio": round(float(mule_df["degree_centrality"].mean() / max(norm_df["degree_centrality"].mean(), 0.000001)), 2),
            "pagerank_ratio": round(float(mule_df["pagerank"].mean() / max(norm_df["pagerank"].mean(), 0.000001)), 2),
            "betweenness_ratio": round(float(mule_df["betweenness"].mean() / max(norm_df["betweenness"].mean(), 0.000001)), 2)
        },
        "mule_nodes_detail": mule_stats
    }

    print("\n--- CENTRALITY METRICS COMPARISON (ACTUAL GRAPH EXECUTION) ---")
    print(f"{'Metric':<28} | {'Normal Nodes (Avg)':<20} | {'Mule Nodes (Avg)':<20} | {'Ratio (M/N)':<10}")
    print("-" * 85)
    print(f"{'In-Degree (Fan-In)':<28} | {summary['normal_nodes_average']['in_degree']:<20.2f} | {summary['mule_nodes_average']['in_degree']:<20.2f} | {summary['centrality_ratios_mule_vs_normal']['in_degree_ratio']:<10.1f}x")
    print(f"{'Total Degree':<28} | {summary['normal_nodes_average']['total_degree']:<20.2f} | {summary['mule_nodes_average']['total_degree']:<20.2f} | {mule_df['total_degree'].mean()/norm_df['total_degree'].mean():<10.1f}x")
    print(f"{'Degree Centrality':<28} | {summary['normal_nodes_average']['degree_centrality']:<20.6f} | {summary['mule_nodes_average']['degree_centrality']:<20.6f} | {summary['centrality_ratios_mule_vs_normal']['degree_centrality_ratio']:<10.1f}x")
    print(f"{'PageRank Score':<28} | {summary['normal_nodes_average']['pagerank']:<20.6f} | {summary['mule_nodes_average']['pagerank']:<20.6f} | {summary['centrality_ratios_mule_vs_normal']['pagerank_ratio']:<10.1f}x")
    print(f"{'Betweenness Centrality':<28} | {summary['normal_nodes_average']['betweenness_centrality']:<20.6f} | {summary['mule_nodes_average']['betweenness_centrality']:<20.6f} | {summary['centrality_ratios_mule_vs_normal']['betweenness_ratio']:<10.1f}x")
    print("=" * 85)

    with open(os.path.join(OUTPUTS_DIR, "centrality_proof.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"Saved complete centrality proof to {os.path.join(OUTPUTS_DIR, 'centrality_proof.json')}")

    return summary

if __name__ == "__main__":
    compute_centrality_proof()
