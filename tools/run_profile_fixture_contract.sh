#!/usr/bin/env bash
set -euo pipefail

python3 tools/manage_release_closure.py --check
python3 -m unittest discover -s conformance-runner/tests
python3 -m unittest discover -s tools -p 'test_effective_capability_taxonomy.py'
python3 -m unittest discover -s tools -p 'test_runtime_identity_context.py'
python3 -m unittest discover -s tools -p 'test_environmental_independence.py'
python3 -m unittest discover -s tools -p 'test_environmental_independence_decision.py'
python3 -m unittest discover -s tools -p 'test_identifier_registry_architecture.py'
python3 -m unittest discover -s tools -p 'test_task_time_semantics.py'
python3 -m unittest discover -s tools -p 'test_directory_state_semantics.py'
python3 -m unittest discover -s tools -p 'test_effective_service_capability_semantics.py'
python3 -m unittest discover -s tools -p 'test_effective_capability_wire_contract.py'
python3 -m unittest discover -s tools -p 'test_compatibility_environment.py'
python3 -m unittest discover -s tools -p 'test_restricted_trust_domain_fixture.py'
python3 -m unittest discover -s tools -p 'test_restricted_directory_decision_fixture.py'
python3 -m unittest discover -s tools -p 'test_restricted_trust_domain_membership.py'
python3 -m unittest discover -s tools -p 'test_restricted_trust_domain_bootstrap.py'
python3 -m unittest discover -s tools -p 'test_local_directory_discovery.py'
python3 tools/check_intent_registry.py
python3 tools/check_intent_registry_schema.py
python3 -m unittest discover -s tools -p 'test_intent_registry.py'
python3 -m unittest discover -s tools -p 'test_intent_payload_fixture.py'
python3 tools/audit_intent_sources.py --check
python3 -m unittest discover -s tools -p 'test_service_lifecycle_fixture.py'
python3 tools/test_mcp_era_fixture.py
python3 tools/check_e050_client_credential_lifecycle.py
python3 -m unittest discover -s tools -p 'test_e050_client_credential_lifecycle.py'
python3 tools/test_reputation_hourly_velocity_fixture.py
python3 -m unittest discover -s tools -p 'test_terminology_discoverability.py'
python3 tools/check_runtime_health_fixture.py
python3 tools/check_public_measurement_profile.py
python3 -m unittest discover -s tools -p 'test_public_measurement_profile.py'
python3 tools/check_ecosystem_version_truth.py
python3 -m unittest discover -s tools -p 'test_ecosystem_version_truth.py'
python3 tools/check_a2a_execution_binding.py
python3 -m unittest discover -s tools -p 'test_a2a_execution_binding.py'
python3 -m unittest discover -s tools -p 'test_a2a_cross_runtime_loopback.py'
python3 tools/check_dns_aid_mapping.py
python3 -m unittest discover -s tools -p 'test_dns_aid_mapping.py'
python3 tools/check_identity_evidence_layering.py
python3 -m unittest discover -s tools -p 'test_identity_evidence_layering.py'
python3 tools/check_security_considerations_coverage.py
python3 -m unittest discover -s tools -p 'test_security_considerations_coverage.py'
python3 tools/check_operator_onboarding_recovery.py
python3 -m unittest discover -s tools -p 'test_operator_onboarding_recovery.py'
python3 tools/check_newcomer_validation_record.py
python3 -m unittest discover -s tools -p 'test_newcomer_validation_record.py'
python3 tools/check_clean_room_interoperability_record.py
python3 -m unittest discover -s tools -p 'test_clean_room_interoperability_record.py'
python3 -m unittest discover -s tools -p 'test_external_participation_campaign.py'
python3 tools/check_submission_governance_decision.py
python3 -m unittest discover -s tools -p 'test_submission_governance_decision.py'
python3 tools/check_signed_message_envelope_boundary.py
python3 -m unittest discover -s tools -p 'test_signed_message_envelope_boundary.py'
python3 tools/check_native_framing_fixtures.py
python3 tools/check_pre1_feature_baseline.py
python3 -m unittest discover -s tools -p 'test_pre1_feature_baseline.py'
python3 tools/check_public_evidence_access.py
python3 -m unittest discover -s tools -p 'test_public_evidence_access.py'
python3 -m unittest discover -s tools -p 'test_ci_required_check_contract.py'
