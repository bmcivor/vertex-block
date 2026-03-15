import pytest

from pydantic import ValidationError

from vertex_block.config import get_settings


class TestSettings:

    @pytest.fixture(autouse=True)
    def reset_settings(self):
        get_settings.cache_clear()

    def test_get_settings(self):
        settings = get_settings()

        expected_settings = {
            "dns_port": 53,
            "dns_upstream": ["1.1.1.1", "8.8.8.8"],
            "dns_timeout": 5,
            "dns_block_response": "nxdomain",
            "api_port": 8080,
            "api_host": "0.0.0.0",
            "blocklist_dir": "./blocklists",
            "catalog_file": "./catalog.json",
            "update_schedule": "0 4 * * *",
            "log_level": "info",
            "log_queries": False,
            "data_dir": "./data",
            "stats_retention": 7,
        }

        assert settings.model_dump() == expected_settings

    def test_env_var_overrides(self, monkeypatch):
        monkeypatch.setenv("VB_DNS_PORT", "9053")
        monkeypatch.setenv("VB_LOG_LEVEL", "debug")

        settings = get_settings()

        expected_settings = {
            "dns_port": 9053,
            "dns_upstream": ["1.1.1.1", "8.8.8.8"],
            "dns_timeout": 5,
            "dns_block_response": "nxdomain",
            "api_port": 8080,
            "api_host": "0.0.0.0",
            "blocklist_dir": "./blocklists",
            "catalog_file": "./catalog.json",
            "update_schedule": "0 4 * * *",
            "log_level": "debug",
            "log_queries": False,
            "data_dir": "./data",
            "stats_retention": 7,
        }

        assert settings.model_dump() == expected_settings

    @pytest.mark.parametrize("env_var,value", [
        ("VB_DNS_PORT", "not-a-port"),
        ("VB_DNS_TIMEOUT", "slow"),
        ("VB_API_PORT", ""),
        ("VB_LOG_QUERIES", "maybe"),
        ("VB_STATS_RETENTION", "not-a-number"),
    ])
    def test_invalid_env_var(self, monkeypatch, env_var, value):
        monkeypatch.setenv(env_var, value)

        with pytest.raises(ValidationError):
            get_settings()
