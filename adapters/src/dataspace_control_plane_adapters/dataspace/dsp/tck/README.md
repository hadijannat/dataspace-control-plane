# DSP TCK Integration

Run `pytest tests/compatibility/dsp-tck` to execute the Dataspace Protocol
Technology Compatibility Kit against this adapter.

The TCK verifies conformance with the DSP 2025-1 specification for:
- Catalog Protocol (§4)
- Contract Negotiation Protocol (§5)
- Transfer Process Protocol (§6)

TCK configuration is managed in `tests/compatibility/dsp-tck/conftest.py`.
