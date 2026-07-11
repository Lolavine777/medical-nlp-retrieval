# External Data Manifest

The organizer confirmed that public Vietnamese medical NER datasets and other external training sources are allowed.
Do not use a dataset until its license, redistribution status, reproducible acquisition, and competition-label mapping are documented.

| dataset | source | version | license | redistribution_status | download_procedure | original_labels | competition_label_mapping | usage | known_mismatches |
|---|---|---|---|---|---|---|---|---|---|
| ViMedNer | Not pinned | Not acquired | Verify | Verify | Document | Inspect | Map explicitly | Domain adaptation and span detection | Competition policy mismatch possible |
| ViMQ | Not pinned | Not acquired | Verify | Verify | Document | Inspect | Map explicitly | Domain adaptation | Task-format mismatch possible |
| PhoNER_COVID19 | https://github.com/VinAIResearch/PhoNER_COVID19 | Not acquired | Verify pinned release | Verify | Pin commit and script | Epidemic NER labels | Map explicitly | Span pretraining | News genre and label mismatch |

Allowed competition targets are `TRIỆU_CHỨNG`, `TÊN_XÉT_NGHIỆM`, `KẾT_QUẢ_XÉT_NGHIỆM`, `CHẨN_ĐOÁN`, and `THUỐC`.
Use external data mainly for domain adaptation and span detection, not blind label transfer.
