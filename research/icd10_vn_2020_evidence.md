# Vietnamese ICD-10 Source Evidence - 2026-07-14

## Verified facts

The Ministry clinical-coding application is publicly accessible at `https://icd.kcb.vn/ICD-10-VN`.
Its published application code requests the base Vietnamese catalog from `https://ccs.whiteneuron.com/api/ICD10/`.
The root and child endpoints return Vietnamese hierarchy nodes containing model, identity, code, title, leaf status, and parent relationships.
The application exposes the June 2026 update through a separate `ICD10_TT06` API branch.

The canonical base-branch acquisition completed on 2026-07-14 with 15,827 nodes and 13,940 leaf nodes.
The local snapshot SHA-256 is `72b81f78e3fb971c2c44250d3a5ae67f7c41bef3b5bf1ded59954250e479212f`.
The verified offline index contains 13,906 unambiguous leaf-backed normalized titles.

No explicit redistribution license was located on the public application.
The raw snapshot is therefore untracked, not bundled, not redistributed, and restricted to internal competition use unless a license is established.

## Evidence-backed inference

The base `ICD10` branch is treated as the Vietnamese national catalog associated with Decision 4469/QĐ-BYT dated 2020-10-28.
This association is supported by Ministry materials that identify Decision 4469 as the national ICD-10 catalog and by the application's separate labeling of the June 2026 update.
The API payload itself does not expose a release identifier, so this is not treated as organizer-confirmed ontology evidence.

## Competition uncertainty

The organizer has not stated whether diagnosis candidates use this national catalog, WHO ICD-10 2019, ICD-10-CM, or another derived code set.
The baseline therefore emits only top-one codes present in the pinned local snapshot and treats the ontology branch as a controlled hidden variable.
The June 2026 `ICD10_TT06` branch must not be mixed into the baseline without a separate reproducible experiment.

## Reproducible acquisition

Run `.\.venv\Scripts\python.exe tools\fetch_icd10_vn.py --workers 8 --output ontologies\icd\icd10_vn_2020.json`.
Verify the resulting SHA-256 before offline use.
Prediction and submission building perform no network access.
