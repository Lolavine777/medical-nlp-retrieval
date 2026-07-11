# Evidence Audit Plan Corrections

The implementation must add `audit_official_html(path: Path) -> dict[str, object]` to `tools/audit_sources.py`.
That function must parse the official JSON example from the saved HTML and report the entity count, per-type field sets, repeated surface forms, WER, Jaccard, score weights, self-host restriction, and 9B limit.

The implementation must also add deterministic section-header frequencies to `audit_documents`.
A candidate header is a trimmed line of at most 100 characters that optionally starts with a numeric heading and then starts with an observed clinical heading family such as `Tiền sử`, `Bệnh sử`, `Lịch sử`, `Lý do nhập viện`, `Diễn biến`, `Triệu chứng`, `Đánh giá`, `Khám`, `Xét nghiệm`, `Chẩn đoán`, `Phát hiện`, `Thuốc`, `Các bệnh`, or `Các yếu tố`.

ZIP validation must compare the complete ordered entry names with `input/1.txt` through `input/100.txt`, not only compare numeric stems.
