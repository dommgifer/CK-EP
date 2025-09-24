"""
T023: VMNode 模型
VM 節點相關模型（已整合到 vm_cluster_config.py 中）
"""
# 此檔案的內容已整合到 vm_cluster_config.py 中
# 為保持任務清單完整性而建立此檔案

from .vm_cluster_config import VMNode, VMNodeSpecs

__all__ = ["VMNode", "VMNodeSpecs"]