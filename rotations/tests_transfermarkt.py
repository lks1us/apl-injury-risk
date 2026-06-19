from django.test import TestCase

from rotations.services.transfermarkt_sync import infer_body_part, infer_severity, parse_injury_rows


SAMPLE_INJURY_HTML = """
<table>
<tbody>
<tr class="odd">
  <td>25/26</td><td>Ankle injury</td><td>31/03/2025</td><td>01/05/2025</td><td>32 days</td><td>6</td>
</tr>
<tr class="even">
  <td>24/25</td><td>Knee problems</td><td>16/02/2025</td><td>25/02/2025</td><td>10 days</td><td>1</td>
</tr>
</tbody>
</table>
"""


class TransfermarktParserTests(TestCase):
    def test_parse_injury_rows(self):
        rows = parse_injury_rows(SAMPLE_INJURY_HTML)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["injury_type"], "Ankle injury")
        self.assertEqual(rows[0]["days_out"], 32)

    def test_infer_body_part_and_severity(self):
        self.assertEqual(infer_body_part("Hamstring strain"), "hamstring")
        self.assertEqual(infer_severity(5), "minor")
        self.assertEqual(infer_severity(30), "severe")
