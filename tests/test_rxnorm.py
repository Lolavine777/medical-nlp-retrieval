import hashlib
import tempfile
import unittest
import zipfile
from pathlib import Path

from medical_race.linking.rxnorm import RxNormTerm, read_rxnorm_archive


def row(
    rxcui="1",
    language="ENG",
    source="RXNORM",
    term_type="IN",
    text="aspirin",
    suppressed="N",
):
    fields = [""] * 18
    fields[0] = rxcui
    fields[1] = language
    fields[6] = "Y"
    fields[11] = source
    fields[12] = term_type
    fields[14] = text
    fields[16] = suppressed
    return "|".join(fields) + "|"


def archive(path, rows, member="rrf/RXNCONSO.RRF"):
    with zipfile.ZipFile(path, "w") as output:
        output.writestr(member, "\n".join(rows) + "\n")
    return hashlib.md5(path.read_bytes()).hexdigest()


class RxNormReaderTest(unittest.TestCase):
    def test_reads_supported_english_unsuppressed_terms(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "rxnorm.zip"
            expected_md5 = archive(
                path,
                [
                    row(),
                    row("2", source="MTHSPL", term_type="SU", text="ASPIRIN"),
                    row("3", language="SPA"),
                    row("4", source="MTHCMSFRF"),
                    row("5", suppressed="Y"),
                ],
            )
            self.assertEqual(
                read_rxnorm_archive(path, expected_md5),
                (
                    RxNormTerm("1", "aspirin", "IN", "RXNORM", True),
                    RxNormTerm("2", "ASPIRIN", "SU", "MTHSPL", True),
                ),
            )

    def test_rejects_checksum_member_and_row_errors(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "rxnorm.zip"
            expected_md5 = archive(path, [row()])
            with self.assertRaisesRegex(ValueError, "MD5"):
                read_rxnorm_archive(path, "0" * 32)
            wrong_member = Path(directory) / "wrong.zip"
            wrong_md5 = archive(wrong_member, [row()], member="RXNCONSO.RRF")
            with self.assertRaisesRegex(ValueError, "RXNCONSO"):
                read_rxnorm_archive(wrong_member, wrong_md5)
            malformed = Path(directory) / "malformed.zip"
            malformed_md5 = archive(malformed, ["too|short|"])
            with self.assertRaisesRegex(ValueError, "columns"):
                read_rxnorm_archive(malformed, malformed_md5)


if __name__ == "__main__":
    unittest.main()
