# dns module
#
# Provider-neutral contract only. This module intentionally does not create DNS
# resources until a concrete provider is selected by the infra owner.
#
# When a provider is chosen, implement the real zone and record resources here
# instead of keeping an implicit placeholder path.
