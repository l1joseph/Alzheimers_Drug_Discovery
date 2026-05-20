#!/bin/bash
#SBATCH --job-name=tamgen-smoke-env
#SBATCH --output=/cosmos/nfs/home/l1joseph/Alzheimers_Drug_Discovery/logs/%x_%j.out
#SBATCH --error=/cosmos/nfs/home/l1joseph/Alzheimers_Drug_Discovery/logs/%x_%j.err
#SBATCH --partition=cluster
#SBATCH --nodes=1
#SBATCH --time=00:15:00

set -euo pipefail

PROJECT="/cosmos/nfs/home/l1joseph/Alzheimers_Drug_Discovery"

ts=$(date +%Y%m%d-%H%M%S)
ln -sf "${SLURM_JOB_NAME}_${SLURM_JOB_ID}.out" "$PROJECT/logs/${ts}_${SLURM_JOB_NAME}_${SLURM_JOB_ID}.out"
ln -sf "${SLURM_JOB_NAME}_${SLURM_JOB_ID}.err" "$PROJECT/logs/${ts}_${SLURM_JOB_NAME}_${SLURM_JOB_ID}.err"

module load rocm/6.3.0 2>&1 | tail -3 || true
source ~/miniforge3/etc/profile.d/conda.sh
conda activate tamgen-rocm

echo "=== Environment ==="
echo "host: $(hostname)"
echo "python: $(python --version)"
python -c "
import torch
print('torch:', torch.__version__, 'hip:', torch.version.hip)
print('cuda_available:', torch.cuda.is_available())
print('device_count:', torch.cuda.device_count())
for i in range(torch.cuda.device_count()):
    print(f'  device {i}: {torch.cuda.get_device_name(i)}')
"
echo
echo "=== TamGen / fairseq imports ==="
python -c "
import fairseq
print('fairseq:', fairseq.__version__)
from fairseq import checkpoint_utils, options, tasks, utils
print('fairseq core modules: OK')
import rdkit
print('rdkit:', rdkit.__version__)
"
echo
echo "=== torch_cluster import (may fail on first run) ==="
python -c "
try:
    import torch_cluster
    print('torch_cluster:', torch_cluster.__version__)
    from torch_cluster import knn, knn_graph, fps
    print('torch_cluster.knn / knn_graph / fps: OK')
except Exception as e:
    print('torch_cluster IMPORT FAILED:', e)
" || echo "(continuing despite torch_cluster failure)"
echo
echo "=== TamGen pointcloud module sanity ==="
cd "$PROJECT/tools/TamGen"
python -c "
import sys; sys.path.insert(0, '.')
try:
    from fairseq.modules.pointcloud import point_transformer_layer
    print('TamGen pointcloud transformer layer: importable')
except Exception as e:
    print('pointcloud import failed:', e)
"
echo
echo "=== Done at $(date) ==="
