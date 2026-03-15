from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from VB_* environment variables with defaults.

    See docs/design/configuration.md for the full list of options and defaults.
    """
    model_config = SettingsConfigDict(env_prefix="VB_")

    dns_port: int = Field(
        default=53,
        description="Port for DNS server",
    )
    dns_upstream: list[str] = Field(
        default=["1.1.1.1", "8.8.8.8"],
        description="Upstream DNS servers",
    )
    dns_timeout: int = Field(
        default=5,
        description="Timeout for upstream DNS queries",
    )
    dns_block_response: Literal["nxdomain", "zero"] = Field(
        default="nxdomain",
        description="Response for blocked domains: nxdomain or zero",
    )
    api_port: int = Field(
        default=8080,
        description="Port for API server",
    )
    api_host: str = Field(
        default="0.0.0.0",
        description="Bind address for API server",
    )
    blocklist_dir: str = Field(
        default="./blocklists",
        description="Directory for blocklist files",
    )
    catalog_file: str = Field(
        default="./catalog.json",
        description="Path to catalog JSON file",
    )
    update_schedule: str = Field(
        default="0 4 * * *",
        description="Cron expression for scheduled updates",
    )
    log_level: Literal["debug", "info", "warning", "error"] = Field(
        default="info",
        description="Log level",
    )
    log_queries: bool = Field(
        default=False,
        description="Log all DNS queries",
    )
    data_dir: str = Field(
        default="./data",
        description="Directory for persistent data",
    )
    stats_retention: int = Field(
        default=7,
        description="Days to retain query stats",
    )
