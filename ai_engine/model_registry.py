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
        
        # Export ONNX model (use latest supported opset to avoid costly version conversions)
        dummy_input = torch.randn(1, feature_count).to(next(model.parameters()).device)
        # select an opset version high enough that torch will not auto-upgrade
        opset_version = 18
        onnx_path = version_dir / "model.onnx"
        
        try:
            # Use export_params=True + do_constant_folding for smaller models
            torch.onnx.export(
                model,
                (dummy_input,),
                str(onnx_path),
                input_names=["input"],
                output_names=["reconstruction", "latent"],
                # specify dynamic batch dimension using new API (avoids dynamo warning)
                dynamic_shapes={"input": {0: "batch_size"}},
                # request modern opset – torch may still bump this further
                opset_version=18,  # >=18 avoids automatic up/down conversion issues
                export_params=True,
                do_constant_folding=True
            )
            logger.info(f"✅ Exported ONNX model (opset {opset_version}) to {onnx_path}")
        except ModuleNotFoundError as e:
            # common missing dependency when torch tries to lazily import onnxscript
            logger.error(f"❌ ONNX export failed: {e}")
            logger.error("   (hint: install the 'onnxscript' package or an appropriate onnx runtime build)")
            logger.info("⚠️  Falling back to PyTorch save (Service 1 will need torch)")
            torch.save(model.state_dict(), version_dir / "model.pth")
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
        """Safely update 'latest' symlink (handles directory leftovers)

        We aggressively clean up whatever already exists at ``latest`` before
        creating the new symlink.  ``os.symlink`` will raise ``FileExistsError``
        if the destination path already exists, which is exactly what was
        observed in the logs during normal operation.  After a failed
        symlink attempt we erase the target and fall back to copying the
        versioned directory so the learning engine can continue without a
        broken link.
        """
        # remove any pre-existing entity (symlink, file or directory)
        if self.latest_dir.exists() or self.latest_dir.is_symlink():
            try:
                if self.latest_dir.is_symlink() or self.latest_dir.is_file():
                    os.unlink(self.latest_dir)
                    logger.debug("Removed existing 'latest' symlink/file")
                elif self.latest_dir.is_dir():
                    backup_name = f"latest_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}"
                    backup_path = self.model_dir / backup_name
                    shutil.move(str(self.latest_dir), str(backup_path))
                    logger.warning(
                        f"⚠️  'latest' was a directory (not symlink); backed up to {backup_name}"
                    )
            except Exception as cleanup_err:
                logger.warning(f"⚠️  unable to clean up old 'latest' entry: {cleanup_err}")

        # try creating the symlink; if it still fails fall back to copy
        try:
            os.symlink(target_dir.absolute(), self.latest_dir)
            logger.debug(f"Created symlink: latest -> {target_dir.name}")
        except OSError as e:
            logger.error(f"❌ Symlink creation failed: {e}")
            logger.info("⚠️  Falling back to directory copy (less efficient)")
            # ensure nothing remains before copying
            if self.latest_dir.exists() or self.latest_dir.is_symlink():
                try:
                    if self.latest_dir.is_dir():
                        shutil.rmtree(self.latest_dir)
                    else:
                        os.unlink(self.latest_dir)
                except Exception as rm_err:
                    logger.warning(f"⚠️  could not remove existing fallback target: {rm_err}")
            shutil.copytree(target_dir, self.latest_dir, dirs_exist_ok=True)
