"""
Configuration management for the RAG system.

This module handles dataset discovery, configuration management, and provides
a centralized way to manage system settings without hardcoding.
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class DatasetConfig:
    """Configuration for a single dataset."""
    name: str
    path: Path
    document_id: str
    description: str
    domain: Optional[str] = None
    page_count: Optional[int] = None
    table_count: Optional[int] = None
    keyword_count: Optional[int] = None

@dataclass
class SystemConfig:
    """Main system configuration."""
    datasets: Dict[str, DatasetConfig]
    data_root: Path
    default_dataset: Optional[str] = None
    llm_config: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.llm_config is None:
            self.llm_config = {}

class DataDiscovery:
    """Handles automatic discovery of available datasets."""
    
    def __init__(self, data_root: Optional[Path] = None):
        """
        Initialize data discovery.
        
        Args:
            data_root: Root directory for data. Defaults to project_root/data
        """
        if data_root is None:
            # Find project root (assuming we're in src/)
            current_dir = Path(__file__).parent
            project_root = current_dir.parent
            data_root = project_root / "data"
        
        self.data_root = data_root
        logger.info(f"Data discovery initialized with root: {data_root}")
    
    def discover_datasets(self) -> Dict[str, DatasetConfig]:
        """
        Discover all available datasets in the data directory.
        
        Returns:
            Dictionary mapping dataset names to DatasetConfig objects
        """
        datasets = {}
        
        if not self.data_root.exists():
            logger.warning(f"Data root directory does not exist: {self.data_root}")
            return datasets
        
        # Look for directories that contain final_output.json
        for item in self.data_root.iterdir():
            if item.is_dir():
                final_output_path = item / "final_output.json"
                if final_output_path.exists():
                    try:
                        dataset_config = self._load_dataset_config(item, final_output_path)
                        if dataset_config:
                            datasets[dataset_config.name] = dataset_config
                            logger.info(f"Discovered dataset: {dataset_config.name}")
                    except Exception as e:
                        logger.error(f"Error loading dataset from {item}: {e}")
        
        logger.info(f"Discovered {len(datasets)} datasets")
        return datasets
    
    def _load_dataset_config(self, dataset_dir: Path, final_output_path: Path) -> Optional[DatasetConfig]:
        """
        Load configuration for a single dataset.
        
        Args:
            dataset_dir: Directory containing the dataset
            final_output_path: Path to final_output.json
            
        Returns:
            DatasetConfig object or None if loading fails
        """
        try:
            # Load final_output.json to get document info
            with open(final_output_path, 'r') as f:
                data = json.load(f)
            
            document_info = data.get('document_info', {})
            document_summary = data.get('document_summary', {})
            
            # Extract basic info
            document_id = document_info.get('document_id', dataset_dir.name)
            page_count = document_info.get('total_pages', 0)
            table_count = document_info.get('total_tables', 0)
            keyword_count = document_info.get('total_keywords', 0)
            
            # Generate a human-readable name
            name = self._generate_dataset_name(document_id, document_summary)
            
            # Try to detect domain from content
            domain = self._detect_domain(document_summary)
            
            # Generate description
            description = self._generate_description(document_summary, page_count, table_count)
            
            return DatasetConfig(
                name=name,
                path=final_output_path,
                document_id=document_id,
                description=description,
                domain=domain,
                page_count=page_count,
                table_count=table_count,
                keyword_count=keyword_count
            )
            
        except Exception as e:
            logger.error(f"Error loading dataset config from {final_output_path}: {e}")
            return None
    
    def _generate_dataset_name(self, document_id: str, document_summary: Dict[str, Any]) -> str:
        """Generate a human-readable name for the dataset."""
        # Try to extract a meaningful name from page titles
        page_titles = document_summary.get('page_titles', [])
        if page_titles:
            # Use the first non-empty title
            for title in page_titles:
                if title and title.strip():
                    # Clean up the title for display
                    clean_title = title.strip()
                    # Truncate if too long
                    if len(clean_title) > 50:
                        clean_title = clean_title[:47] + "..."
                    return clean_title
        
        # Fallback to document_id with some cleaning
        return document_id.replace('_', ' ').title()
    
    def _detect_domain(self, document_summary: Dict[str, Any]) -> Optional[str]:
        """Detect the domain of the document from its content."""
        keywords = document_summary.get('combined_keywords', [])
        page_titles = document_summary.get('page_titles', [])
        
        # Combine all text for analysis
        all_text = ' '.join(keywords + page_titles).lower()
        
        # Simple domain detection based on keywords
        if any(word in all_text for word in ['surgical', 'medical', 'protocol', 'acetabular', 'trident']):
            return 'medical'
        elif any(word in all_text for word in ['peanut', 'butter', 'jelly', 'sandwich', 'cooking']):
            return 'cooking'
        elif any(word in all_text for word in ['technical', 'specification', 'engineering']):
            return 'technical'
        elif any(word in all_text for word in ['legal', 'contract', 'agreement']):
            return 'legal'
        else:
            return 'general'
    
    def _generate_description(self, document_summary: Dict[str, Any], page_count: int, table_count: int) -> str:
        """Generate a description for the dataset."""
        parts = []
        
        if page_count > 0:
            parts.append(f"{page_count} pages")
        
        if table_count > 0:
            parts.append(f"{table_count} tables")
        
        # Add some context from page titles
        page_titles = document_summary.get('page_titles', [])
        if page_titles:
            # Use the first meaningful title
            for title in page_titles:
                if title and len(title.strip()) > 10:
                    parts.append(f"Topic: {title.strip()}")
                    break
        
        if parts:
            return " • ".join(parts)
        else:
            return "Document dataset"

class ConfigManager:
    """Main configuration manager for the system."""
    
    def __init__(self, data_root: Optional[Path] = None):
        """
        Initialize the configuration manager.
        
        Args:
            data_root: Root directory for data
        """
        self.discovery = DataDiscovery(data_root)
        self.config = self._load_config()
    
    def _load_config(self) -> SystemConfig:
        """Load the system configuration."""
        datasets = self.discovery.discover_datasets()
        
        # Set default dataset (first one found, or None)
        default_dataset = None
        if datasets:
            # Prefer medical datasets as default, then any available
            for name, dataset in datasets.items():
                if dataset.domain == 'medical':
                    default_dataset = name
                    break
            if not default_dataset:
                default_dataset = list(datasets.keys())[0]
        
        return SystemConfig(
            datasets=datasets,
            default_dataset=default_dataset,
            data_root=self.discovery.data_root,
            llm_config={}
        )
    
    def get_dataset_config(self, dataset_name: Optional[str] = None) -> Optional[DatasetConfig]:
        """
        Get configuration for a specific dataset.
        
        Args:
            dataset_name: Name of the dataset. If None, returns default dataset.
            
        Returns:
            DatasetConfig object or None if not found
        """
        if dataset_name is None:
            dataset_name = self.config.default_dataset
        
        if dataset_name is None:
            return None
        
        return self.config.datasets.get(dataset_name)
    
    def get_dataset_path(self, dataset_name: Optional[str] = None) -> Optional[Path]:
        """
        Get the path to a dataset's final_output.json.
        
        Args:
            dataset_name: Name of the dataset. If None, returns default dataset.
            
        Returns:
            Path to final_output.json or None if not found
        """
        dataset_config = self.get_dataset_config(dataset_name)
        return dataset_config.path if dataset_config else None
    
    def list_datasets(self) -> List[Dict[str, Any]]:
        """
        Get a list of all available datasets with their info.
        
        Returns:
            List of dictionaries with dataset information
        """
        datasets = []
        for name, config in self.config.datasets.items():
            datasets.append({
                'name': name,
                'document_id': config.document_id,
                'description': config.description,
                'domain': config.domain,
                'page_count': config.page_count,
                'table_count': config.table_count,
                'keyword_count': config.keyword_count,
                'is_default': name == self.config.default_dataset
            })
        return datasets
    
    def refresh_datasets(self):
        """Refresh the dataset discovery."""
        logger.info("Refreshing dataset discovery...")
        self.config = self._load_config()
        logger.info(f"Found {len(self.config.datasets)} datasets")

# Global configuration instance
_config_manager = None

def get_config_manager(data_root: Optional[Path] = None) -> ConfigManager:
    """
    Get the global configuration manager instance.
    
    Args:
        data_root: Root directory for data (only used on first call)
        
    Returns:
        ConfigManager instance
    """
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager(data_root)
    return _config_manager

def get_dataset_path(dataset_name: Optional[str] = None) -> Optional[Path]:
    """
    Convenience function to get dataset path.
    
    Args:
        dataset_name: Name of the dataset. If None, returns default dataset.
        
    Returns:
        Path to final_output.json or None if not found
    """
    config_manager = get_config_manager()
    return config_manager.get_dataset_path(dataset_name)

def list_datasets() -> List[Dict[str, Any]]:
    """
    Convenience function to list all datasets.
    
    Returns:
        List of dictionaries with dataset information
    """
    config_manager = get_config_manager()
    return config_manager.list_datasets() 