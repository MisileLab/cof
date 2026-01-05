"""
Git interoperability helpers for cof.
"""

from pathlib import Path
from typing import Tuple

import pygit2

README_TEMPLATE = """# cof repository

This repository stores data as cof chunks and metadata.

To work with this repo, install cof:

- uv tool install git+https://github.com/misilelab/cof
- cof --help
"""

GITIGNORE_TEMPLATE = """*
!.cof/
!.cof/**
!README.md
!.gitignore
!.cofignore
"""

COFIGNORE_TEMPLATE = """.cof/
.git/
__pycache__/
.venv/
"""


class GitMirror:
    """Mirror cof state into minimal git objects."""

    def __init__(self, repo_path: Path) -> None:
        self.repo_path = repo_path
        self.repo = self._open_or_init_repo()

    def _open_or_init_repo(self) -> pygit2.Repository:
        git_dir = self.repo_path / ".git"
        if git_dir.exists():
            return pygit2.Repository(str(git_dir))
        return pygit2.init_repository(str(self.repo_path), bare=False)

    def ensure_templates(self) -> None:
        readme_path = self.repo_path / "README.md"
        if not readme_path.exists():
            readme_path.write_text(README_TEMPLATE, encoding="utf-8")

        gitignore_path = self.repo_path / ".gitignore"
        if not gitignore_path.exists():
            gitignore_path.write_text(GITIGNORE_TEMPLATE, encoding="utf-8")

        cofignore_path = self.repo_path / ".cofignore"
        if not cofignore_path.exists():
            cofignore_path.write_text(COFIGNORE_TEMPLATE, encoding="utf-8")

    def commit_snapshot(self, message: str, author: Tuple[str, str]) -> str:
        self.ensure_templates()
        index = self.repo.index
        index.read()
        index.add_all([".cof", "README.md", ".gitignore", ".cofignore"])
        index.write()
        tree_id = index.write_tree()

        name, email = author
        signature = pygit2.Signature(name, email)
        parents = []
        if not self.repo.head_is_unborn:
            parents = [self.repo.head.target]

        commit_id = self.repo.create_commit(
            "HEAD", signature, signature, message, tree_id, parents
        )
        return str(commit_id)

    def create_branch(self, name: str) -> None:
        if self.repo.head_is_unborn:
            return
        target = self.repo[self.repo.head.target]
        self.repo.create_branch(name, target, force=True)

    def checkout_branch(self, name: str) -> None:
        ref_name = f"refs/heads/{name}"
        self.repo.set_head(ref_name)
        self.repo.checkout_head(strategy=pygit2.GIT_CHECKOUT_FORCE)
