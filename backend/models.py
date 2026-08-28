"""Domain models for Translation Workbench projects and series."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Literal


class ProjectStatus(StrEnum):
    NEW = "new"
    ANALYSIS = "analysis"
    TRANSLATION = "translation"
    AUDIT = "audit"
    COMPLETED = "completed"


StorageType = Literal["local", "object-storage", "external-reference"]


@dataclass
class Progress:
    progress: float = 0
    analysisProgress: float = 0
    translationProgress: float = 0
    auditProgress: float = 0

    def __post_init__(self):
        for value in (
            self.progress,
            self.analysisProgress,
            self.translationProgress,
            self.auditProgress,
        ):
            if not 0 <= value <= 100:
                raise ValueError("Progress values must be between 0 and 100.")


@dataclass
class SourceFile:
    fileName: str | None = None
    storageType: StorageType | None = None
    storageKey: str | None = None
    checksum: str | None = None


@dataclass
class Rule:
    ruleId: str
    text: str
    category: str | None = None
    priority: int | None = None
    active: bool = True
    updatedAt: datetime | None = None


@dataclass
class GlossaryEntry:
    glossaryEntryId: str
    source: str
    target: str
    note: str | None = None
    active: bool = True


@dataclass
class Author:
    authorId: str
    name: str


@dataclass
class InheritedRuleReference:
    ruleId: str
    confirmed: bool = False
    confirmedAt: datetime | None = None


@dataclass
class InheritedGlossaryReference:
    glossaryEntryId: str
    confirmed: bool = False
    confirmedAt: datetime | None = None


@dataclass
class Series:
    seriesId: str
    name: str


@dataclass
class SeriesAuthorContext:
    seriesId: str
    authorId: str
    ruleIds: list[str] = field(default_factory=list)
    glossaryEntryIds: list[str] = field(default_factory=list)


@dataclass
class BookProject:
    projectId: str
    title: str
    authorId: str | None = None
    seriesId: str | None = None
    status: ProjectStatus = ProjectStatus.NEW
    progress: Progress = field(default_factory=Progress)
    chapterCount: int = 0
    fileName: str | None = None
    createdAt: datetime | None = None
    updatedAt: datetime | None = None
    sourceFile: SourceFile | None = None
    inheritedRules: list[InheritedRuleReference] = field(default_factory=list)
    inheritedGlossary: list[InheritedGlossaryReference] = field(default_factory=list)
    projectRuleIds: list[str] = field(default_factory=list)
    projectGlossaryEntryIds: list[str] = field(default_factory=list)
    styleNotes: list[str] = field(default_factory=list)
    characterNotes: list[str] = field(default_factory=list)
    contextNotes: list[str] = field(default_factory=list)

    def __post_init__(self):
        if self.chapterCount < 0:
            raise ValueError("chapterCount cannot be negative.")


Project = BookProject


__all__ = [
    "Author",
    "BookProject",
    "GlossaryEntry",
    "InheritedGlossaryReference",
    "InheritedRuleReference",
    "Progress",
    "Project",
    "ProjectStatus",
    "Rule",
    "Series",
    "SeriesAuthorContext",
    "SourceFile",
]
