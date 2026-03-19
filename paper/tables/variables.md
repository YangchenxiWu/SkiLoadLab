# Table 1. Variables and definitions

| Variable | Type | Units | Definition | Notes |
|---|---:|---:|---|---|
| run_id | id | – | Downhill run identifier within a session | Produced by segmentation |
| duration_s | numeric | s | Duration of a downhill run | Run-level aggregation |
| vertical_drop_m | numeric | m | Total vertical drop during a run | Derived from DEM-sampled elevation |
| speed_mean_ms | numeric | m/s | Mean speed during a run | May be absent in demo table |
| edwards_trimp | numeric | a.u. | Edwards TRIMP (zone-weighted time) | Requires HR data |
| internal_used_for_combined | categorical | – | Internal metric chosen for fusion | e.g., impulse-based vs TRIMP |
| z_internal | numeric | z-score | Standardized internal load metric across runs | Computed within a session/table |
| z_mech | numeric | z-score | Standardized external/mechanical proxy across runs | Computed within a session/table |
| z_trimp | numeric | z-score | Standardized TRIMP (if available) | Demo may include only z_trimp |
| combined_load_v2 | numeric | a.u. | Alpha-weighted fusion: alpha·z_internal + (1-alpha)·z_mech | Alpha sweep supported |
| alpha | numeric | – | Weight in [0,1] controlling fusion | Selected by balance heuristic |
| corr(combined, z_internal) | numeric | – | Correlation between combined index and z_internal | Used for alpha sweep diagnostics |
| corr(combined, z_mech) | numeric | – | Correlation between combined index and z_mech | Used for alpha sweep diagnostics |
| score_balanced | numeric | – | min(|corr(combined,z_internal)|, |corr(combined,z_mech)|) | Alpha sweep objective |
