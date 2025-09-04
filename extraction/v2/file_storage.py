"""
File-based storage for V2 extraction results.

This module handles saving extraction results to JSON files instead of database
to avoid serialization issues while maintaining all data.
"""

import os
import json
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

from core.common.logger import logger


class FileStorage:
    """
    File-based storage for extraction results.
    
    Saves results as JSON files with proper timestamp and pandas object handling.
    """
    
    def __init__(self, base_dir: str = "extraction_results"):
        """
        Initialize file storage.
        
        Args:
            base_dir: Base directory for storing results
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        (self.base_dir / "single_symbol").mkdir(exist_ok=True)
        (self.base_dir / "multi_symbol").mkdir(exist_ok=True)
        (self.base_dir / "daily").mkdir(exist_ok=True)
        
        self._log = logger.bind(component="file_storage")
        self._log.info(f"Initialized FileStorage at {self.base_dir}")
    
    def save_extraction_result(self, result: Dict[str, Any], result_type: str = "single") -> str:
        """
        Save extraction result to file.
        
        Args:
            result: Extraction result dictionary
            result_type: Type of result ("single", "multi", "config")
            
        Returns:
            Path to saved file
        """
        try:
            # Convert pandas objects to serializable format
            serializable_result = self._make_serializable(result)
            
            # Generate filename
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            symbol = result.get("symbol", "unknown").replace("/", "_")
            filename = f"{timestamp}_{symbol}_{result_type}.json"
            
            # Choose subdirectory
            if result_type == "multi":
                filepath = self.base_dir / "multi_symbol" / filename
            elif result_type == "config":
                filepath = self.base_dir / "daily" / filename
            else:
                filepath = self.base_dir / "single_symbol" / filename
            
            # Save to file
            with open(filepath, 'w') as f:
                json.dump(serializable_result, f, indent=2, default=str)
            
            self._log.info(f"✅ Saved extraction result to {filepath}")
            return str(filepath)
            
        except Exception as e:
            self._log.error(f"❌ Failed to save result: {str(e)}")
            return ""
    
    def save_multiple_results(self, results: Dict[str, Any], batch_name: str = None) -> str:
        """
        Save multiple extraction results to single file.
        
        Args:
            results: Dictionary of results by symbol
            batch_name: Optional batch name for filename
            
        Returns:
            Path to saved file
        """
        try:
            # Convert all results to serializable format
            serializable_results = {}
            for symbol, result in results.items():
                serializable_results[symbol] = self._make_serializable(result)
            
            # Generate filename
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            if batch_name:
                filename = f"{timestamp}_{batch_name}_batch.json"
            else:
                symbols_count = len(results)
                filename = f"{timestamp}_{symbols_count}symbols_batch.json"
            
            filepath = self.base_dir / "multi_symbol" / filename
            
            # Add metadata
            batch_result = {
                "timestamp": datetime.utcnow().isoformat(),
                "batch_name": batch_name,
                "symbol_count": len(results),
                "symbols": list(results.keys()),
                "results": serializable_results
            }
            
            # Save to file
            with open(filepath, 'w') as f:
                json.dump(batch_result, f, indent=2, default=str)
            
            self._log.info(f"✅ Saved batch of {len(results)} results to {filepath}")
            return str(filepath)
            
        except Exception as e:
            self._log.error(f"❌ Failed to save batch results: {str(e)}")
            return ""
    
    def _make_serializable(self, obj: Any) -> Any:
        """
        Convert pandas and other objects to JSON-serializable format.
        
        Args:
            obj: Object to convert
            
        Returns:
            JSON-serializable object
        """
        if isinstance(obj, dict):
            return {key: self._make_serializable(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._make_serializable(item) for item in obj]
        elif isinstance(obj, pd.Timestamp):
            return obj.isoformat()
        elif isinstance(obj, pd.Series):
            return obj.tolist()
        elif isinstance(obj, pd.DataFrame):
            return obj.to_dict('records')
        elif hasattr(obj, 'isoformat'):  # datetime objects
            return obj.isoformat()
        elif hasattr(obj, 'item'):  # numpy scalars
            return obj.item()
        else:
            return obj
    
    def load_latest_result(self, symbol: str = None, result_type: str = "single") -> Dict[str, Any]:
        """
        Load the latest extraction result for a symbol.
        
        Args:
            symbol: Symbol to load (None for latest overall)
            result_type: Type of result to load
            
        Returns:
            Latest extraction result or empty dict
        """
        try:
            # Choose directory
            if result_type == "multi":
                search_dir = self.base_dir / "multi_symbol"
            elif result_type == "config":
                search_dir = self.base_dir / "daily"
            else:
                search_dir = self.base_dir / "single_symbol"
            
            # Find files
            pattern = "*.json"
            if symbol:
                symbol_clean = symbol.replace("/", "_")
                pattern = f"*{symbol_clean}*.json"
            
            files = list(search_dir.glob(pattern))
            if not files:
                return {}
            
            # Get latest file
            latest_file = max(files, key=lambda f: f.stat().st_mtime)
            
            # Load and return
            with open(latest_file, 'r') as f:
                result = json.load(f)
            
            self._log.info(f"✅ Loaded result from {latest_file}")
            return result
            
        except Exception as e:
            self._log.error(f"❌ Failed to load result: {str(e)}")
            return {}
    
    def list_results(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        List recent extraction results.
        
        Args:
            limit: Maximum number of results to return
            
        Returns:
            List of result metadata
        """
        try:
            results = []
            
            # Scan all subdirectories
            for subdir in ["single_symbol", "multi_symbol", "daily"]:
                search_dir = self.base_dir / subdir
                if not search_dir.exists():
                    continue
                
                for filepath in search_dir.glob("*.json"):
                    try:
                        stat = filepath.stat()
                        results.append({
                            "file": str(filepath),
                            "type": subdir,
                            "size": stat.st_size,
                            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                            "name": filepath.name
                        })
                    except Exception:
                        continue
            
            # Sort by modification time (newest first)
            results.sort(key=lambda x: x["modified"], reverse=True)
            
            return results[:limit]
            
        except Exception as e:
            self._log.error(f"❌ Failed to list results: {str(e)}")
            return []
    
    def cleanup_old_files(self, days_to_keep: int = 7) -> int:
        """
        Clean up old result files.
        
        Args:
            days_to_keep: Number of days of results to keep
            
        Returns:
            Number of files deleted
        """
        try:
            cutoff_time = datetime.utcnow().timestamp() - (days_to_keep * 24 * 3600)
            deleted_count = 0
            
            for subdir in ["single_symbol", "multi_symbol", "daily"]:
                search_dir = self.base_dir / subdir
                if not search_dir.exists():
                    continue
                
                for filepath in search_dir.glob("*.json"):
                    try:
                        if filepath.stat().st_mtime < cutoff_time:
                            filepath.unlink()
                            deleted_count += 1
                    except Exception:
                        continue
            
            self._log.info(f"✅ Cleaned up {deleted_count} old files")
            return deleted_count
            
        except Exception as e:
            self._log.error(f"❌ Failed to cleanup files: {str(e)}")
            return 0