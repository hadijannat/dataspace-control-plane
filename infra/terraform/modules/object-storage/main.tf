# object-storage module
#
# Provider-neutral contract only. This module intentionally does not create an
# object store until a concrete provider is selected by the infra owner.
#
# When a provider is chosen, implement the real resource here and keep the
# external contract explicit rather than masking placeholders as production
# infrastructure.
