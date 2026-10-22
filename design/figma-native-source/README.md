# Native Figma continuation

The state file identifies the created Figma foundations. builder.js builds native auto-layout screens from the adjacent screens.json data once native editing is available. Resolve library components by key, not transient import IDs.

Use the existing file key from state.json and continue in small, retry-safe screen batches. Return created node IDs and inspect the resulting screens. This source has not yet completed a screen build because native-editing access was exhausted.
