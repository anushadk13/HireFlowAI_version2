import unittest

from backend.services.hr import parse_jd


class ParseJDTests(unittest.TestCase):
    def test_role_summary_is_list_of_bullets(self):
        job_description = """
        Senior Data Engineer
        We are looking for a Senior Data Engineer to build data pipelines, design ETL workflows, and collaborate across teams.
        This role requires 4+ years of experience and a Bachelor's degree.
        """

        result = parse_jd(job_description)

        self.assertIsInstance(result["role_summary"], list)
        self.assertTrue(result["role_summary"])
        self.assertTrue(all(isinstance(item, str) and item.strip() for item in result["role_summary"]))


if __name__ == "__main__":
    unittest.main()
