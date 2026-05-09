"""Core contracts, settings, and storage helpers for LogicLlama."""

from .models import (
	EvidenceItem,
	LogicCase,
	LogicCaseStatus,
	LogicSignal,
	LogicSource,
	LogicSourceType,
	LogicStep,
	QueryFilter,
)
from .schema_projection import build_master_schema_projection
from .settings import AppSettings, get_settings
from .storage import SQLiteLogicStore

__version__ = "1.0.0"
__author__ = "LogicLlama Team"

__all__ = [
	"AppSettings",
	"EvidenceItem",
	"LogicCase",
	"LogicCaseStatus",
	"LogicSignal",
	"LogicSource",
	"LogicSourceType",
	"LogicStep",
	"QueryFilter",
	"build_master_schema_projection",
	"SQLiteLogicStore",
	"get_settings",
]