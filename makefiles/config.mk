# ==============================================================================
# Configuration Validation
# ==============================================================================

PYTHON := .venv/bin/python

validate-config:
	@echo "Validating environment configurations..."
	@$(PYTHON) -c "from src.cdk.config import load_config; \
		print('✓ dev.yaml'); load_config('dev'); \
		print('✓ test.yaml'); load_config('test'); \
		print('✓ prod.yaml'); load_config('prod'); \
		print('\n✓ All configurations are valid')"

show-config:
	@echo "Configuration for $(ENV) environment:"
	@echo "======================================"
	@$(PYTHON) -c "from src.cdk.config import load_config; \
		import yaml; \
		config = load_config('$(ENV)'); \
		print(yaml.dump({ \
			'environment': config.environment, \
			'memory': { \
				'enabled': config.memory.enabled, \
				'event_expiry_days': config.memory.event_expiry_days, \
				'strategies': { \
					'summary': config.memory.strategies.summary, \
					'preference': config.memory.strategies.preference, \
					'semantic': config.memory.strategies.semantic \
				} \
			}, \
			'agent_runtime': { \
				'log_level': config.agent_runtime.log_level, \
				'otel_logging_enabled': config.agent_runtime.otel_logging_enabled \
			}, \
			'mcp_runtimes': { \
				'calculator': { \
					'log_level': config.mcp_runtimes.calculator.log_level \
				} \
			}, \
			'lambda_targets': { \
				'skill_search': { \
					'log_level': config.lambda_targets.skill_search.log_level \
				}, \
				'temperature_converter': { \
					'log_level': config.lambda_targets.temperature_converter.log_level \
				} \
			}, \
			'observability': { \
				'enabled': config.observability.enabled \
			}, \
			'evaluation': { \
				'sampling_rate': config.evaluation.sampling_rate, \
				'enable_on_create': config.evaluation.enable_on_create \
			} \
		}, default_flow_style=False))"
