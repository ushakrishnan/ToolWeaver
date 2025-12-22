"""
Grafana integration for ToolWeaver Phase 5 Analytics.

Handles:
- Data source creation and configuration
- Dashboard auto-generation
- Panel creation for various metric visualizations
- Real-time metric pushing to Grafana
"""

import requests
import logging
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class GrafanaConfig:
    """Grafana configuration."""

    url: str
    api_key: str
    datasource_name: str = "ToolWeaver Analytics"
    datasource_type: str = "sqlite"
    org_id: int = 1
    auto_create_dashboards: bool = True


class GrafanaClient:
    """Client for Grafana API interactions."""

    def __init__(self, config: GrafanaConfig):
        """Initialize Grafana client.

        Args:
            config: Grafana configuration.
        """
        self.config = config
        self.base_url = config.url.rstrip("/")
        self.headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json",
        }

    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
    ) -> Optional[Any]:
        """Make HTTP request to Grafana API.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE).
            endpoint: API endpoint path.
            data: Request body data.
            params: Query parameters.

        Returns:
            Response JSON or None on error.
        """
        url = f"{self.base_url}/api/{endpoint}"

        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self.headers,
                json=data,
                params=params,
                timeout=30,
            )

            if response.status_code in [200, 201]:
                return response.json()
            else:
                logger.error(
                    f"Grafana API error [{response.status_code}]: "
                    f"{response.text[:200]}"
                )
                return None

        except requests.RequestException as e:
            logger.error(f"Grafana request error: {e}")
            return None

    def health_check(self) -> bool:
        """Check Grafana connectivity.

        Returns:
            True if Grafana is accessible.
        """
        result = self._make_request("GET", "health")
        if result:
            logger.info(f"Grafana health check passed: {result.get('version')}")
            return True
        return False

    # ========================================================================
    # Data Source Management
    # ========================================================================

    def get_datasources(self) -> List[Dict[Any, Any]]:
        """Get list of data sources.

        Returns:
            List of data source configurations.
        """
        result = self._make_request("GET", "datasources")
        return result if isinstance(result, list) else []

    def get_datasource(self, name: str) -> Optional[Dict[str, Any]]:
        """Get data source by name.

        Args:
            name: Data source name.

        Returns:
            Data source configuration or None.
        """
        result = self._make_request("GET", f"datasources/name/{name}")
        return result if isinstance(result, dict) else None

    def create_datasource(
        self,
        name: str,
        db_path: str,
        datasource_type: str = "sqlite",
    ) -> Optional[Dict[str, Any]]:
        """Create new data source.

        Args:
            name: Data source name.
            db_path: Path to SQLite database.
            datasource_type: Type of data source.

        Returns:
            Created data source config or None.
        """
        payload = {
            "name": name,
            "type": datasource_type,
            "access": "proxy",
            "isDefault": True,
            "jsonData": {
                "path": db_path,
                "sqlMode": True,
            },
        }

        # Check if exists first
        existing = self.get_datasource(name)
        if existing:
            logger.info(f"Data source '{name}' already exists")
            return existing

        result = self._make_request("POST", "datasources", payload)
        if isinstance(result, dict):
            logger.info(f"Created data source: {name}")
            return result
        return None

    def update_datasource(
        self,
        name: str,
        db_path: str,
    ) -> Optional[Dict[str, Any]]:
        """Update existing data source.

        Args:
            name: Data source name.
            db_path: New database path.

        Returns:
            Updated data source or None.
        """
        existing = self.get_datasource(name)
        if not existing:
            return None

        payload = {
            "id": existing["id"],
            "name": name,
            "type": existing["type"],
            "access": "proxy",
            "isDefault": True,
            "jsonData": {
                "path": db_path,
                "sqlMode": True,
            },
        }

        result = self._make_request(
            "PUT", f"datasources/{existing['id']}", payload
        )
        if isinstance(result, dict):
            logger.info(f"Updated data source: {name}")
            return result
        return None

    # ========================================================================
    # Dashboard Management
    # ========================================================================

    def get_dashboards(self) -> List[Dict[Any, Any]]:
        """Get list of dashboards.

        Returns:
            List of dashboard summaries.
        """
        result = self._make_request("GET", "search", params={"type": "dash-db"})
        return result if isinstance(result, list) else []

    def get_dashboard(self, uid: str) -> Optional[Dict[str, Any]]:
        """Get dashboard by UID.

        Args:
            uid: Dashboard UID.

        Returns:
            Dashboard configuration or None.
        """
        result = self._make_request("GET", f"dashboards/uid/{uid}")
        return result.get("dashboard") if isinstance(result, dict) else None

    def create_dashboard(
        self,
        title: str,
        panels: List[Dict],
        uid: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Create new dashboard.

        Args:
            title: Dashboard title.
            panels: List of panel configurations.
            uid: Optional dashboard UID.

        Returns:
            Created dashboard metadata or None.
        """
        dashboard = {
            "title": title,
            "timezone": "browser",
            "panels": panels,
            "refresh": "1m",
            "time": {
                "from": "now-7d",
                "to": "now",
            },
            "uid": uid or title.lower().replace(" ", "-"),
            "version": 1,
        }

        payload = {
            "dashboard": dashboard,
            "overwrite": True,
        }

        result = self._make_request("POST", "dashboards/db", payload)
        if isinstance(result, dict):
            logger.info(f"Created dashboard: {title}")
            return result
        return None

    def delete_dashboard(self, uid: str) -> bool:
        """Delete dashboard by UID.

        Args:
            uid: Dashboard UID.

        Returns:
            True if deleted successfully.
        """
        result = self._make_request("DELETE", f"dashboards/uid/{uid}")
        if result:
            logger.info(f"Deleted dashboard: {uid}")
            return True
        return False

    # ========================================================================
    # Panel Creation Helpers
    # ========================================================================

    def create_graph_panel(
        self,
        title: str,
        datasource: str,
        target_query: str,
        position: int = 0,
        height: int = 8,
        width: int = 12,
    ) -> Dict:
        """Create a graph/time-series panel.

        Args:
            title: Panel title.
            datasource: Data source name.
            target_query: SQL query for data.
            position: Panel grid position.
            height: Panel height (grid units).
            width: Panel width (grid units).

        Returns:
            Panel configuration.
        """
        return {
            "type": "graph",
            "title": title,
            "gridPos": {
                "h": height,
                "w": width,
                "x": (position % 2) * 12,
                "y": (position // 2) * 8,
            },
            "datasource": datasource,
            "targets": [
                {
                    "refId": "A",
                    "sql": target_query,
                }
            ],
            "options": {
                "legend": {
                    "displayMode": "list",
                    "placement": "bottom",
                },
                "tooltipDisplayMode": "multi",
            },
        }

    def create_table_panel(
        self,
        title: str,
        datasource: str,
        target_query: str,
        position: int = 0,
        height: int = 8,
        width: int = 12,
    ) -> Dict:
        """Create a table panel.

        Args:
            title: Panel title.
            datasource: Data source name.
            target_query: SQL query for data.
            position: Panel grid position.
            height: Panel height.
            width: Panel width.

        Returns:
            Panel configuration.
        """
        return {
            "type": "table",
            "title": title,
            "gridPos": {
                "h": height,
                "w": width,
                "x": (position % 2) * 12,
                "y": (position // 2) * 8,
            },
            "datasource": datasource,
            "targets": [
                {
                    "refId": "A",
                    "sql": target_query,
                }
            ],
            "options": {
                "showHeader": True,
                "sortBy": [],
            },
        }

    def create_stat_panel(
        self,
        title: str,
        datasource: str,
        target_query: str,
        unit: str = "short",
        position: int = 0,
        height: int = 4,
        width: int = 6,
    ) -> Dict:
        """Create a stat/number panel.

        Args:
            title: Panel title.
            datasource: Data source name.
            target_query: SQL query for data.
            unit: Unit for display (short, percent, short, etc).
            position: Panel grid position.
            height: Panel height.
            width: Panel width.

        Returns:
            Panel configuration.
        """
        return {
            "type": "stat",
            "title": title,
            "gridPos": {
                "h": height,
                "w": width,
                "x": (position % 4) * 6,
                "y": (position // 4) * 4,
            },
            "datasource": datasource,
            "targets": [
                {
                    "refId": "A",
                    "sql": target_query,
                }
            ],
            "options": {
                "colorMode": "background",
                "graphMode": "none",
                "justifyMode": "center",
                "orientation": "auto",
                "textMode": "auto",
                "unit": unit,
            },
        }

    # ========================================================================
    # Dashboard Templates
    # ========================================================================

    def create_usage_dashboard(self, datasource: str) -> bool:
        """Create Usage Trends dashboard.

        Args:
            datasource: Data source name.

        Returns:
            True if created successfully.
        """
        panels = [
            self.create_stat_panel(
                "Total Skills",
                datasource,
                "SELECT COUNT(DISTINCT skill_id) FROM skill_usage",
                position=0,
            ),
            self.create_stat_panel(
                "Total Executions",
                datasource,
                "SELECT SUM(execution_count) FROM skill_usage",
                unit="short",
                position=1,
            ),
            self.create_stat_panel(
                "Avg Success Rate",
                datasource,
                "SELECT AVG(CAST(success_count AS FLOAT) / CAST(execution_count AS FLOAT) * 100) FROM skill_usage WHERE execution_count > 0",
                unit="percent",
                position=2,
            ),
            self.create_graph_panel(
                "Daily Usage Trend",
                datasource,
                "SELECT DATE(timestamp) as time, SUM(execution_count) as value FROM skill_usage GROUP BY DATE(timestamp) ORDER BY time",
                position=3,
            ),
        ]

        return bool(
            self.create_dashboard(
                "Usage Trends", panels, uid="toolweaver-usage"
            )
        )

    def create_leaderboard_dashboard(self, datasource: str) -> bool:
        """Create Leaderboards dashboard.

        Args:
            datasource: Data source name.

        Returns:
            True if created successfully.
        """
        panels = [
            self.create_table_panel(
                "Top Skills by Usage",
                datasource,
                """
                SELECT 
                    ROW_NUMBER() OVER (ORDER BY SUM(execution_count) DESC) as Rank,
                    skill_id as 'Skill ID',
                    SUM(execution_count) as 'Executions',
                    COUNT(DISTINCT user_id) as 'Users'
                FROM skill_usage
                GROUP BY skill_id
                ORDER BY SUM(execution_count) DESC
                LIMIT 20
                """,
                position=0,
            ),
            self.create_table_panel(
                "Top Skills by Rating",
                datasource,
                """
                SELECT 
                    ROW_NUMBER() OVER (ORDER BY rating_avg DESC) as Rank,
                    skill_id as 'Skill ID',
                    rating_avg as 'Avg Rating',
                    rating_count as 'Ratings'
                FROM skill_metrics
                WHERE rating_count > 0
                ORDER BY rating_avg DESC, rating_count DESC
                LIMIT 20
                """,
                position=1,
            ),
        ]

        return bool(
            self.create_dashboard(
                "Leaderboards", panels, uid="toolweaver-leaderboards"
            )
        )

    def create_metrics_dashboard(self, datasource: str) -> bool:
        """Create Performance Metrics dashboard.

        Args:
            datasource: Data source name.

        Returns:
            True if created successfully.
        """
        panels = [
            self.create_stat_panel(
                "Avg Latency (ms)",
                datasource,
                "SELECT AVG(avg_latency_ms) FROM skill_usage",
                unit="ms",
                position=0,
            ),
            self.create_stat_panel(
                "Success Rate",
                datasource,
                "SELECT SUM(success_count) * 100.0 / SUM(execution_count) FROM skill_usage WHERE execution_count > 0",
                unit="percent",
                position=1,
            ),
            self.create_graph_panel(
                "Latency Over Time",
                datasource,
                "SELECT DATE(timestamp) as time, AVG(avg_latency_ms) as latency FROM skill_usage GROUP BY DATE(timestamp)",
                position=2,
                height=8,
                width=24,
            ),
        ]

        return bool(
            self.create_dashboard(
                "Performance Metrics", panels, uid="toolweaver-metrics"
            )
        )

    def create_adoption_dashboard(self, datasource: str) -> bool:
        """Create Adoption Tracking dashboard.

        Args:
            datasource: Data source name.

        Returns:
            True if created successfully.
        """
        panels = [
            self.create_stat_panel(
                "Active Users",
                datasource,
                "SELECT COUNT(DISTINCT user_id) FROM skill_usage",
                position=0,
            ),
            self.create_graph_panel(
                "New Users Over Time",
                datasource,
                """
                SELECT 
                    DATE(MIN(timestamp)) as time,
                    COUNT(*) as count
                FROM (
                    SELECT DISTINCT user_id, MIN(timestamp) FROM skill_usage GROUP BY user_id
                )
                GROUP BY DATE(time)
                """,
                position=1,
            ),
        ]

        return bool(
            self.create_dashboard(
                "Adoption Tracking", panels, uid="toolweaver-adoption"
            )
        )

    def create_health_dashboard(self, datasource: str) -> bool:
        """Create Health Dashboard.

        Args:
            datasource: Data source name.

        Returns:
            True if created successfully.
        """
        panels = [
            self.create_stat_panel(
                "Avg Health Score",
                datasource,
                "SELECT AVG(health_score) FROM skill_metrics",
                unit="percent",
                position=0,
            ),
            self.create_table_panel(
                "Skills Health Status",
                datasource,
                """
                SELECT 
                    skill_id,
                    health_score,
                    rating_avg,
                    install_count,
                    deprecation_status
                FROM skill_metrics
                ORDER BY health_score DESC
                LIMIT 30
                """,
                position=1,
            ),
        ]

        return bool(
            self.create_dashboard(
                "Health Dashboard", panels, uid="toolweaver-health"
            )
        )

    def create_all_dashboards(self, datasource: str) -> Dict[str, bool]:
        """Create all standard dashboards.

        Args:
            datasource: Data source name.

        Returns:
            Dictionary with results for each dashboard.
        """
        results = {
            "usage": self.create_usage_dashboard(datasource),
            "leaderboards": self.create_leaderboard_dashboard(datasource),
            "metrics": self.create_metrics_dashboard(datasource),
            "adoption": self.create_adoption_dashboard(datasource),
            "health": self.create_health_dashboard(datasource),
        }

        created = sum(1 for v in results.values() if v)
        logger.info(f"Created {created}/5 dashboards")
        return results


def setup_grafana(
    url: str,
    api_key: str,
    db_path: str,
    datasource_name: str = "ToolWeaver Analytics",
    auto_create_dashboards: bool = True,
) -> bool:
    """Setup Grafana integration.

    Args:
        url: Grafana URL.
        api_key: Grafana API key.
        db_path: SQLite database path.
        datasource_name: Name for data source.
        auto_create_dashboards: Whether to auto-create dashboards.

    Returns:
        True if setup was successful.
    """
    config = GrafanaConfig(
        url=url,
        api_key=api_key,
        datasource_name=datasource_name,
        auto_create_dashboards=auto_create_dashboards,
    )

    client = GrafanaClient(config)

    # Check connectivity
    if not client.health_check():
        logger.error("Failed to connect to Grafana")
        return False

    # Create/update data source
    if not client.create_datasource(datasource_name, db_path):
        logger.error("Failed to create data source")
        return False

    # Create dashboards if enabled
    if auto_create_dashboards:
        client.create_all_dashboards(datasource_name)

    logger.info("Grafana setup complete")
    return True
