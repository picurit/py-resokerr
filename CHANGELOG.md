## v1.0.0 (2026-01-23)

### BREAKING CHANGE

- Validator class is no longer exported from the public API.
Users should use to_dict() on Ok/Err/MessageTrace or unwrap(as_dict=True)
instead of calling Validator methods directly.

### Feat

- :sparkles: Add Validator class for message serialization checks and update MessageTrace serialization methods

### Refactor

- :recycle: Rename Validator to TypeUtils and make internal

## v0.3.0 (2026-01-22)

### Feat

- :sparkles: Add success message handling in MessageTrace and Ok classes

### Fix

- :wrench: Use deploy key for release workflow to bypass branch protection
- :pencil2: Remove unnecessary type hinting for success and info message properties

## v0.2.0 (2026-01-19)

### Feat

- :sparkles: Add serialization methods to MessageTrace and implement Serializable protocol

## v0.1.2 (2026-01-15)

## v0.1.1 (2026-01-15)

### Feat

- :sparkles: Implement map functionality for Ok and Err instances with comprehensive tests
- :sparkles: Add unwrap methods for Ok and Err classes with default handling

## v0.1.0 (2026-01-14)

### Refactor

- :recycle: Rename 'trace' to 'cause' in Err class and update related tests

## v0.0.1 (2026-01-14)

### Feat

- :children_crossing: Downgrade ERROR messages to WARNING in Ok class for semantic correctness
- :art: Enhance MessageTrace and Protocols for improved message handling and immutability
- :construction: Add .gitignore and initial implementation of result handling classes
- :tada: Initial commit

### Fix

- :bug: Ensure immutability of details and metadata by creating copies before conversion to MappingProxyType

### Refactor

- :recycle: Organize code inside core functionality

### Perf

- :zap: Apply final decorator and slots to Ok and Err dataclasses for performance optimization
