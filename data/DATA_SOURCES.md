# External Data Manifest

The organizer confirmed that public Vietnamese medical NER datasets and other external training sources are allowed.
Do not use a dataset until its license, redistribution status, reproducible acquisition, and competition-label mapping are documented.

| dataset | source | version | license | redistribution_status | download_procedure | original_labels | competition_label_mapping | usage | known_mismatches |
|---|---|---|---|---|---|---|---|---|---|
| RxNorm Current Prescribable Content | https://download.nlm.nih.gov/rxnorm/RxNorm_full_prescribe_07062026.zip | 2026-07-06, MD5 `767678e3b5b1d6fe358b61c21659f3ef`, SHA-256 `e81e29a27575718dc1f0cf80b1371b283bcba53f446f27fc85f74c71def99829` | No license required for this subset; NLM normalized names and RXCUIs are public domain with requested attribution | Raw archive is untracked and not redistributed; reproduce from the dated official URL | Download the dated ZIP, enforce the published MD5, and read `rrf/RXNCONSO.RRF` directly | RXCUI, term type, source, preferred flag, suppression flag, and English term | RXCUI becomes a `THUỐC.candidates` value only after deterministic lexical linking | Active drug candidate generation for the first rule baseline | U.S.-centric active prescribable subset excludes obsolete and historical concepts; competition release and target granularity are hidden |
| ViMedNer | Not pinned | Not acquired | Verify | Verify | Document | Inspect | Map explicitly | Domain adaptation and span detection | Competition policy mismatch possible |
| ViMQ | Not pinned | Not acquired | Verify | Verify | Document | Inspect | Map explicitly | Domain adaptation | Task-format mismatch possible |
| PhoNER_COVID19 | https://github.com/VinAIResearch/PhoNER_COVID19 | Not acquired | Verify pinned release | Verify | Pin commit and script | Epidemic NER labels | Map explicitly | Span pretraining | News genre and label mismatch |

Allowed competition targets are `TRIỆU_CHỨNG`, `TÊN_XÉT_NGHIỆM`, `KẾT_QUẢ_XÉT_NGHIỆM`, `CHẨN_ĐOÁN`, and `THUỐC`.
Use external data mainly for domain adaptation and span detection, not blind label transfer.
