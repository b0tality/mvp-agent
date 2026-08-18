"""
状态管理器工具
提供通用的状态管理功能
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass, field
import json
import pickle
from pathlib import Path


@dataclass
class StateSnapshot:
    """状态快照"""
    timestamp: str
    state: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)


class StateManager:
    """通用状态管理器"""
    
    def __init__(self, persistence_path: Optional[str] = None):
        """
        初始化状态管理器
        
        Args:
            persistence_path: 状态持久化路径
        """
        self._state: Dict[str, Any] = {}
        self._history: List[StateSnapshot] = []
        self._persistence_path = persistence_path
        
        # 如果有持久化路径，加载历史状态
        if persistence_path:
            self._load_state()
    
    def update(self, key: str, value: Any) -> None:
        """更新状态"""
        old_value = self._state.get(key)
        self._state[key] = value
        
        # 记录历史
        self._history.append(StateSnapshot(
            timestamp=datetime.now().isoformat(),
            state=self._state.copy(),
            metadata={"action": "update", "key": key, "old_value": old_value}
        ))
        
        # 持久化
        if self._persistence_path:
            self._save_state()
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取状态值"""
        return self._state.get(key, default)
    
    def get_all(self) -> Dict[str, Any]:
        """获取完整状态"""
        return self._state.copy()
    
    def delete(self, key: str) -> bool:
        """删除状态"""
        if key in self._state:
            old_value = self._state.pop(key)
            
            # 记录历史
            self._history.append(StateSnapshot(
                timestamp=datetime.now().isoformat(),
                state=self._state.copy(),
                metadata={"action": "delete", "key": key, "old_value": old_value}
            ))
            
            # 持久化
            if self._persistence_path:
                self._save_state()
            
            return True
        return False
    
    def clear(self) -> None:
        """清空状态"""
        self._state.clear()
        
        # 记录历史
        self._history.append(StateSnapshot(
            timestamp=datetime.now().isoformat(),
            state=self._state.copy(),
            metadata={"action": "clear"}
        ))
        
        # 持久化
        if self._persistence_path:
            self._save_state()
    
    def get_history(self, limit: Optional[int] = None) -> List[StateSnapshot]:
        """获取历史记录"""
        if limit:
            return self._history[-limit:]
        return self._history.copy()
    
    def rollback(self, steps: int = 1) -> bool:
        """回滚到之前的状态"""
        if len(self._history) >= steps:
            # 移除最近的步骤
            for _ in range(steps):
                if self._history:
                    self._history.pop()
            
            # 恢复到上一个状态
            if self._history:
                self._state = self._history[-1].state.copy()
            else:
                self._state.clear()
            
            # 持久化
            if self._persistence_path:
                self._save_state()
            
            return True
        return False
    
    def _save_state(self) -> None:
        """保存状态到文件"""
        if not self._persistence_path:
            return
        
        path = Path(self._persistence_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            "state": self._state,
            "history": [
                {
                    "timestamp": h.timestamp,
                    "state": h.state,
                    "metadata": h.metadata
                }
                for h in self._history
            ]
        }
        
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _load_state(self) -> None:
        """从文件加载状态"""
        if not self._persistence_path:
            return
        
        path = Path(self._persistence_path)
        if not path.exists():
            return
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            self._state = data.get("state", {})
            self._history = [
                StateSnapshot(
                    timestamp=h["timestamp"],
                    state=h["state"],
                    metadata=h.get("metadata", {})
                )
                for h in data.get("history", [])
            ]
        except Exception as e:
            print(f"加载状态失败: {e}")
    
    def export_state(self, format: str = "json") -> str:
        """导出状态"""
        if format == "json":
            return json.dumps(self._state, ensure_ascii=False, indent=2)
        elif format == "pickle":
            import base64
            return base64.b64encode(pickle.dumps(self._state)).decode()
        else:
            raise ValueError(f"不支持的格式: {format}")
    
    def import_state(self, data: str, format: str = "json") -> None:
        """导入状态"""
        if format == "json":
            self._state = json.loads(data)
        elif format == "pickle":
            import base64
            self._state = pickle.loads(base64.b64decode(data))
        else:
            raise ValueError(f"不支持的格式: {format}")
        
        # 记录历史
        self._history.append(StateSnapshot(
            timestamp=datetime.now().isoformat(),
            state=self._state.copy(),
            metadata={"action": "import"}
        ))
        
        # 持久化
        if self._persistence_path:
            self._save_state()
