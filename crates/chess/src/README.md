# Chess domain source

The source tree is organized by responsibility:

- `model/` contains foundational, notation-independent chess values;
- future position, move-generation, and game-state modules remain separate.

Application integration, hardware, and transport concerns do not belong here.
