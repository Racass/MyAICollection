from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "validate_skills.py"
SPEC = importlib.util.spec_from_file_location("validate_skills", MODULE_PATH)
assert SPEC and SPEC.loader
validate_skills = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = validate_skills
SPEC.loader.exec_module(validate_skills)


class ValidateSkillsTests(unittest.TestCase):
    def create_repository(self, skill_name: str = "example-skill") -> Path:
        temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        root = Path(temporary_directory.name)
        skill_dir = root / ".claude" / "skills" / skill_name
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(
            "---\n"
            f"name: {skill_name}\n"
            "description: Perform a safe example task when a user requests an example.\n"
            "license: MIT\n"
            "---\n\n"
            "# Instructions\n\n"
            "Follow the user's request without inventing facts.\n",
            encoding="utf-8",
        )
        return root

    def test_valid_repository_passes(self) -> None:
        root = self.create_repository()
        self.assertEqual([], validate_skills.validate_repository(root))

    def test_name_must_match_directory(self) -> None:
        root = self.create_repository()
        skill_file = root / ".claude" / "skills" / "example-skill" / "SKILL.md"
        skill_file.write_text(
            skill_file.read_text(encoding="utf-8").replace(
                "name: example-skill", "name: different-name"
            ),
            encoding="utf-8",
        )

        messages = [error.message for error in validate_skills.validate_repository(root)]
        self.assertTrue(any("must match directory" in message for message in messages))

    def test_required_description_is_enforced(self) -> None:
        root = self.create_repository()
        skill_file = root / ".claude" / "skills" / "example-skill" / "SKILL.md"
        skill_file.write_text(
            skill_file.read_text(encoding="utf-8").replace(
                "description: Perform a safe example task when a user requests an example.\n",
                "",
            ),
            encoding="utf-8",
        )

        messages = [error.message for error in validate_skills.validate_repository(root)]
        self.assertIn("frontmatter requires a description", messages)

    def test_broken_relative_link_is_rejected(self) -> None:
        root = self.create_repository()
        skill_file = root / ".claude" / "skills" / "example-skill" / "SKILL.md"
        with skill_file.open("a", encoding="utf-8") as handle:
            handle.write("\nRead [missing guidance](MISSING.md).\n")

        messages = [error.message for error in validate_skills.validate_repository(root)]
        self.assertTrue(any("relative link target does not exist" in message for message in messages))

    def test_private_key_file_is_rejected(self) -> None:
        root = self.create_repository()
        (root / "unsafe.pem").write_text("not a real key", encoding="utf-8")

        messages = [error.message for error in validate_skills.validate_repository(root)]
        self.assertTrue(any("potential secret" in message for message in messages))


if __name__ == "__main__":
    unittest.main()
