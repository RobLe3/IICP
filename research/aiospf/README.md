# AI-OSPF / ARCP pre-normative evidence

This directory mirrors implementation-neutral research fixtures from the IICP
control-plane repository. They are not part of the normative v1.9 protocol.

`fixtures/cip-consumer-cosignature-v1.json` defines executable evidence for an
optional future CIP consumer co-signature profile. It pins full RFC 8785
canonical receipt bytes and edge vectors, a domain-separated digest, provider and consumer signatures, semantic
failure cases, privacy exclusions and settlement-simulation outcomes. The
fixture does not enable the profile, change credits or reputation, or authorize
mandatory co-signatures.
