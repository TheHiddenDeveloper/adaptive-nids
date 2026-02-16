"""
Model registry - robust ONNX export + symlink handling
"""
import os
import json
import shutil
import torch
from datetime import datetime
from pathlib import Path
import logging

logger = logging.getLogger("ModelRegistry")

class ModelRegistry:
    def __init__(self, model_dir: str = "/models"):
        self.model_dir = Path(model_dir)
        self.latest_dir = self.model_dir / "latest"
        self.archive_dir = self.model_dir / "archive"
        self.archive_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Model registry initialized at {model_dir}")
    
    def export_onnx(self, model: torch.nn.Module, scaler, threshold: float, feature_count: int = 85):
        """Export model with robust symlink handling"""
        # Create versioned directory
        version = datetime.now().strftime("v_%Y%m%d_%H%M%S")
        version_dir = self.archive_dir / version
        version_dir.mkdir(exist_ok=True)
        
        # Export ONNX model (opset 11 for maximum compatibility)
        dummy_input = torch.randn(1, feature_count).to(next(model.parameters()).device)
        onnx_path = version_dir / "model.onnx"
        
        try:
            # Use export_params=True + do_constant_folding for smaller models
            torch.onnx.export(
                model,
                dummy_input,
                str(onnx_path),
                input_names=["input"],
                output_names=["reconstruction", "latent"],
                dynamic_axes={"input": {0: "batch_size"}},
                opset_version=11,  # ✅ Stable version - no onnxscript required
                export_params=True,
                do_constant_folding=True
            )
            logger.info(f"✅ Exported ONNX model (opset 11) to {onnx_path}")
        except Exception as e:
            logger.error(f"❌ ONNX export failed: {e}")
            logger.info("⚠️  Falling back to PyTorch save (Service 1 will need torch)")
            torch.save(model.state_dict(), version_dir / "model.pth")
        
        # Save scaler and metadata
        import joblib
        joblib.dump(scaler, version_dir / "scaler.pkl")
        
        metadata = {
            "version": version,
            "exported_at": datetime.utcnow().isoformat() + "Z",
            "threshold": threshold,
            "feature_count": feature_count,
            "model_type": "denoising_autoencoder",
            "training_flows": "unsupervised_baseline",
            "adaptive_threshold_percentile": 95,
            "opset_version": 11
        }
        with open(version_dir / "metadata.json", "w") as f:
            json.dump(metadata, f, indent=2)
        
        # 🔑 CRITICAL FIX: Robust symlink handling
        self._update_latest_symlink(version_dir)
        
        logger.info(f"✓ Model deployed to {version_dir}")
        logger.info(f"  → Active model: {self.latest_dir} -> {version_dir.name}")
        return version_dir
    
    def _update_latest_symlink(self, target_dir: Path):
        """Safely update 'latest' symlink (handles directory leftovers)"""
        if self.latest_dir.exists():
            if self.latest_dir.is_symlink():
                # Normal case: remove existing symlink
                os.unlink(self.latest_dir)
                logger.debug("Removed existing 'latest' symlink")
            elif self.latest_dir.is_dir():
                # Error case: 'latest' is a directory (from interrupted previous run)
                backup_name = f"latest_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                backup_path = self.model_dir / backup_name
                shutil.move(str(self.latest_dir), str(backup_path))
                logger.warning(f"⚠️  'latest' was a directory (not symlink). Backed up to {backup_name}")
            else:
                # Unexpected case: file (not dir/symlink)
                self.latest_dir.unlink()
                logger.warning("⚠️  'latest' was a regular file - removed")
        
        # Create new symlink
        try:
            os.symlink(target_dir.absolute(), self.latest_dir)
            logger.debug(f"Created symlink: latest -> {target_dir.name}")
        except OSError as e:
            logger.error(f"❌ Symlink creation failed: {e}")
            logger.info("⚠️  Falling back to directory copy (less efficient)")
            shutil.copytree(target_dir, self.latest_dir, dirs_exist_ok=True)