"""Legacy import alias; all updates now use the manual release workflow."""
from .updater import UpdateManager, update_manager

__all__ = ['UpdateManager', 'update_manager']
