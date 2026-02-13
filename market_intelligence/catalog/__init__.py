"""
Data catalog registry for market intelligence sources.

Loads and manages catalog entries from YAML definitions, providing
schema validation, parameter checking, and catalog lookup.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional
import yaml

from core.common.logger import logger
from market_intelligence.types import (
    CatalogEntry,
    CatalogError,
    ParamSchema,
    SourceConfig,
    CacheConfig,
    AgentFormat,
    DataQuality
)


class DataCatalog:
    """
    Registry of all available market intelligence data sources.

    Loads catalog entries from YAML files and provides lookup/validation.
    """

    def __init__(self, catalog_dir: Optional[str] = None):
        """
        Initialize data catalog.

        Args:
            catalog_dir: Path to catalog directory (defaults to market_intelligence/catalog/data_types/)
        """
        if catalog_dir is None:
            # Default to data_types/ in the catalog package
            base_dir = Path(__file__).parent
            catalog_dir = base_dir / "data_types"

        self.catalog_dir = Path(catalog_dir)
        self.entries: Dict[str, CatalogEntry] = {}
        self._log = logger.bind(component="data_catalog")

    def load_all(self):
        """
        Load all catalog entries from YAML files.

        Raises:
            CatalogError: If any catalog file is invalid
        """
        if not self.catalog_dir.exists():
            raise CatalogError(f"Catalog directory not found: {self.catalog_dir}")

        yaml_files = list(self.catalog_dir.rglob("*.yaml")) + list(self.catalog_dir.rglob("*.yml"))

        if not yaml_files:
            self._log.warning(f"No catalog files found in {self.catalog_dir}")
            return

        loaded_count = 0
        for yaml_file in yaml_files:
            try:
                entry = self._load_catalog_file(yaml_file)
                self.entries[entry.name] = entry
                loaded_count += 1
                self._log.debug(f"Loaded catalog entry: {entry.name}")
            except Exception as e:
                self._log.error(f"Failed to load catalog file {yaml_file}: {e}")
                raise CatalogError(f"Invalid catalog file {yaml_file}: {e}")

        self._log.debug(f"Loaded {loaded_count} catalog entries from {self.catalog_dir}")

    def _load_catalog_file(self, yaml_file: Path) -> CatalogEntry:
        """Load and parse a single catalog YAML file."""
        with open(yaml_file, 'r') as f:
            data = yaml.safe_load(f)

        if not data:
            raise CatalogError(f"Empty catalog file: {yaml_file}")

        # Parse required fields
        name = data.get('name')
        if not name:
            raise CatalogError(f"Catalog entry missing 'name' field in {yaml_file}")

        category = data.get('category')
        if not category:
            raise CatalogError(f"Catalog entry missing 'category' field in {yaml_file}")

        description = data.get('description', '')

        # Parse query parameters
        query_params = {}
        for param_name, param_data in data.get('query_params', {}).items():
            query_params[param_name] = ParamSchema(
                type=param_data.get('type', 'string'),
                required=param_data.get('required', False),
                default=param_data.get('default'),
                description=param_data.get('description', ''),
                enum=param_data.get('enum'),
                min=param_data.get('min'),
                max=param_data.get('max'),
                items=param_data.get('items'),
                properties=param_data.get('properties')
            )

        # Parse sources
        sources = []
        for source_data in data.get('sources', []):
            sources.append(SourceConfig(
                adapter=source_data.get('adapter'),
                priority=source_data.get('priority', 999),
                cost=source_data.get('cost', 0.0),
                rate_limit=source_data.get('rate_limit'),
                required_env=source_data.get('required_env', [])
            ))

        if not sources:
            raise CatalogError(f"Catalog entry has no sources defined in {yaml_file}")

        # Parse cache config
        cache_data = data.get('cache', {})
        cache = CacheConfig(
            backend=cache_data.get('backend', 'redis'),
            ttl=cache_data.get('ttl', 3600),
            key_pattern=cache_data.get('key_pattern', 'intel:{name}:{{symbol}}')
        )

        # Parse response schema
        response_schema = data.get('response_schema', {})

        # Parse agent format (optional)
        agent_format = None
        if 'agent_format' in data:
            af_data = data['agent_format']
            agent_format = AgentFormat(
                summary_template=af_data.get('summary_template', ''),
                insights=af_data.get('insights', [])
            )

        # Parse data quality (optional)
        data_quality = None
        if 'data_quality' in data:
            dq_data = data['data_quality']
            data_quality = DataQuality(
                latency_target_ms=dq_data.get('latency_target_ms'),
                freshness_target_seconds=dq_data.get('freshness_target_seconds'),
                confidence_scoring=dq_data.get('confidence_scoring', True)
            )

        # Parse examples (optional)
        examples = data.get('examples', [])

        return CatalogEntry(
            name=name,
            category=category,
            description=description,
            query_params=query_params,
            sources=sources,
            cache=cache,
            response_schema=response_schema,
            agent_format=agent_format,
            data_quality=data_quality,
            examples=examples
        )

    def get(self, data_type: str) -> Optional[CatalogEntry]:
        """
        Get catalog entry by data type name.

        Args:
            data_type: Name of the data type (e.g., 'ohlcv', 'twitter_sentiment')

        Returns:
            CatalogEntry if found, None otherwise
        """
        return self.entries.get(data_type)

    def list_all(self) -> List[str]:
        """Get list of all available data types."""
        return list(self.entries.keys())

    def list_by_category(self, category: str) -> List[str]:
        """
        Get list of data types in a specific category.

        Args:
            category: Category name (e.g., 'market_data', 'sentiment')

        Returns:
            List of data type names in that category
        """
        return [
            name for name, entry in self.entries.items()
            if entry.category == category
        ]

    def validate_catalog_entry(self, entry: CatalogEntry):
        """
        Validate a catalog entry for completeness.

        Args:
            entry: Catalog entry to validate

        Raises:
            CatalogError: If validation fails
        """
        # Check required fields
        if not entry.name:
            raise CatalogError("Catalog entry missing 'name'")

        if not entry.category:
            raise CatalogError(f"Catalog entry '{entry.name}' missing 'category'")

        if not entry.sources:
            raise CatalogError(f"Catalog entry '{entry.name}' has no sources")

        # Validate cache key pattern has placeholders
        if '{' not in entry.cache.key_pattern:
            self._log.warning(
                f"Cache key pattern for '{entry.name}' has no placeholders, "
                f"all queries will use same key"
            )

        # Validate source adapters
        for source in entry.sources:
            if not source.adapter:
                raise CatalogError(f"Source in '{entry.name}' missing adapter class name")

        self._log.debug(f"Validated catalog entry: {entry.name}")

    def reload(self):
        """Reload all catalog entries from disk."""
        self.entries.clear()
        self.load_all()
        self._log.info("Catalog reloaded")
